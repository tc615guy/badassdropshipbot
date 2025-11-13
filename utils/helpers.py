"""
Helper utilities
"""
import re
from typing import Dict
from slugify import slugify as python_slugify


def calculate_profit(
    source_price: float,
    selling_price: float,
    shipping_cost: float = 0.0,
    platform_fee_percent: float = 0.0
) -> Dict[str, float]:
    """Calculate profit and margins"""
    platform_fee = selling_price * (platform_fee_percent / 100)
    total_cost = source_price + shipping_cost + platform_fee
    profit = selling_price - total_cost
    margin_percent = (profit / selling_price * 100) if selling_price > 0 else 0

    return {
        "selling_price": round(selling_price, 2),
        "total_cost": round(total_cost, 2),
        "profit": round(profit, 2),
        "margin_percent": round(margin_percent, 2),
        "platform_fee": round(platform_fee, 2)
    }


def format_currency(amount: float, currency: str = "USD") -> str:
    """Format currency for display"""
    symbols = {
        "USD": "$",
        "EUR": "€",
        "GBP": "£"
    }
    symbol = symbols.get(currency, "$")
    return f"{symbol}{amount:,.2f}"


def slugify_title(title: str) -> str:
    """Create URL-friendly slug from title"""
    return python_slugify(title, max_length=100)


def extract_price_from_text(text: str) -> float:
    """Extract price from text"""
    # Match patterns like $19.99, 19.99, $19
    pattern = r'\$?\s*(\d+(?:,\d{3})*(?:\.\d{2})?)'
    match = re.search(pattern, text)

    if match:
        price_str = match.group(1).replace(',', '')
        return float(price_str)

    return 0.0


def sanitize_html(html: str) -> str:
    """Remove potentially dangerous HTML"""
    # Basic sanitization - remove script tags
    html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r'<iframe[^>]*>.*?</iframe>', '', html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r'on\w+="[^"]*"', '', html, flags=re.IGNORECASE)

    return html


def validate_url(url: str) -> bool:
    """Validate if string is a valid URL"""
    pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)

    return pattern.match(url) is not None


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text to maximum length"""
    if len(text) <= max_length:
        return text

    return text[:max_length - len(suffix)].rstrip() + suffix


def parse_category(category_string: str) -> str:
    """Normalize category strings"""
    # Convert to lowercase and replace spaces/special chars
    category = category_string.lower()
    category = re.sub(r'[^\w\s-]', '', category)
    category = re.sub(r'[-\s]+', '_', category)

    return category


def format_number(number: int) -> str:
    """Format number with K/M suffix"""
    if number >= 1_000_000:
        return f"{number / 1_000_000:.1f}M"
    elif number >= 1_000:
        return f"{number / 1_000:.1f}K"
    else:
        return str(number)
