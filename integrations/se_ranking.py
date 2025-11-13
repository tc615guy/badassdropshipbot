"""
SE Ranking API integration for SEO analysis
"""
import httpx
from typing import List, Dict, Optional
from loguru import logger
from config import settings, APIEndpoints


class SERankingClient:
    """SE Ranking API client"""

    def __init__(self):
        self.api_key = settings.se_ranking_api_key
        self.base_url = APIEndpoints.SE_RANKING_BASE

    def _get_headers(self) -> Dict[str, str]:
        """Generate API headers"""
        return {
            "Authorization": f"Token {self.api_key}",
            "Content-Type": "application/json"
        }

    async def keyword_research(
        self,
        keyword: str,
        region: str = "us",
        limit: int = 50
    ) -> List[Dict]:
        """Research keywords and get related suggestions"""
        try:
            payload = {
                "phrase": keyword,
                "region_id": self._get_region_id(region),
                "limit": limit
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/keywords",
                    headers=self._get_headers(),
                    json=payload,
                    timeout=30.0
                )
                response.raise_for_status()
                data = response.json()

                keywords = data.get("data", [])
                logger.info(f"Found {len(keywords)} keywords for: {keyword}")
                return keywords

        except Exception as e:
            logger.error(f"SE Ranking keyword research error: {e}")
            return []

    async def get_keyword_difficulty(self, keyword: str, region: str = "us") -> Dict:
        """Get keyword difficulty and competition metrics"""
        try:
            payload = {
                "phrase": keyword,
                "region_id": self._get_region_id(region)
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/keyword-difficulty",
                    headers=self._get_headers(),
                    json=payload,
                    timeout=30.0
                )
                response.raise_for_status()
                data = response.json()

                return {
                    "keyword": keyword,
                    "difficulty": data.get("difficulty", 0),
                    "competition": data.get("competition", 0),
                    "search_volume": data.get("search_volume", 0),
                    "cpc": data.get("cpc", 0.0)
                }

        except Exception as e:
            logger.error(f"Error getting keyword difficulty: {e}")
            return {}

    async def analyze_competitors(
        self,
        domain: str,
        limit: int = 10
    ) -> List[Dict]:
        """Analyze competitors for a domain"""
        try:
            params = {
                "domain": domain,
                "limit": limit
            }

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/competitors",
                    headers=self._get_headers(),
                    params=params,
                    timeout=30.0
                )
                response.raise_for_status()
                data = response.json()

                competitors = data.get("data", [])
                logger.info(f"Found {len(competitors)} competitors for {domain}")
                return competitors

        except Exception as e:
            logger.error(f"Error analyzing competitors: {e}")
            return []

    async def get_search_volume(self, keywords: List[str], region: str = "us") -> Dict[str, int]:
        """Get search volume for multiple keywords"""
        try:
            payload = {
                "phrases": keywords,
                "region_id": self._get_region_id(region)
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/search-volume",
                    headers=self._get_headers(),
                    json=payload,
                    timeout=30.0
                )
                response.raise_for_status()
                data = response.json()

                volumes = {}
                for item in data.get("data", []):
                    volumes[item["phrase"]] = item.get("search_volume", 0)

                logger.info(f"Got search volumes for {len(volumes)} keywords")
                return volumes

        except Exception as e:
            logger.error(f"Error getting search volumes: {e}")
            return {}

    def _get_region_id(self, region: str) -> str:
        """Map region code to SE Ranking region ID"""
        region_map = {
            "us": "2840",
            "uk": "2826",
            "ca": "2124",
            "au": "2036"
        }
        return region_map.get(region.lower(), "2840")

    async def find_low_competition_keywords(
        self,
        base_keyword: str,
        min_volume: int = 100,
        max_difficulty: int = 30
    ) -> List[Dict]:
        """Find low-competition, high-value keywords"""
        try:
            # Get keyword suggestions
            keywords = await self.keyword_research(base_keyword, limit=100)

            # Filter for low competition and good volume
            filtered = []
            for kw in keywords:
                if (kw.get("search_volume", 0) >= min_volume and
                    kw.get("difficulty", 100) <= max_difficulty):
                    filtered.append(kw)

            # Sort by search volume
            filtered.sort(key=lambda x: x.get("search_volume", 0), reverse=True)

            logger.info(f"Found {len(filtered)} low-competition keywords")
            return filtered

        except Exception as e:
            logger.error(f"Error finding keywords: {e}")
            return []
