"""
AliExpress API integration via RapidAPI
"""
import httpx
from typing import List, Dict, Optional
from loguru import logger
from config import settings, APIEndpoints


class AliExpressClient:
    """AliExpress API client"""

    def __init__(self):
        self.api_key = settings.rapidapi_key
        self.host = settings.rapidapi_host
        self.base_url = APIEndpoints.ALIEXPRESS_BASE
        self.headers = {
            "X-RapidAPI-Key": self.api_key,
            "X-RapidAPI-Host": self.host
        }

    async def search_products(
        self,
        query: str,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        min_rating: float = 4.0,
        page: int = 1,
        limit: int = 20
    ) -> List[Dict]:
        """Search for products on AliExpress"""
        try:
            params = {
                "query": query,
                "page": page,
                "limit": limit
            }

            if min_price:
                params["minPrice"] = min_price
            if max_price:
                params["maxPrice"] = max_price

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/search",
                    headers=self.headers,
                    params=params,
                    timeout=30.0
                )
                response.raise_for_status()
                data = response.json()

                products = data.get("products", [])

                # Filter by rating
                filtered = [
                    p for p in products
                    if p.get("rating", 0) >= min_rating
                ]

                logger.info(f"Found {len(filtered)} products for query: {query}")
                return filtered

        except Exception as e:
            logger.error(f"AliExpress search error: {e}")
            return []

    async def get_product_details(self, product_id: str) -> Optional[Dict]:
        """Get detailed product information"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/product/{product_id}",
                    headers=self.headers,
                    timeout=30.0
                )
                response.raise_for_status()
                return response.json()

        except Exception as e:
            logger.error(f"Error fetching product {product_id}: {e}")
            return None

    async def get_featured_products(self, category: Optional[str] = None) -> List[Dict]:
        """Get featured/promo products"""
        try:
            params = {}
            if category:
                params["category"] = category

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/featured",
                    headers=self.headers,
                    params=params,
                    timeout=30.0
                )
                response.raise_for_status()
                data = response.json()

                logger.info(f"Found {len(data)} featured products")
                return data.get("products", [])

        except Exception as e:
            logger.error(f"Error fetching featured products: {e}")
            return []

    async def get_trending_products(self, category: Optional[str] = None, limit: int = 50) -> List[Dict]:
        """Get trending products"""
        try:
            # Use search with sorting by orders
            products = await self.search_products(
                query=category if category else "trending",
                limit=limit
            )

            # Sort by orders (popularity)
            sorted_products = sorted(
                products,
                key=lambda x: x.get("orders", 0),
                reverse=True
            )

            logger.info(f"Found {len(sorted_products)} trending products")
            return sorted_products

        except Exception as e:
            logger.error(f"Error fetching trending products: {e}")
            return []

    def calculate_profit_margin(
        self,
        source_price: float,
        shipping_cost: float = 0.0,
        markup_multiplier: float = 2.5
    ) -> Dict[str, float]:
        """Calculate profit margins"""
        suggested_price = (source_price + shipping_cost) * markup_multiplier
        profit = suggested_price - source_price - shipping_cost
        margin_percent = (profit / suggested_price) * 100

        return {
            "source_price": source_price,
            "shipping_cost": shipping_cost,
            "suggested_price": round(suggested_price, 2),
            "profit": round(profit, 2),
            "margin_percent": round(margin_percent, 2)
        }
