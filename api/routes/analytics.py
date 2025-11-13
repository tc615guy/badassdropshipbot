"""
Analytics API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from loguru import logger

from models.database import get_db
from core import AnalyticsEngine

router = APIRouter()


@router.get("/dashboard")
async def get_dashboard(db: Session = Depends(get_db)):
    """Get dashboard statistics"""
    try:
        analytics = AnalyticsEngine()
        stats = analytics.get_dashboard_stats(db)

        return {
            "success": True,
            "data": stats
        }

    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/products/{product_id}")
async def get_product_analytics(
    product_id: int,
    days: int = 30,
    db: Session = Depends(get_db)
):
    """Get analytics for a specific product"""
    try:
        analytics = AnalyticsEngine()
        performance = analytics.get_product_performance(product_id, db, days)

        if not performance:
            raise HTTPException(status_code=404, detail="Product not found")

        return {
            "success": True,
            "data": performance
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Product analytics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/platforms/{platform}")
async def get_platform_analytics(
    platform: str,
    days: int = 30,
    db: Session = Depends(get_db)
):
    """Get analytics for a specific platform"""
    try:
        analytics = AnalyticsEngine()
        performance = analytics.get_platform_performance(platform, db, days)

        return {
            "success": True,
            "data": performance
        }

    except Exception as e:
        logger.error(f"Platform analytics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trending")
async def get_trending(limit: int = 10, db: Session = Depends(get_db)):
    """Get trending products"""
    try:
        analytics = AnalyticsEngine()
        trending = analytics.get_trending_products(db, limit)

        return {
            "success": True,
            "count": len(trending),
            "products": trending
        }

    except Exception as e:
        logger.error(f"Trending products error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
