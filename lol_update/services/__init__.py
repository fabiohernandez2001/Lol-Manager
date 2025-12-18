"""
Services package for Riot API integration.

This package contains services for fetching and processing data from Riot's APIs:
- riot_api_client: Base client with RiotWatcher integration
- summoner_service: Summoner profile and rank data
- match_service: Match history and details
- static_data_service: Champions, items, and runes
"""

from .riot_api_client import get_riot_api_client
from .summoner_service import fetch_summoner_by_riot_id, update_summoner_rank
from .match_service import fetch_match_history, fetch_match_details
from .static_data_service import sync_champions, sync_items, get_latest_version

__all__ = [
    'get_riot_api_client',
    'fetch_summoner_by_riot_id',
    'update_summoner_rank',
    'fetch_match_history',
    'fetch_match_details',
    'sync_champions',
    'sync_items',
    'get_latest_version',
]
