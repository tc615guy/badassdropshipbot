"""
Analytics and performance tracking
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from loguru import logger

from models.database import Product, Listing, Analytics


class AnalyticsEngine:
    """Track and analyze product performance"""

    def get_product_performance(
        self,
        product_id: int,
        db: Session,
        days: int = 30
    ) -> Dict:
        """Get performance metrics for a product"""
        try:
            # Get product
            product = db.query(Product).filter(Product.id == product_id).first()
            if not product:
                return {}

            # Get analytics for date range
            start_date = datetime.utcnow() - timedelta(days=days)
            analytics = db.query(Analytics).filter(
                Analytics.product_id == product_id,
                Analytics.date >= start_date
            ).all()

            # Aggregate metrics
            total_views = sum(a.views for a in analytics)
            total_clicks = sum(a.clicks for a in analytics)
            total_orders = sum(a.orders for a in analytics)
            total_revenue = sum(a.revenue for a in analytics)
            total_profit = sum(a.profit for a in analytics)

            # Calculate rates
            ctr = (total_clicks / total_views * 100) if total_views > 0 else 0
            conversion_rate = (total_orders / total_clicks * 100) if total_clicks > 0 else 0
            avg_order_value = total_revenue / total_orders if total_orders > 0 else 0

            return {
                "product_id": product_id,
                "product_title": product.title,
                "period_days": days,
                "metrics": {
                    "views": total_views,
                    "clicks": total_clicks,
                    "orders": total_orders,
                    "revenue": round(total_revenue, 2),
                    "profit": round(total_profit, 2)
                },
                "rates": {
                    "ctr": round(ctr, 2),
                    "conversion_rate": round(conversion_rate, 2),
                    "avg_order_value": round(avg_order_value, 2),
                    "roi": round((total_profit / product.source_price * 100) if product.source_price > 0 else 0, 2)
                },
                "daily_data": [
                    {
                        "date": a.date.strftime("%Y-%m-%d"),
                        "views": a.views,
                        "clicks": a.clicks,
                        "orders": a.orders,
                        "revenue": a.revenue
                    }
                    for a in analytics
                ]
            }

        except Exception as e:
            logger.error(f"Error getting product performance: {e}")
            return {}

    def get_platform_performance(
        self,
        platform: str,
        db: Session,
        days: int = 30
    ) -> Dict:
        """Get performance metrics for a platform"""
        try:
            start_date = datetime.utcnow() - timedelta(days=days)

            # Get all listings for platform
            listings = db.query(Listing).filter(
                Listing.platform == platform,
                Listing.updated_at >= start_date
            ).all()

            total_views = sum(l.views for l in listings)
            total_clicks = sum(l.clicks for l in listings)
            total_orders = sum(l.orders for l in listings)
            total_revenue = sum(l.revenue for l in listings)

            return {
                "platform": platform,
                "period_days": days,
                "active_listings": len([l for l in listings if l.status == "active"]),
                "total_listings": len(listings),
                "metrics": {
                    "views": total_views,
                    "clicks": total_clicks,
                    "orders": total_orders,
                    "revenue": round(total_revenue, 2)
                },
                "top_products": [
                    {
                        "title": l.title,
                        "orders": l.orders,
                        "revenue": l.revenue
                    }
                    for l in sorted(listings, key=lambda x: x.revenue, reverse=True)[:10]
                ]
            }

        except Exception as e:
            logger.error(f"Error getting platform performance: {e}")
            return {}

    def get_dashboard_stats(self, db: Session) -> Dict:
        """Get overall dashboard statistics"""
        try:
            # Product counts by status
            total_products = db.query(Product).count()
            discovered = db.query(Product).filter(Product.status == "discovered").count()
            published = db.query(Product).filter(Product.is_published == True).count()

            # Total listings by platform
            listings_by_platform = db.query(
                Listing.platform,
                func.count(Listing.id)
            ).group_by(Listing.platform).all()

            # Revenue stats (last 30 days)
            start_date = datetime.utcnow() - timedelta(days=30)
            recent_listings = db.query(Listing).filter(
                Listing.updated_at >= start_date
            ).all()

            total_revenue = sum(l.revenue for l in recent_listings)
            total_orders = sum(l.orders for l in recent_listings)

            return {
                "products": {
                    "total": total_products,
                    "discovered": discovered,
                    "published": published
                },
                "listings": {
                    "total": sum(count for _, count in listings_by_platform),
                    "by_platform": {platform: count for platform, count in listings_by_platform}
                },
                "revenue_30d": {
                    "total": round(total_revenue, 2),
                    "orders": total_orders,
                    "avg_order_value": round(total_revenue / total_orders, 2) if total_orders > 0 else 0
                }
            }

        except Exception as e:
            logger.error(f"Error getting dashboard stats: {e}")
            return {}

    def get_trending_products(self, db: Session, limit: int = 10) -> List[Dict]:
        """Get currently trending products based on recent performance"""
        try:
            # Get products with recent analytics
            start_date = datetime.utcnow() - timedelta(days=7)

            # Query products with highest recent orders
            products = db.query(Product).join(Analytics).filter(
                Analytics.date >= start_date
            ).group_by(Product.id).order_by(
                func.sum(Analytics.orders).desc()
            ).limit(limit).all()

            trending = []
            for product in products:
                recent_analytics = db.query(Analytics).filter(
                    Analytics.product_id == product.id,
                    Analytics.date >= start_date
                ).all()

                total_orders = sum(a.orders for a in recent_analytics)
                total_revenue = sum(a.revenue for a in recent_analytics)

                trending.append({
                    "id": product.id,
                    "title": product.title,
                    "category": product.category,
                    "orders_7d": total_orders,
                    "revenue_7d": round(total_revenue, 2),
                    "trending_score": product.trending_score
                })

            return trending

        except Exception as e:
            logger.error(f"Error getting trending products: {e}")
            return []

    def record_event(
        self,
        product_id: int,
        event_type: str,
        db: Session,
        value: float = 0.0
    ) -> bool:
        """Record an analytics event"""
        try:
            today = datetime.utcnow().date()

            # Get or create today's analytics record
            analytics = db.query(Analytics).filter(
                Analytics.product_id == product_id,
                func.date(Analytics.date) == today
            ).first()

            if not analytics:
                analytics = Analytics(
                    product_id=product_id,
                    date=datetime.utcnow()
                )
                db.add(analytics)

            # Update based on event type
            if event_type == "view":
                analytics.views += 1
            elif event_type == "click":
                analytics.clicks += 1
            elif event_type == "order":
                analytics.orders += 1
                analytics.revenue += value
                # Calculate profit (would need product cost)
                product = db.query(Product).filter(Product.id == product_id).first()
                if product:
                    cost = product.source_price + (product.shipping_cost or 0)
                    analytics.profit += (value - cost)

            db.commit()
            return True

        except Exception as e:
            logger.error(f"Error recording event: {e}")
            db.rollback()
            return False
