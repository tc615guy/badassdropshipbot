"""
CJ Dropshipping API integration
"""
import httpx
import hashlib
from typing import List, Dict, Optional
from loguru import logger
from config import settings, APIEndpoints


class CJDropshippingClient:
    """CJ Dropshipping API client"""

    def __init__(self):
        self.api_key = settings.cj_api_key
        self.base_url = APIEndpoints.CJ_BASE

    def _get_headers(self) -> Dict[str, str]:
        """Generate API headers"""
        return {
            "CJ-Access-Token": self.api_key,
            "Content-Type": "application/json"
        }

    async def search_products(
        self,
        keyword: str,
        category_id: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> List[Dict]:
        """Search products on CJ Dropshipping"""
        try:
            params = {
                "keyword": keyword,
                "pageNum": page,
                "pageSize": page_size
            }

            if category_id:
                params["categoryId"] = category_id

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/product/list",
                    headers=self._get_headers(),
                    params=params,
                    timeout=30.0
                )
                response.raise_for_status()
                data = response.json()

                if data.get("result"):
                    products = data.get("data", {}).get("list", [])
                    logger.info(f"Found {len(products)} products on CJ")
                    return products
                else:
                    logger.warning(f"CJ API error: {data.get('message')}")
                    return []

        except Exception as e:
            logger.error(f"CJ search error: {e}")
            return []

    async def get_product_details(self, product_id: str) -> Optional[Dict]:
        """Get product details"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/product/query",
                    headers=self._get_headers(),
                    params={"pid": product_id},
                    timeout=30.0
                )
                response.raise_for_status()
                data = response.json()

                if data.get("result"):
                    return data.get("data")
                return None

        except Exception as e:
            logger.error(f"Error fetching CJ product {product_id}: {e}")
            return None

    async def get_categories(self) -> List[Dict]:
        """Get product categories"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/product/category",
                    headers=self._get_headers(),
                    timeout=30.0
                )
                response.raise_for_status()
                data = response.json()

                if data.get("result"):
                    return data.get("data", [])
                return []

        except Exception as e:
            logger.error(f"Error fetching categories: {e}")
            return []

    async def check_inventory(self, product_id: str, variant_id: Optional[str] = None) -> Dict:
        """Check product inventory"""
        try:
            params = {"pid": product_id}
            if variant_id:
                params["vid"] = variant_id

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/product/inventory",
                    headers=self._get_headers(),
                    params=params,
                    timeout=30.0
                )
                response.raise_for_status()
                data = response.json()

                if data.get("result"):
                    return data.get("data", {})
                return {}

        except Exception as e:
            logger.error(f"Error checking inventory: {e}")
            return {}
