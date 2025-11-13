"""
Autopilot API endpoints - Full automation
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.orm import Session
from loguru import logger

from models.database import get_db, Product
from core import ProductScout, AIContentGenerator, MultiPlatformPublisher
from utils import SlackNotifier

router = APIRouter()


class AutopilotRequest(BaseModel):
    sources: List[str] = ["all"]
    platforms: List[str] = ["tiktok"]
    category: Optional[str] = None
    min_score: float = 70.0
    limit: int = 10


@router.post("/run")
async def run_autopilot(
    request: AutopilotRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Run full autopilot: discover -> generate -> publish

    This is the complete hands-free operation:
    1. Discover winning products from specified sources
    2. Generate AI-optimized content
    3. Publish to specified platforms
    4. Send Slack notifications
    """
    try:
        logger.info("Starting autopilot mode...")

        scout = ProductScout()
        generator = AIContentGenerator()
        publisher = MultiPlatformPublisher()
        slack = SlackNotifier()

        results = {
            "discovered": 0,
            "generated": 0,
            "published": 0,
            "failed": 0,
            "products": []
        }

        # Step 1: Discover winning products
        logger.info("Step 1: Discovering products...")
        all_products = []

        for source in request.sources:
            products = await scout.find_winning_products(
                min_score=request.min_score,
                sources=[source],
                limit=request.limit
            )
            all_products.extend(products)

        results["discovered"] = len(all_products)

        # Step 2: Generate content and publish
        logger.info(f"Step 2: Processing {len(all_products)} products...")

        for product_data in all_products[:request.limit]:
            try:
                # Check if product already exists
                existing = db.query(Product).filter(
                    Product.external_id == product_data.get("external_id"),
                    Product.source == product_data.get("source")
                ).first()

                if existing and existing.is_published:
                    logger.info(f"Product already published: {existing.title}")
                    continue

                # Save product
                if not existing:
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
                    db.commit()
                    db.refresh(product)
                else:
                    product = existing

                # Generate AI content
                logger.info(f"Generating content for: {product.title}")
                enriched = await generator.generate_complete_listing({
                    "id": product.id,
                    "title": product.title,
                    "description": product.description,
                    "category": product.category,
                    "price": product.source_price,
                    "rating": product.rating,
                    "images": product.images
                })

                # Update product
                product.ai_title = enriched.get("ai_title")
                product.ai_description = enriched.get("ai_description")
                product.ai_bullets = enriched.get("ai_bullets")
                product.seo_keywords = enriched.get("seo_keywords")
                product.status = "generated"

                from datetime import datetime
                product.generated_at = datetime.utcnow()
                db.commit()

                results["generated"] += 1

                # Publish to platforms
                logger.info(f"Publishing to: {request.platforms}")
                publish_results = await publisher.publish_product(
                    {
                        "id": product.id,
                        "title": product.ai_title,
                        "ai_title": product.ai_title,
                        "description": product.ai_description,
                        "ai_description": product.ai_description,
                        "price": product.suggested_price,
                        "suggested_price": product.suggested_price,
                        "images": product.images,
                        "category": product.category,
                        "seo_keywords": product.seo_keywords
                    },
                    request.platforms,
                    db
                )

                # Update status if published successfully
                if any(publish_results.values()):
                    product.is_published = True
                    product.status = "published"
                    product.published_at = datetime.utcnow()
                    db.commit()

                    results["published"] += 1

                    # Send notification
                    background_tasks.add_task(
                        slack.notify_listing_published,
                        {
                            "title": product.ai_title,
                            "suggested_price": product.suggested_price,
                            "profit_margin": product.profit_margin
                        },
                        publish_results
                    )

                results["products"].append({
                    "id": product.id,
                    "title": product.ai_title or product.title,
                    "score": product.overall_score,
                    "published": product.is_published,
                    "platforms": publish_results
                })

            except Exception as e:
                logger.error(f"Error processing product: {e}")
                results["failed"] += 1

        # Send summary notification
        background_tasks.add_task(
            slack.notify_daily_summary,
            {
                "discovered": results["discovered"],
                "published": results["published"],
                "revenue": 0,  # Would need actual sales data
                "orders": 0,
                "avg_order_value": 0
            }
        )

        logger.info("Autopilot complete!")
        return {
            "success": True,
            "results": results
        }

    except Exception as e:
        logger.error(f"Autopilot error: {e}")
        return {
            "success": False,
            "error": str(e),
            "results": results
        }
