"""
TikTok Shop API integration
"""
import httpx
from typing import List, Dict, Optional
from loguru import logger
from config import settings, APIEndpoints


class TikTokClient:
    """TikTok Shop API client"""

    def __init__(self):
        self.access_token = settings.tiktok_access_token
        self.pixel_id = settings.tiktok_pixel_id
        self.base_url = APIEndpoints.TIKTOK_BASE

    def _get_headers(self) -> Dict[str, str]:
        """Generate API headers"""
        return {
            "Access-Token": self.access_token,
            "Content-Type": "application/json"
        }

    async def create_product(self, product_data: Dict) -> Optional[str]:
        """Create a product listing on TikTok Shop"""
        try:
            payload = {
                "product_name": product_data.get("title"),
                "description": product_data.get("description"),
                "category_id": product_data.get("category_id"),
                "brand_id": product_data.get("brand_id"),
                "images": product_data.get("images", []),
                "video": product_data.get("video_url"),
                "skus": [{
                    "price": str(product_data.get("price")),
                    "stock": product_data.get("stock", 9999),
                    "sku_id": product_data.get("sku_id", "")
                }]
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/product/create",
                    headers=self._get_headers(),
                    json=payload,
                    timeout=30.0
                )
                response.raise_for_status()
                data = response.json()

                if data.get("code") == 0:
                    product_id = data.get("data", {}).get("product_id")
                    logger.info(f"Created TikTok product: {product_id}")
                    return product_id
                else:
                    logger.error(f"TikTok API error: {data.get('message')}")
                    return None

        except Exception as e:
            logger.error(f"Error creating TikTok product: {e}")
            return None

    async def update_product(self, product_id: str, product_data: Dict) -> bool:
        """Update an existing product"""
        try:
            payload = {
                "product_id": product_id,
                **product_data
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/product/update",
                    headers=self._get_headers(),
                    json=payload,
                    timeout=30.0
                )
                response.raise_for_status()
                data = response.json()

                success = data.get("code") == 0
                if success:
                    logger.info(f"Updated TikTok product: {product_id}")
                return success

        except Exception as e:
            logger.error(f"Error updating TikTok product: {e}")
            return False

    async def get_product(self, product_id: str) -> Optional[Dict]:
        """Get product details"""
        try:
            params = {"product_id": product_id}

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/product/details",
                    headers=self._get_headers(),
                    params=params,
                    timeout=30.0
                )
                response.raise_for_status()
                data = response.json()

                if data.get("code") == 0:
                    return data.get("data")
                return None

        except Exception as e:
            logger.error(f"Error fetching TikTok product: {e}")
            return None

    async def get_trending_products(self, category: Optional[str] = None) -> List[Dict]:
        """Get trending products from TikTok Shop"""
        try:
            params = {}
            if category:
                params["category"] = category

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/product/trending",
                    headers=self._get_headers(),
                    params=params,
                    timeout=30.0
                )
                response.raise_for_status()
                data = response.json()

                if data.get("code") == 0:
                    products = data.get("data", {}).get("products", [])
                    logger.info(f"Found {len(products)} trending TikTok products")
                    return products
                return []

        except Exception as e:
            logger.error(f"Error fetching trending products: {e}")
            return []

    async def track_event(self, event_type: str, event_data: Dict) -> bool:
        """Track pixel events"""
        try:
            payload = {
                "pixel_code": self.pixel_id,
                "event": event_type,
                "properties": event_data
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/pixel/track",
                    headers=self._get_headers(),
                    json=payload,
                    timeout=30.0
                )
                response.raise_for_status()
                return True

        except Exception as e:
            logger.error(f"Error tracking event: {e}")
            return False
