"""
Product discovery and research engine
"""
import asyncio
from typing import List, Dict, Optional
from loguru import logger
from sqlalchemy.orm import Session

from integrations import (
    AliExpressClient,
    CJDropshippingClient,
    ScraperAPI,
    SERankingClient,
    TikTokClient
)
from models.database import Product
from config import PRODUCT_SCORE_THRESHOLDS


class ProductScout:
    """Intelligent product discovery system"""

    def __init__(self):
        self.aliexpress = AliExpressClient()
        self.cj = CJDropshippingClient()
        self.scraper = ScraperAPI()
        self.seo = SERankingClient()
        self.tiktok = TikTokClient()

    async def discover_products(
        self,
        source: str = "all",
        category: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict]:
        """Discover products from multiple sources"""
        logger.info(f"Starting product discovery: source={source}, category={category}, limit={limit}")

        tasks = []

        if source in ["all", "aliexpress"]:
            tasks.append(self._discover_aliexpress(category, limit))

        if source in ["all", "cj"]:
            tasks.append(self._discover_cj(category, limit))

        if source in ["all", "tiktok"]:
            tasks.append(self._discover_tiktok(category, limit))

        # Run all discoveries in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Flatten results
        all_products = []
        for result in results:
            if isinstance(result, list):
                all_products.extend(result)
            elif isinstance(result, Exception):
                logger.error(f"Discovery error: {result}")

        # Score and rank products
        scored_products = [self._calculate_product_score(p) for p in all_products]
        scored_products.sort(key=lambda x: x.get("overall_score", 0), reverse=True)

        logger.info(f"Discovered {len(scored_products)} total products")
        return scored_products[:limit]

    async def _discover_aliexpress(self, category: Optional[str], limit: int) -> List[Dict]:
        """Discover products from AliExpress"""
        try:
            query = category if category else "trending"
            products = await self.aliexpress.search_products(
                query=query,
                min_rating=4.0,
                limit=limit
            )

            formatted = []
            for p in products:
                formatted.append({
                    "source": "aliexpress",
                    "external_id": p.get("productId", p.get("id")),
                    "title": p.get("title", p.get("productTitle")),
                    "description": p.get("description", ""),
                    "price": float(p.get("salePrice", p.get("price", 0))),
                    "rating": float(p.get("averageStarRate", p.get("rating", 0))),
                    "reviews": int(p.get("evaluateScore", p.get("reviews", 0))),
                    "orders": int(p.get("orders", 0)),
                    "images": p.get("images", []),
                    "category": category or "general"
                })

            logger.info(f"Found {len(formatted)} products from AliExpress")
            return formatted

        except Exception as e:
            logger.error(f"AliExpress discovery error: {e}")
            return []

    async def _discover_cj(self, category: Optional[str], limit: int) -> List[Dict]:
        """Discover products from CJ Dropshipping"""
        try:
            keyword = category if category else "trending"
            products = await self.cj.search_products(
                keyword=keyword,
                page_size=limit
            )

            formatted = []
            for p in products:
                formatted.append({
                    "source": "cj_dropship",
                    "external_id": p.get("pid"),
                    "title": p.get("productNameEn"),
                    "description": p.get("description", ""),
                    "price": float(p.get("sellPrice", 0)),
                    "rating": 0.0,  # CJ doesn't always provide ratings
                    "reviews": 0,
                    "orders": 0,
                    "images": p.get("productImage", "").split(",") if p.get("productImage") else [],
                    "category": category or "general"
                })

            logger.info(f"Found {len(formatted)} products from CJ")
            return formatted

        except Exception as e:
            logger.error(f"CJ discovery error: {e}")
            return []

    async def _discover_tiktok(self, category: Optional[str], limit: int) -> List[Dict]:
        """Discover trending products from TikTok"""
        try:
            products = await self.tiktok.get_trending_products(category=category)

            formatted = []
            for p in products[:limit]:
                formatted.append({
                    "source": "tiktok",
                    "external_id": p.get("product_id"),
                    "title": p.get("product_name"),
                    "description": p.get("description", ""),
                    "price": float(p.get("price", 0)),
                    "rating": float(p.get("rating", 0)),
                    "reviews": int(p.get("review_count", 0)),
                    "orders": int(p.get("sales", 0)),
                    "images": p.get("images", []),
                    "category": category or "general"
                })

            logger.info(f"Found {len(formatted)} trending products from TikTok")
            return formatted

        except Exception as e:
            logger.error(f"TikTok discovery error: {e}")
            return []

    async def analyze_competitor(self, competitor_url: str) -> Dict:
        """Analyze competitor store"""
        logger.info(f"Analyzing competitor: {competitor_url}")

        try:
            # Scrape competitor store
            store_data = await self.scraper.scrape_competitor_store(competitor_url)

            # Get sitemap for deeper analysis
            sitemap_urls = await self.scraper.scrape_sitemap(competitor_url)

            analysis = {
                "url": competitor_url,
                "product_count": store_data.get("product_count", 0),
                "products": store_data.get("products", []),
                "total_pages": len(sitemap_urls),
                "insights": []
            }

            # Analyze pricing
            prices = [p.get("price", 0) for p in store_data.get("products", []) if p.get("price")]
            if prices:
                analysis["avg_price"] = sum(prices) / len(prices)
                analysis["price_range"] = {"min": min(prices), "max": max(prices)}
                analysis["insights"].append(f"Average product price: ${analysis['avg_price']:.2f}")

            # Identify top categories
            categories = {}
            for product in store_data.get("products", []):
                cat = product.get("category", "uncategorized")
                categories[cat] = categories.get(cat, 0) + 1

            analysis["top_categories"] = sorted(
                categories.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]

            logger.info(f"Competitor analysis complete: {len(store_data.get('products', []))} products")
            return analysis

        except Exception as e:
            logger.error(f"Competitor analysis error: {e}")
            return {}

    def _calculate_product_score(self, product: Dict) -> Dict:
        """Calculate overall product score based on multiple factors"""
        score = 0
        max_score = 100

        # Profit margin score (0-30 points)
        price = product.get("price", 0)
        if price > 0:
            profit_calc = self.aliexpress.calculate_profit_margin(price)
            margin = profit_calc.get("margin_percent", 0)
            product["profit_margin"] = margin
            product["suggested_price"] = profit_calc.get("suggested_price", price * 2.5)

            if margin >= PRODUCT_SCORE_THRESHOLDS["min_margin"]:
                score += min(30, (margin / 50) * 30)

        # Rating score (0-20 points)
        rating = product.get("rating", 0)
        if rating >= PRODUCT_SCORE_THRESHOLDS["min_rating"]:
            score += (rating / 5.0) * 20

        # Social proof score (0-25 points)
        reviews = product.get("reviews", 0)
        orders = product.get("orders", 0)

        if reviews >= PRODUCT_SCORE_THRESHOLDS["min_reviews"]:
            score += min(15, (reviews / 500) * 15)

        if orders > 0:
            score += min(10, (orders / 1000) * 10)

        # Trending score (0-25 points)
        # Products with high orders relative to reviews are trending
        if reviews > 0:
            trending_ratio = orders / reviews
            trending_score = min(25, trending_ratio * 5)
            score += trending_score
            product["trending_score"] = trending_score
        else:
            product["trending_score"] = 0

        product["overall_score"] = round(score, 2)
        product["profit_score"] = round((margin if price > 0 else 0), 2)
        product["competition_score"] = 50  # Placeholder - would need SEO data

        return product

    async def find_winning_products(
        self,
        min_score: float = 70.0,
        sources: List[str] = ["all"],
        limit: int = 20
    ) -> List[Dict]:
        """Find high-scoring winning products"""
        logger.info(f"Searching for winning products (min_score={min_score})")

        all_products = []
        for source in sources:
            products = await self.discover_products(source=source, limit=100)
            all_products.extend(products)

        # Filter by minimum score
        winners = [
            p for p in all_products
            if p.get("overall_score", 0) >= min_score
        ]

        logger.info(f"Found {len(winners)} winning products")
        return winners[:limit]

    async def enrich_product_with_seo(self, product: Dict) -> Dict:
        """Enrich product with SEO data"""
        try:
            title = product.get("title", "")
            if not title:
                return product

            # Get keyword data
            keywords = await self.seo.keyword_research(title, limit=20)

            # Find low-competition keywords
            low_comp = await self.seo.find_low_competition_keywords(
                title,
                min_volume=100,
                max_difficulty=30
            )

            product["seo_keywords"] = {
                "primary": title,
                "secondary": [k.get("phrase") for k in keywords[:5]],
                "long_tail": [k.get("phrase") for k in low_comp[:10]]
            }

            logger.info(f"Enriched product with SEO data: {title}")
            return product

        except Exception as e:
            logger.error(f"SEO enrichment error: {e}")
            return product
