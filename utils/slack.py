"""
Slack notifications
"""
import httpx
from typing import Dict, Optional
from loguru import logger
from config import settings


class SlackNotifier:
    """Send notifications to Slack"""

    def __init__(self):
        self.webhook_url = settings.slack_webhook_url
        self.channel = settings.slack_channel

    async def send_notification(
        self,
        message: str,
        title: Optional[str] = None,
        color: str = "good",
        fields: Optional[Dict] = None
    ) -> bool:
        """Send a notification to Slack"""
        if not self.webhook_url:
            logger.warning("Slack webhook URL not configured")
            return False

        try:
            # Build attachment
            attachment = {
                "color": color,
                "text": message
            }

            if title:
                attachment["title"] = title

            if fields:
                attachment["fields"] = [
                    {"title": k, "value": str(v), "short": True}
                    for k, v in fields.items()
                ]

            payload = {
                "channel": self.channel,
                "attachments": [attachment]
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.webhook_url,
                    json=payload,
                    timeout=10.0
                )
                response.raise_for_status()

            logger.info("Slack notification sent")
            return True

        except Exception as e:
            logger.error(f"Error sending Slack notification: {e}")
            return False

    async def notify_product_found(self, product: Dict) -> bool:
        """Notify when a winning product is found"""
        message = f"🎯 *Winning Product Found!*\n\n{product.get('title', 'Unknown Product')}"

        fields = {
            "Source": product.get("source", "unknown"),
            "Score": f"{product.get('overall_score', 0):.1f}/100",
            "Profit Margin": f"{product.get('profit_margin', 0):.1f}%",
            "Rating": f"{product.get('rating', 0):.1f}⭐",
            "Orders": product.get("orders", 0),
            "Suggested Price": f"${product.get('suggested_price', 0):.2f}"
        }

        return await self.send_notification(
            message=message,
            title="New Product Alert",
            color="good",
            fields=fields
        )

    async def notify_listing_published(self, product: Dict, platforms: Dict[str, bool]) -> bool:
        """Notify when a product is published"""
        successful_platforms = [p for p, success in platforms.items() if success]

        message = f"✅ *Product Published*\n\n{product.get('title', 'Unknown Product')}"

        fields = {
            "Platforms": ", ".join(successful_platforms) if successful_platforms else "None",
            "Price": f"${product.get('suggested_price', 0):.2f}",
            "Profit": f"${product.get('profit_margin', 0):.2f}"
        }

        color = "good" if successful_platforms else "danger"

        return await self.send_notification(
            message=message,
            title="Listing Published",
            color=color,
            fields=fields
        )

    async def notify_error(self, error_type: str, error_message: str) -> bool:
        """Notify about errors"""
        message = f"❌ *Error Occurred*\n\nType: {error_type}\n\nDetails: {error_message}"

        return await self.send_notification(
            message=message,
            title="System Error",
            color="danger"
        )

    async def notify_daily_summary(self, stats: Dict) -> bool:
        """Send daily performance summary"""
        message = "📊 *Daily Performance Summary*"

        fields = {
            "Products Discovered": stats.get("discovered", 0),
            "Products Published": stats.get("published", 0),
            "Total Revenue": f"${stats.get('revenue', 0):.2f}",
            "Total Orders": stats.get("orders", 0),
            "Avg Order Value": f"${stats.get('avg_order_value', 0):.2f}"
        }

        return await self.send_notification(
            message=message,
            title="Daily Summary",
            color="#36a64f",
            fields=fields
        )

    async def notify_competition_alert(self, competitor: str, products: int) -> bool:
        """Alert about competitor activity"""
        message = f"👀 *Competitor Alert*\n\n{competitor} has listed {products} new products"

        return await self.send_notification(
            message=message,
            title="Competitor Activity",
            color="warning"
        )
