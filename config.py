"""
Configuration management for Badass Dropship Bot
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    """Application settings"""

    # API Keys
    n8n_api_key: str = os.getenv("N8N_API_KEY", "")
    n8n_instance_url: str = os.getenv("N8N_INSTANCE_URL", "")

    tiktok_access_token: str = os.getenv("TIKTOK_ACCESS_TOKEN", "")
    tiktok_pixel_id: str = os.getenv("TIKTOK_PIXEL_ID", "")

    scraper_api_key: str = os.getenv("SCRAPER_API_KEY", "")
    se_ranking_api_key: str = os.getenv("SE_RANKING_API_KEY", "")

    rapidapi_key: str = os.getenv("RAPIDAPI_KEY", "")
    rapidapi_host: str = os.getenv("RAPIDAPI_HOST", "aliexpress-unofficial.p.rapidapi.com")

    cj_api_key: str = os.getenv("CJ_API_KEY", "")

    banggood_app_id: str = os.getenv("BANGGOOD_APP_ID", "")
    banggood_app_secret: str = os.getenv("BANGGOOD_APP_SECRET", "")

    slack_webhook_url: str = os.getenv("SLACK_WEBHOOK_URL", "")
    slack_channel: str = os.getenv("SLACK_CHANNEL", "#reviews")

    fastapi_url: str = os.getenv("FASTAPI_URL", "https://dropship-api-nioc.onrender.com")

    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")

    # Database
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./dropship.db")

    # Application
    debug: bool = os.getenv("DEBUG", "True").lower() == "true"
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    max_concurrent_tasks: int = int(os.getenv("MAX_CONCURRENT_TASKS", "5"))

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()


# API Endpoints
class APIEndpoints:
    """API endpoint configurations"""

    # Scraper API
    SCRAPER_API_BASE = "http://api.scraperapi.com"

    # SE Ranking
    SE_RANKING_BASE = "https://api4.seranking.com"

    # AliExpress (RapidAPI)
    ALIEXPRESS_BASE = "https://aliexpress-unofficial.p.rapidapi.com"

    # CJ Dropshipping
    CJ_BASE = "https://developers.cjdropshipping.com/api2.0/v1"

    # Banggood
    BANGGOOD_BASE = "https://api.banggood.com"

    # TikTok
    TIKTOK_BASE = "https://business-api.tiktok.com"


# Product Categories
PRODUCT_CATEGORIES = [
    "electronics",
    "fashion",
    "home_garden",
    "beauty",
    "sports",
    "toys",
    "jewelry",
    "automotive",
    "pet_supplies",
    "office_supplies"
]

# Platform Configurations
PLATFORMS = {
    "aliexpress": {
        "name": "AliExpress",
        "enabled": True,
        "commission_rate": 0.05
    },
    "cj_dropship": {
        "name": "CJ Dropshipping",
        "enabled": True,
        "commission_rate": 0.03
    },
    "banggood": {
        "name": "Banggood",
        "enabled": True,
        "commission_rate": 0.04
    },
    "tiktok": {
        "name": "TikTok Shop",
        "enabled": True,
        "commission_rate": 0.08
    }
}

# Content Generation Prompts
CONTENT_PROMPTS = {
    "title": """Create a compelling, SEO-optimized product title for the following product.
The title should be:
- 60-80 characters long
- Include key benefits and features
- Use power words that drive clicks
- Optimized for search engines

Product Info: {product_info}

Return only the title, nothing else.""",

    "description": """Create a persuasive, detailed product description for:

Product: {product_name}
Features: {features}
Category: {category}

The description should:
- Start with a compelling hook
- Highlight unique benefits (not just features)
- Address customer pain points
- Include social proof elements
- End with a strong call-to-action
- Be 200-300 words
- Use short paragraphs for readability
- Include relevant keywords naturally for SEO

Return the description in HTML format with proper formatting.""",

    "bullets": """Create 5-7 compelling bullet points for this product:

Product: {product_name}
Details: {details}

Each bullet should:
- Start with a benefit, then explain the feature
- Be concise (under 100 characters)
- Use action words
- Focus on what the customer gains

Return as a JSON array of strings.""",

    "seo_keywords": """Analyze this product and generate SEO keywords:

Product: {product_name}
Description: {description}
Category: {category}

Provide:
1. Primary keyword (highest search volume, moderate competition)
2. 5-10 secondary keywords
3. 5-10 long-tail keywords (low competition, specific)

Return as JSON: {{"primary": "", "secondary": [], "long_tail": []}}"""
}

# Scraping Targets
COMPETITOR_SITES = [
    "shopify.com",
    "amazon.com",
    "etsy.com",
    "ebay.com"
]

# Success Thresholds
PRODUCT_SCORE_THRESHOLDS = {
    "min_margin": 30,  # Minimum profit margin percentage
    "min_rating": 4.0,  # Minimum product rating
    "min_reviews": 50,  # Minimum number of reviews
    "max_competition": 100,  # Maximum competing listings
    "trending_score": 70  # Minimum trending score (0-100)
}

# Rate Limiting
RATE_LIMITS = {
    "scraper_api": 100,  # requests per minute
    "se_ranking": 10,
    "aliexpress": 60,
    "cj_dropship": 30,
    "anthropic": 50
}
