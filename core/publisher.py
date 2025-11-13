"""
Multi-platform product publisher
"""
import asyncio
from typing import Dict, List, Optional
from loguru import logger
from sqlalchemy.orm import Session

from integrations import TikTokClient
from models.database import Listing


class MultiPlatformPublisher:
    """Publish products to multiple platforms"""

    def __init__(self):
        self.tiktok = TikTokClient()

    async def publish_product(
        self,
        product: Dict,
        platforms: List[str],
        db: Optional[Session] = None
    ) -> Dict[str, bool]:
        """Publish product to specified platforms"""
        logger.info(f"Publishing to platforms: {platforms}")

        results = {}

        # Publish to each platform
        tasks = []
        for platform in platforms:
            if platform.lower() == "tiktok":
                tasks.append(self._publish_to_tiktok(product, db))
            elif platform.lower() == "shopify":
                tasks.append(self._publish_to_shopify(product, db))
            elif platform.lower() == "custom":
                tasks.append(self._publish_to_custom_api(product, db))

        # Execute all publishes in parallel
        platform_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Map results
        for platform, result in zip(platforms, platform_results):
            if isinstance(result, Exception):
                logger.error(f"Error publishing to {platform}: {result}")
                results[platform] = False
            else:
                results[platform] = result

        return results

    async def _publish_to_tiktok(self, product: Dict, db: Optional[Session]) -> bool:
        """Publish to TikTok Shop"""
        try:
            tiktok_data = {
                "title": product.get("ai_title") or product.get("title"),
                "description": product.get("ai_description") or product.get("description"),
                "price": product.get("suggested_price") or product.get("price"),
                "images": product.get("images", [])[:10],  # TikTok limit
                "video_url": product.get("video_url"),
                "category_id": self._map_category_to_tiktok(product.get("category")),
                "stock": 9999  # Dropshipping - high stock
            }

            product_id = await self.tiktok.create_product(tiktok_data)

            if product_id and db:
                # Save listing to database
                listing = Listing(
                    product_id=product.get("id"),
                    platform="tiktok",
                    platform_listing_id=product_id,
                    title=tiktok_data["title"],
                    description=tiktok_data["description"],
                    price=tiktok_data["price"],
                    status="active"
                )
                db.add(listing)
                db.commit()

            success = product_id is not None
            logger.info(f"TikTok publish: {'success' if success else 'failed'}")
            return success

        except Exception as e:
            logger.error(f"TikTok publish error: {e}")
            return False

    async def _publish_to_shopify(self, product: Dict, db: Optional[Session]) -> bool:
        """Publish to Shopify (requires Shopify API credentials)"""
        try:
            logger.info("Shopify publishing requires Shopify API credentials")
            # Placeholder - would need Shopify API integration
            return False

        except Exception as e:
            logger.error(f"Shopify publish error: {e}")
            return False

    async def _publish_to_custom_api(self, product: Dict, db: Optional[Session]) -> bool:
        """Publish to custom API endpoint"""
        try:
            import httpx

            # Use the FastAPI URL from config
            from config import settings

            payload = {
                "title": product.get("ai_title") or product.get("title"),
                "description": product.get("ai_description") or product.get("description"),
                "price": product.get("suggested_price") or product.get("price"),
                "images": product.get("images", []),
                "category": product.get("category"),
                "seo_keywords": product.get("seo_keywords", {})
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{settings.fastapi_url}/api/products",
                    json=payload,
                    timeout=30.0
                )
                response.raise_for_status()

                success = response.status_code == 200
                logger.info(f"Custom API publish: {'success' if success else 'failed'}")
                return success

        except Exception as e:
            logger.error(f"Custom API publish error: {e}")
            return False

    def _map_category_to_tiktok(self, category: Optional[str]) -> str:
        """Map generic category to TikTok category ID"""
        # Placeholder - would need actual TikTok category mapping
        category_map = {
            "electronics": "100001",
            "fashion": "100002",
            "home_garden": "100003",
            "beauty": "100004",
            "sports": "100005"
        }

        return category_map.get(category, "100001")

    async def update_product(
        self,
        platform: str,
        platform_product_id: str,
        updates: Dict
    ) -> bool:
        """Update an existing product listing"""
        try:
            if platform.lower() == "tiktok":
                success = await self.tiktok.update_product(platform_product_id, updates)
                logger.info(f"TikTok update: {'success' if success else 'failed'}")
                return success

            return False

        except Exception as e:
            logger.error(f"Update error: {e}")
            return False

    async def bulk_publish(
        self,
        products: List[Dict],
        platforms: List[str],
        max_concurrent: int = 5
    ) -> Dict:
        """Publish multiple products in parallel"""
        logger.info(f"Bulk publishing {len(products)} products to {len(platforms)} platforms")

        results = {
            "total": len(products),
            "successful": 0,
            "failed": 0,
            "details": []
        }

        # Process in batches to avoid overwhelming APIs
        for i in range(0, len(products), max_concurrent):
            batch = products[i:i + max_concurrent]

            tasks = [
                self.publish_product(product, platforms)
                for product in batch
            ]

            batch_results = await asyncio.gather(*tasks, return_exceptions=True)

            for product, result in zip(batch, batch_results):
                if isinstance(result, Exception):
                    results["failed"] += 1
                    results["details"].append({
                        "product": product.get("title"),
                        "status": "error",
                        "error": str(result)
                    })
                else:
                    # Check if any platform succeeded
                    if any(result.values()):
                        results["successful"] += 1
                    else:
                        results["failed"] += 1

                    results["details"].append({
                        "product": product.get("title"),
                        "status": "published" if any(result.values()) else "failed",
                        "platforms": result
                    })

            # Rate limiting between batches
            await asyncio.sleep(2)

        logger.info(f"Bulk publish complete: {results['successful']}/{results['total']} successful")
        return results
