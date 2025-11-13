"""
Web scraping integration using ScraperAPI
"""
import httpx
from typing import Dict, List, Optional
from bs4 import BeautifulSoup
from loguru import logger
from config import settings, APIEndpoints


class ScraperAPI:
    """ScraperAPI client for web scraping"""

    def __init__(self):
        self.api_key = settings.scraper_api_key
        self.base_url = APIEndpoints.SCRAPER_API_BASE

    async def scrape_url(self, url: str, render_js: bool = False) -> Optional[str]:
        """Scrape a URL and return HTML content"""
        try:
            params = {
                "api_key": self.api_key,
                "url": url
            }

            if render_js:
                params["render"] = "true"

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self.base_url,
                    params=params,
                    timeout=60.0
                )
                response.raise_for_status()
                logger.info(f"Successfully scraped: {url}")
                return response.text

        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            return None

    async def scrape_competitor_store(self, store_url: str) -> Dict:
        """Scrape competitor store for product analysis"""
        try:
            html = await self.scrape_url(store_url, render_js=True)
            if not html:
                return {}

            soup = BeautifulSoup(html, "html.parser")

            # Extract product listings (generic selectors)
            products = []

            # Try common e-commerce patterns
            product_selectors = [
                ".product-item",
                ".product-card",
                "[data-product-id]",
                ".grid-item",
                "article.product"
            ]

            for selector in product_selectors:
                items = soup.select(selector)
                if items:
                    for item in items[:20]:  # Limit to 20 products
                        product_data = self._extract_product_data(item)
                        if product_data:
                            products.append(product_data)
                    break

            logger.info(f"Scraped {len(products)} products from {store_url}")

            return {
                "url": store_url,
                "product_count": len(products),
                "products": products
            }

        except Exception as e:
            logger.error(f"Error scraping competitor store: {e}")
            return {}

    def _extract_product_data(self, element) -> Optional[Dict]:
        """Extract product data from HTML element"""
        try:
            # Try to extract common fields
            product = {}

            # Title
            title_selectors = [".product-title", "h2", "h3", ".title"]
            for selector in title_selectors:
                title_elem = element.select_one(selector)
                if title_elem:
                    product["title"] = title_elem.get_text(strip=True)
                    break

            # Price
            price_selectors = [".price", ".product-price", "[data-price]"]
            for selector in price_selectors:
                price_elem = element.select_one(selector)
                if price_elem:
                    price_text = price_elem.get_text(strip=True)
                    # Extract numeric value
                    import re
                    price_match = re.search(r'[\d,]+\.?\d*', price_text)
                    if price_match:
                        product["price"] = float(price_match.group().replace(',', ''))
                    break

            # Image
            img_elem = element.select_one("img")
            if img_elem:
                product["image"] = img_elem.get("src") or img_elem.get("data-src")

            # Link
            link_elem = element.select_one("a")
            if link_elem:
                product["url"] = link_elem.get("href")

            return product if "title" in product else None

        except Exception as e:
            logger.debug(f"Error extracting product data: {e}")
            return None

    async def scrape_sitemap(self, site_url: str) -> List[str]:
        """Scrape sitemap.xml to get all URLs"""
        try:
            sitemap_url = f"{site_url.rstrip('/')}/sitemap.xml"
            html = await self.scrape_url(sitemap_url)

            if not html:
                return []

            soup = BeautifulSoup(html, "xml")
            urls = [loc.get_text() for loc in soup.find_all("loc")]

            logger.info(f"Found {len(urls)} URLs in sitemap")
            return urls

        except Exception as e:
            logger.error(f"Error scraping sitemap: {e}")
            return []

    async def analyze_product_page(self, url: str) -> Dict:
        """Analyze a product page for detailed information"""
        try:
            html = await self.scrape_url(url, render_js=True)
            if not html:
                return {}

            soup = BeautifulSoup(html, "html.parser")

            analysis = {
                "url": url,
                "title": "",
                "description": "",
                "price": 0.0,
                "images": [],
                "features": [],
                "reviews_count": 0,
                "rating": 0.0
            }

            # Extract title
            title_elem = soup.find("h1") or soup.find("title")
            if title_elem:
                analysis["title"] = title_elem.get_text(strip=True)

            # Extract meta description
            meta_desc = soup.find("meta", {"name": "description"})
            if meta_desc:
                analysis["description"] = meta_desc.get("content", "")

            # Extract images
            images = soup.find_all("img")
            analysis["images"] = [
                img.get("src") or img.get("data-src")
                for img in images
                if img.get("src") or img.get("data-src")
            ][:10]  # Limit to 10 images

            return analysis

        except Exception as e:
            logger.error(f"Error analyzing product page: {e}")
            return {}
