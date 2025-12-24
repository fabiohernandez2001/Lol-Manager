"""
Riot API Client with rate limiting and error handling.

This client handles:
- Rate limiting (per second and per 2 minutes)
- Retry logic with exponential backoff
- Platform and regional routing
- Error handling for common API responses
"""

import time
import logging
from typing import Optional, Dict, Any, List
from collections import deque
from datetime import datetime, timedelta
import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class RateLimiter:
    """Token bucket rate limiter for Riot API requests."""

    def __init__(self, requests_per_second: int = 20, requests_per_2min: int = 100):
        self.requests_per_second = requests_per_second
        self.requests_per_2min = requests_per_2min

        # Track request timestamps
        self.second_window = deque(maxlen=requests_per_second)
        self.two_min_window = deque(maxlen=requests_per_2min)

    def wait_if_needed(self):
        """Block if rate limits would be exceeded."""
        now = datetime.now()

        # Clean up old timestamps
        one_second_ago = now - timedelta(seconds=1)
        two_min_ago = now - timedelta(minutes=2)

        while self.second_window and self.second_window[0] < one_second_ago:
            self.second_window.popleft()

        while self.two_min_window and self.two_min_window[0] < two_min_ago:
            self.two_min_window.popleft()

        # Wait if limits would be exceeded
        if len(self.second_window) >= self.requests_per_second:
            sleep_time = (self.second_window[0] + timedelta(seconds=1) - now).total_seconds()
            if sleep_time > 0:
                logger.debug(f"Rate limit: sleeping for {sleep_time:.2f}s (per-second limit)")
                time.sleep(sleep_time)

        if len(self.two_min_window) >= self.requests_per_2min:
            sleep_time = (self.two_min_window[0] + timedelta(minutes=2) - now).total_seconds()
            if sleep_time > 0:
                logger.debug(f"Rate limit: sleeping for {sleep_time:.2f}s (per-2min limit)")
                time.sleep(sleep_time)

        # Record this request
        now = datetime.now()
        self.second_window.append(now)
        self.two_min_window.append(now)


class RiotAPIClient:
    """
    Client for Riot Games API with automatic rate limiting and retry logic.

    Platform routing (e.g., EUW1, NA1):
    - SUMMONER-V4
    - LEAGUE-V4
    - CHAMPION-MASTERY-V4

    Regional routing (e.g., EUROPE, AMERICAS):
    - MATCH-V5
    """

    # Platform to regional routing mapping
    PLATFORM_TO_REGION = {
        'BR1': 'americas',
        'EUN1': 'europe',
        'EUW1': 'europe',
        'JP1': 'asia',
        'KR': 'asia',
        'LA1': 'americas',
        'LA2': 'americas',
        'NA1': 'americas',
        'OC1': 'sea',
        'TR1': 'europe',
        'RU': 'europe',
        'PH2': 'sea',
        'SG2': 'sea',
        'TH2': 'sea',
        'TW2': 'sea',
        'VN2': 'sea',
    }

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.RIOT_API_KEY
        if not self.api_key:
            raise ValueError("RIOT_API_KEY not configured in settings or environment")

        self.rate_limiter = RateLimiter(
            requests_per_second=settings.RIOT_RATE_LIMIT_PER_SECOND,
            requests_per_2min=settings.RIOT_RATE_LIMIT_PER_2MIN,
        )
        self.session = requests.Session()
        self.session.headers.update({
            'X-Riot-Token': self.api_key,
            'User-Agent': 'LolManager/1.0'
        })

    def _make_request(
        self,
        url: str,
        max_retries: int = 3,
        timeout: int = 10
    ) -> Optional[Dict[str, Any]]:
        """
        Make HTTP request with rate limiting and retry logic.

        Args:
            url: Full URL to request
            max_retries: Maximum number of retry attempts
            timeout: Request timeout in seconds

        Returns:
            JSON response data or None if request fails
        """
        for attempt in range(max_retries):
            try:
                # Wait if rate limited
                self.rate_limiter.wait_if_needed()

                response = self.session.get(url, timeout=timeout)

                # Success
                if response.status_code == 200:
                    return response.json()

                # Not found
                elif response.status_code == 404:
                    logger.warning(f"Resource not found: {url}")
                    return None

                # Rate limited by Riot (should rarely happen with our rate limiter)
                elif response.status_code == 429:
                    retry_after = int(response.headers.get('Retry-After', 1))
                    logger.warning(f"Rate limited by Riot API. Retrying after {retry_after}s")
                    time.sleep(retry_after)
                    continue

                # Server errors - retry with backoff
                elif response.status_code >= 500:
                    backoff = 2 ** attempt
                    logger.warning(
                        f"Server error {response.status_code}. "
                        f"Retrying in {backoff}s (attempt {attempt + 1}/{max_retries})"
                    )
                    time.sleep(backoff)
                    continue

                # Client errors (400, 401, 403, etc.)
                else:
                    logger.error(
                        f"API request failed with status {response.status_code}: {url}\n"
                        f"Response: {response.text}"
                    )
                    return None

            except requests.exceptions.Timeout:
                logger.warning(f"Request timeout (attempt {attempt + 1}/{max_retries}): {url}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue

            except requests.exceptions.RequestException as e:
                logger.error(f"Request error: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue

        logger.error(f"Failed after {max_retries} attempts: {url}")
        return None

    # SUMMONER-V4 endpoints (platform routing)

    def get_summoner_by_name(self, region: str, summoner_name: str) -> Optional[Dict[str, Any]]:
        """Get summoner by name (uses SUMMONER-V4, platform routing)."""
        url = f"https://{region}.api.riotgames.com/lol/summoner/v4/summoners/by-name/{summoner_name}"
        return self._make_request(url)

    def get_summoner_by_puuid(self, region: str, puuid: str) -> Optional[Dict[str, Any]]:
        """Get summoner by PUUID (uses SUMMONER-V4, platform routing)."""
        url = f"https://{region}.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/{puuid}"
        return self._make_request(url)

    # LEAGUE-V4 endpoints (platform routing)

    def get_league_entries(self, region: str, summoner_id: str) -> Optional[List[Dict[str, Any]]]:
        """Get ranked league entries for summoner (uses LEAGUE-V4, platform routing)."""
        url = f"https://{region}.api.riotgames.com/lol/league/v4/entries/by-summoner/{summoner_id}"
        return self._make_request(url)

    # MATCH-V5 endpoints (regional routing)

    def get_match_list(
        self,
        platform: str,
        puuid: str,
        start: int = 0,
        count: int = 20,
        queue: Optional[int] = None,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None
    ) -> Optional[List[str]]:
        """
        Get match IDs for summoner (uses MATCH-V5, regional routing).

        Args:
            platform: Platform code (e.g., 'EUW1', 'NA1')
            puuid: Player UUID
            start: Start index (default 0)
            count: Number of matches to return (default 20, max 100)
            queue: Queue ID filter (optional)
            start_time: Epoch timestamp filter (optional)
            end_time: Epoch timestamp filter (optional)
        """
        region = self.PLATFORM_TO_REGION.get(platform.upper())
        if not region:
            logger.error(f"Unknown platform: {platform}")
            return None

        url = f"https://{region}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids"
        params = {'start': start, 'count': count}

        if queue is not None:
            params['queue'] = queue
        if start_time is not None:
            params['startTime'] = start_time
        if end_time is not None:
            params['endTime'] = end_time

        # Build query string
        query = '&'.join(f"{k}={v}" for k, v in params.items())
        full_url = f"{url}?{query}"

        return self._make_request(full_url)

    def get_match_details(self, platform: str, match_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed match data (uses MATCH-V5, regional routing).

        Args:
            platform: Platform code (e.g., 'EUW1', 'NA1')
            match_id: Match ID (format: PLATFORM_MATCHID, e.g., 'EUW1_1234567890')
        """
        region = self.PLATFORM_TO_REGION.get(platform.upper())
        if not region:
            logger.error(f"Unknown platform: {platform}")
            return None

        url = f"https://{region}.api.riotgames.com/lol/match/v5/matches/{match_id}"
        return self._make_request(url)

    # CHAMPION-MASTERY-V4 endpoints (platform routing)

    def get_champion_masteries(self, region: str, puuid: str) -> Optional[List[Dict[str, Any]]]:
        """Get all champion masteries for summoner (uses CHAMPION-MASTERY-V4, platform routing)."""
        url = f"https://{region}.api.riotgames.com/lol/champion-mastery/v4/champion-masteries/by-puuid/{puuid}"
        return self._make_request(url)
