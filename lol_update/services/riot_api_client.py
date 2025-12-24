"""
Riot API Client using RiotWatcher library.

This module provides a configured RiotWatcher instance with proper error handling,
rate limiting, and logging. RiotWatcher automatically handles:
- Rate limiting (respects Riot's rate limits)
- Retries with exponential backoff
- Regional routing (platform vs regional endpoints)
"""

import os
import logging
from riotwatcher import LolWatcher, ApiError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Riot API Key from environment
RIOT_API_KEY = os.getenv('RIOT_API_KEY')

if not RIOT_API_KEY:
    logger.warning("RIOT_API_KEY not found in environment variables!")

# Singleton instance of LolWatcher
_lol_watcher_instance = None


def get_riot_api_client():
    """
    Get or create the singleton RiotWatcher client.

    Returns:
        LolWatcher: Configured RiotWatcher instance

    Raises:
        ValueError: If RIOT_API_KEY is not set
    """
    global _lol_watcher_instance

    if not RIOT_API_KEY:
        raise ValueError(
            "RIOT_API_KEY environment variable is not set. "
            "Please add it to your .env file."
        )

    if _lol_watcher_instance is None:
        logger.info("Initializing RiotWatcher client")
        _lol_watcher_instance = LolWatcher(RIOT_API_KEY)

    return _lol_watcher_instance


def handle_api_error(error: ApiError, context: str = ""):
    """
    Handle and log Riot API errors with appropriate messages.

    Args:
        error: The ApiError exception from RiotWatcher
        context: Additional context about what operation failed

    Raises:
        ApiError: Re-raises the error after logging
    """
    status_code = error.response.status_code

    error_messages = {
        400: f"Bad request to Riot API {context}",
        401: f"Unauthorized - check your RIOT_API_KEY {context}",
        403: f"Forbidden - API key may be invalid or expired {context}",
        404: f"Resource not found {context}",
        429: f"Rate limit exceeded {context} - RiotWatcher should handle this automatically",
        500: f"Riot API server error {context}",
        503: f"Riot API service unavailable {context}",
    }

    message = error_messages.get(status_code, f"API error {status_code} {context}")
    logger.error(f"{message}: {error}")

    raise error


# Region mappings for easier use
PLATFORM_REGIONS = {
    'na': 'na1',      # North America
    'euw': 'euw1',    # Europe West
    'eune': 'eun1',   # Europe Nordic & East
    'kr': 'kr',       # Korea
    'br': 'br1',      # Brazil
    'lan': 'la1',     # Latin America North
    'las': 'la2',     # Latin America South
    'oce': 'oc1',     # Oceania
    'tr': 'tr1',      # Turkey
    'ru': 'ru',       # Russia
    'jp': 'jp1',      # Japan
    'ph': 'ph2',      # Philippines
    'sg': 'sg2',      # Singapore
    'th': 'th2',      # Thailand
    'tw': 'tw2',      # Taiwan
    'vn': 'vn2',      # Vietnam
}

REGIONAL_ENDPOINTS = {
    'americas': 'americas',
    'europe': 'europe',
    'asia': 'asia',
    'sea': 'sea',      # Southeast Asia
}

# Map platform regions to their continental regional endpoint
PLATFORM_TO_REGIONAL = {
    'na1': 'americas',
    'br1': 'americas',
    'la1': 'americas',
    'la2': 'americas',
    'euw1': 'europe',
    'eun1': 'europe',
    'tr1': 'europe',
    'ru': 'europe',
    'kr': 'asia',
    'jp1': 'asia',
    'oc1': 'sea',
    'ph2': 'sea',
    'sg2': 'sea',
    'th2': 'sea',
    'tw2': 'sea',
    'vn2': 'sea',
}


def get_platform_region(region_code: str) -> str:
    """
    Convert a short region code to platform region for RiotWatcher.

    Args:
        region_code: Short region code (e.g., 'na', 'euw', 'kr')

    Returns:
        Platform region code (e.g., 'na1', 'euw1', 'kr')

    Examples:
        >>> get_platform_region('na')
        'na1'
        >>> get_platform_region('euw')
        'euw1'
    """
    region_lower = region_code.lower()
    return PLATFORM_REGIONS.get(region_lower, region_code)


def get_regional_endpoint(platform_region: str) -> str:
    """
    Get the regional endpoint for match/account data.

    Args:
        platform_region: Platform region code (e.g., 'na1', 'euw1')

    Returns:
        Regional endpoint (e.g., 'americas', 'europe', 'asia')

    Examples:
        >>> get_regional_endpoint('na1')
        'americas'
        >>> get_regional_endpoint('euw1')
        'europe'
    """
    return PLATFORM_TO_REGIONAL.get(platform_region, 'americas')
