"""
AI-powered content generation using Claude API
"""
import json
import asyncio
from typing import Dict, List, Optional
from loguru import logger
import anthropic

from config import settings, CONTENT_PROMPTS


class AIContentGenerator:
    """Generate optimized product listings using Claude AI"""

    def __init__(self):
        if not settings.anthropic_api_key:
            logger.warning("Anthropic API key not set! AI generation will be disabled.")
            self.client = None
        else:
            self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    async def generate_complete_listing(self, product: Dict) -> Dict:
        """Generate complete optimized listing for a product"""
        if not self.client:
            logger.error("Anthropic client not initialized")
            return product

        logger.info(f"Generating complete listing for: {product.get('title', 'Unknown')}")

        try:
            # Generate all content in parallel
            tasks = [
                self.generate_title(product),
                self.generate_description(product),
                self.generate_bullet_points(product),
                self.generate_seo_keywords(product)
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Unpack results
            title, description, bullets, seo_keywords = results

            # Handle exceptions
            if isinstance(title, Exception):
                logger.error(f"Title generation failed: {title}")
                title = product.get("title")

            if isinstance(description, Exception):
                logger.error(f"Description generation failed: {description}")
                description = product.get("description")

            if isinstance(bullets, Exception):
                logger.error(f"Bullets generation failed: {bullets}")
                bullets = []

            if isinstance(seo_keywords, Exception):
                logger.error(f"SEO keywords generation failed: {seo_keywords}")
                seo_keywords = {}

            product["ai_title"] = title
            product["ai_description"] = description
            product["ai_bullets"] = bullets
            product["seo_keywords"] = seo_keywords

            logger.info("Complete listing generated successfully")
            return product

        except Exception as e:
            logger.error(f"Error generating listing: {e}")
            return product

    async def generate_title(self, product: Dict) -> str:
        """Generate optimized product title"""
        try:
            product_info = {
                "title": product.get("title", ""),
                "category": product.get("category", ""),
                "price": product.get("price", 0),
                "features": product.get("description", "")[:200]
            }

            prompt = CONTENT_PROMPTS["title"].format(
                product_info=json.dumps(product_info, indent=2)
            )

            response = await asyncio.to_thread(
                self.client.messages.create,
                model="claude-3-5-sonnet-20241022",
                max_tokens=200,
                messages=[{"role": "user", "content": prompt}]
            )

            title = response.content[0].text.strip()
            logger.info(f"Generated title: {title}")
            return title

        except Exception as e:
            logger.error(f"Title generation error: {e}")
            return product.get("title", "")

    async def generate_description(self, product: Dict) -> str:
        """Generate compelling product description"""
        try:
            prompt = CONTENT_PROMPTS["description"].format(
                product_name=product.get("title", ""),
                features=product.get("description", "")[:500],
                category=product.get("category", "general")
            )

            response = await asyncio.to_thread(
                self.client.messages.create,
                model="claude-3-5-sonnet-20241022",
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )

            description = response.content[0].text.strip()
            logger.info("Generated description")
            return description

        except Exception as e:
            logger.error(f"Description generation error: {e}")
            return product.get("description", "")

    async def generate_bullet_points(self, product: Dict) -> List[str]:
        """Generate benefit-focused bullet points"""
        try:
            details = {
                "title": product.get("title", ""),
                "description": product.get("description", "")[:300],
                "price": product.get("price", 0),
                "rating": product.get("rating", 0)
            }

            prompt = CONTENT_PROMPTS["bullets"].format(
                product_name=product.get("title", ""),
                details=json.dumps(details, indent=2)
            )

            response = await asyncio.to_thread(
                self.client.messages.create,
                model="claude-3-5-sonnet-20241022",
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}]
            )

            content = response.content[0].text.strip()

            # Try to parse as JSON
            try:
                bullets = json.loads(content)
                if isinstance(bullets, list):
                    logger.info(f"Generated {len(bullets)} bullet points")
                    return bullets
            except json.JSONDecodeError:
                # If not JSON, split by newlines
                bullets = [line.strip() for line in content.split("\n") if line.strip()]
                return bullets

            return []

        except Exception as e:
            logger.error(f"Bullet points generation error: {e}")
            return []

    async def generate_seo_keywords(self, product: Dict) -> Dict:
        """Generate SEO-optimized keywords"""
        try:
            prompt = CONTENT_PROMPTS["seo_keywords"].format(
                product_name=product.get("title", ""),
                description=product.get("description", "")[:300],
                category=product.get("category", "general")
            )

            response = await asyncio.to_thread(
                self.client.messages.create,
                model="claude-3-5-sonnet-20241022",
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}]
            )

            content = response.content[0].text.strip()

            # Try to parse as JSON
            try:
                keywords = json.loads(content)
                logger.info("Generated SEO keywords")
                return keywords
            except json.JSONDecodeError:
                logger.warning("Could not parse keywords as JSON")
                return {
                    "primary": product.get("title", ""),
                    "secondary": [],
                    "long_tail": []
                }

        except Exception as e:
            logger.error(f"SEO keywords generation error: {e}")
            return {}

    async def generate_variations(self, product: Dict, count: int = 3) -> List[Dict]:
        """Generate multiple variations for A/B testing"""
        logger.info(f"Generating {count} variations")

        variations = []
        for i in range(count):
            try:
                variant = await self.generate_complete_listing(product.copy())
                variant["variation_id"] = i + 1
                variations.append(variant)
                await asyncio.sleep(1)  # Rate limiting
            except Exception as e:
                logger.error(f"Error generating variation {i+1}: {e}")

        return variations

    async def optimize_for_platform(self, product: Dict, platform: str) -> Dict:
        """Optimize content for specific platform"""
        logger.info(f"Optimizing for platform: {platform}")

        platform_prompts = {
            "tiktok": "Make the content viral, trendy, and engaging for Gen Z. Use emojis and casual language.",
            "amazon": "Focus on SEO, technical specifications, and professional language. Include search-optimized keywords.",
            "shopify": "Make it conversion-focused with strong calls-to-action and benefit-driven copy.",
            "etsy": "Emphasize uniqueness, craftsmanship, and emotional appeal."
        }

        try:
            style_instruction = platform_prompts.get(
                platform.lower(),
                "Create professional, engaging content."
            )

            prompt = f"""Optimize this product listing for {platform}:

Product: {product.get('title', '')}
Description: {product.get('description', '')[:300]}

Style: {style_instruction}

Generate:
1. Platform-optimized title (60-80 chars)
2. Platform-optimized description (200-300 words)
3. 5 key bullet points

Return as JSON: {{"title": "...", "description": "...", "bullets": [...]}}"""

            response = await asyncio.to_thread(
                self.client.messages.create,
                model="claude-3-5-sonnet-20241022",
                max_tokens=1500,
                messages=[{"role": "user", "content": prompt}]
            )

            content = response.content[0].text.strip()

            # Parse JSON response
            try:
                optimized = json.loads(content)
                product[f"{platform}_optimized"] = optimized
                logger.info(f"Optimized for {platform}")
            except json.JSONDecodeError:
                logger.warning(f"Could not parse {platform} optimization")

            return product

        except Exception as e:
            logger.error(f"Platform optimization error: {e}")
            return product

    async def generate_social_captions(self, product: Dict) -> Dict[str, str]:
        """Generate social media captions for different platforms"""
        try:
            prompt = f"""Create engaging social media captions for this product:

Product: {product.get('title', '')}
Price: ${product.get('price', 0)}
Description: {product.get('description', '')[:200]}

Generate captions for:
1. TikTok (short, trendy, with hashtags)
2. Instagram (engaging, with emojis and hashtags)
3. Facebook (informative and conversion-focused)
4. Twitter (concise, punchy)

Return as JSON: {{"tiktok": "...", "instagram": "...", "facebook": "...", "twitter": "..."}}"""

            response = await asyncio.to_thread(
                self.client.messages.create,
                model="claude-3-5-sonnet-20241022",
                max_tokens=800,
                messages=[{"role": "user", "content": prompt}]
            )

            content = response.content[0].text.strip()

            captions = json.loads(content)
            logger.info("Generated social media captions")
            return captions

        except Exception as e:
            logger.error(f"Social captions generation error: {e}")
            return {}
