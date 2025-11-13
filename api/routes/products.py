"""
Products API endpoints
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.orm import Session
from loguru import logger

from models.database import get_db, Product
from core import ProductScout, AIContentGenerator, MultiPlatformPublisher
from utils import SlackNotifier

router = APIRouter()


class ProductScoutRequest(BaseModel):
    source: str = "all"
    category: Optional[str] = None
    limit: int = 50
    min_score: Optional[float] = None


class GenerateContentRequest(BaseModel):
    product_id: int
    variations: int = 1


class PublishRequest(BaseModel):
    product_id: int
    platforms: List[str]


@router.post("/scout")
async def scout_products(
    request: ProductScoutRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Discover products from various sources"""
    try:
        logger.info(f"Scouting products: {request.source}")

        scout = ProductScout()
        products = await scout.discover_products(
            source=request.source,
            category=request.category,
            limit=request.limit
        )

        # Filter by minimum score if specified
        if request.min_score:
            products = [p for p in products if p.get("overall_score", 0) >= request.min_score]

        # Save to database
        saved_products = []
        for product_data in products:
            # Check if product already exists
            existing = db.query(Product).filter(
                Product.external_id == product_data.get("external_id"),
                Product.source == product_data.get("source")
            ).first()

            if existing:
                continue

            product = Product(
                external_id=product_data.get("external_id"),
                source=product_data.get("source"),
                title=product_data.get("title"),
                original_title=product_data.get("title"),
                description=product_data.get("description", ""),
                original_description=product_data.get("description", ""),
                category=product_data.get("category"),
                source_price=product_data.get("price", 0),
                suggested_price=product_data.get("suggested_price", 0),
                profit_margin=product_data.get("profit_margin", 0),
                images=product_data.get("images", []),
                rating=product_data.get("rating", 0),
                review_count=product_data.get("reviews", 0),
                orders=product_data.get("orders", 0),
                trending_score=product_data.get("trending_score", 0),
                overall_score=product_data.get("overall_score", 0),
                status="discovered"
            )

            db.add(product)
            saved_products.append(product)

        db.commit()

        # Send Slack notifications for high-scoring products
        slack = SlackNotifier()
        for product in saved_products:
            if product.overall_score >= 80:
                background_tasks.add_task(
                    slack.notify_product_found,
                    {
                        "title": product.title,
                        "source": product.source,
                        "overall_score": product.overall_score,
                        "profit_margin": product.profit_margin,
                        "rating": product.rating,
                        "orders": product.orders,
                        "suggested_price": product.suggested_price
                    }
                )

        return {
            "success": True,
            "discovered": len(products),
            "saved": len(saved_products),
            "products": [
                {
                    "id": p.id,
                    "title": p.title,
                    "source": p.source,
                    "score": p.overall_score,
                    "profit_margin": p.profit_margin
                }
                for p in saved_products
            ]
        }

    except Exception as e:
        logger.error(f"Product scouting error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate/{product_id}")
async def generate_content(
    product_id: int,
    variations: int = 1,
    db: Session = Depends(get_db)
):
    """Generate AI-optimized content for a product"""
    try:
        # Get product
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        logger.info(f"Generating content for product {product_id}")

        generator = AIContentGenerator()

        product_data = {
            "id": product.id,
            "title": product.title,
            "description": product.description,
            "category": product.category,
            "price": product.source_price,
            "rating": product.rating,
            "images": product.images
        }

        if variations > 1:
            # Generate multiple variations
            generated_variations = await generator.generate_variations(product_data, variations)
            result = {
                "success": True,
                "variations": generated_variations
            }
        else:
            # Generate single listing
            generated = await generator.generate_complete_listing(product_data)

            # Update product in database
            product.ai_title = generated.get("ai_title")
            product.ai_description = generated.get("ai_description")
            product.ai_bullets = generated.get("ai_bullets")
            product.seo_keywords = generated.get("seo_keywords")
            product.status = "generated"

            from datetime import datetime
            product.generated_at = datetime.utcnow()

            db.commit()

            result = {
                "success": True,
                "product_id": product.id,
                "ai_title": product.ai_title,
                "ai_description": product.ai_description,
                "ai_bullets": product.ai_bullets,
                "seo_keywords": product.seo_keywords
            }

        return result

    except Exception as e:
        logger.error(f"Content generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/publish")
async def publish_product(
    request: PublishRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Publish product to specified platforms"""
    try:
        # Get product
        product = db.query(Product).filter(Product.id == request.product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        logger.info(f"Publishing product {request.product_id} to {request.platforms}")

        publisher = MultiPlatformPublisher()

        product_data = {
            "id": product.id,
            "title": product.ai_title or product.title,
            "ai_title": product.ai_title,
            "description": product.ai_description or product.description,
            "ai_description": product.ai_description,
            "price": product.suggested_price or product.source_price,
            "suggested_price": product.suggested_price,
            "images": product.images,
            "category": product.category,
            "seo_keywords": product.seo_keywords
        }

        results = await publisher.publish_product(
            product_data,
            request.platforms,
            db
        )

        # Update product status
        if any(results.values()):
            product.is_published = True
            product.status = "published"
            from datetime import datetime
            product.published_at = datetime.utcnow()
            db.commit()

            # Send Slack notification
            slack = SlackNotifier()
            background_tasks.add_task(
                slack.notify_listing_published,
                product_data,
                results
            )

        return {
            "success": True,
            "product_id": request.product_id,
            "results": results
        }

    except Exception as e:
        logger.error(f"Publishing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
async def list_products(
    status: Optional[str] = None,
    source: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """List products with filtering"""
    try:
        query = db.query(Product)

        if status:
            query = query.filter(Product.status == status)

        if source:
            query = query.filter(Product.source == source)

        # Order by score
        query = query.order_by(Product.overall_score.desc())

        total = query.count()
        products = query.offset(offset).limit(limit).all()

        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "products": [
                {
                    "id": p.id,
                    "title": p.title,
                    "ai_title": p.ai_title,
                    "source": p.source,
                    "category": p.category,
                    "score": p.overall_score,
                    "profit_margin": p.profit_margin,
                    "suggested_price": p.suggested_price,
                    "status": p.status,
                    "is_published": p.is_published
                }
                for p in products
            ]
        }

    except Exception as e:
        logger.error(f"List products error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{product_id}")
async def get_product(product_id: int, db: Session = Depends(get_db)):
    """Get product details"""
    try:
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        return {
            "id": product.id,
            "external_id": product.external_id,
            "source": product.source,
            "title": product.title,
            "ai_title": product.ai_title,
            "description": product.description,
            "ai_description": product.ai_description,
            "ai_bullets": product.ai_bullets,
            "category": product.category,
            "source_price": product.source_price,
            "suggested_price": product.suggested_price,
            "profit_margin": product.profit_margin,
            "images": product.images,
            "rating": product.rating,
            "review_count": product.review_count,
            "orders": product.orders,
            "overall_score": product.overall_score,
            "trending_score": product.trending_score,
            "seo_keywords": product.seo_keywords,
            "status": product.status,
            "is_published": product.is_published
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get product error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
