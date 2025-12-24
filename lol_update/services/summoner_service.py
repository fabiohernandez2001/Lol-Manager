"""
Summoner Service for fetching and storing player data.

This service uses RiotWatcher to fetch summoner profiles and ranked stats,
integrating the logic from API_Requests.py with Django models.
"""

import logging
import requests
from typing import Optional, Dict, Tuple
from riotwatcher import ApiError

from lol_navo.models import Summoner
from .riot_api_client import (
    get_riot_api_client,
    handle_api_error,
    get_platform_region,
    get_regional_endpoint,
    RIOT_API_KEY,
)

logger = logging.getLogger(__name__)


def fetch_summoner_by_riot_id(
    game_name: str,
    tag_line: str,
    region: str = 'euw'
) -> Optional[Summoner]:
    """
    Fetch a summoner by their Riot ID (game name + tag) and save to database.

    This replaces the get_puuid() function from API_Requests.py with full
    database integration.

    Args:
        game_name: Summoner's game name (e.g., 'koldi')
        tag_line: Summoner's tag line (e.g., 'doggy')
        region: Platform region code (e.g., 'euw', 'na', 'kr')

    Returns:
        Summoner object if successful, None otherwise

    Examples:
        >>> summoner = fetch_summoner_by_riot_id('koldi', 'doggy', 'euw')
        >>> print(summoner.puuid)
    """
    try:
        watcher = get_riot_api_client()
        platform_region = get_platform_region(region)
        regional_endpoint = get_regional_endpoint(platform_region)

        logger.info(f"Fetching summoner: {game_name}#{tag_line} from {regional_endpoint}")

        # Step 1: Get account data (PUUID) from regional endpoint
        # This replaces: get_puuid(name, tag, api_key)
        # Note: RiotWatcher 3.3.1 doesn't have account API, so we use direct requests
        account_url = f'https://{regional_endpoint}.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{game_name}/{tag_line}?api_key={RIOT_API_KEY}'
        response = requests.get(account_url, timeout=10)
        response.raise_for_status()
        account = response.json()
        puuid = account['puuid']

        logger.info(f"Found PUUID: {puuid}")

        # Step 2: Get summoner data from platform endpoint
        # This replaces: get_icon_lvl(puuid, api_key)
        summoner_data = watcher.summoner.by_puuid(
            region=platform_region,
            encrypted_puuid=puuid
        )

        # Step 3: Get ranked stats
        # This replaces: get_all_ranks(Puuid, api_key)
        ranked_stats = _fetch_ranked_stats(puuid, platform_region)

        # Step 4: Save or update in database
        # Note: Summoner model doesn't have level, summoner_id, tier, or LP fields
        # Icon field expects URL, but we'll keep it simple with the icon ID URL
        icon_id = summoner_data.get('profileIconId', 0)

        summoner, created = Summoner.objects.update_or_create(
            puuid=puuid,
            defaults={
                'username': game_name[:16],  # max_length=16
                'tag': tag_line[:5],  # max_length=5
                'server': platform_region[:5],  # max_length=5
                'icon': f"https://ddragon.leagueoflegends.com/cdn/15.24.1/img/profileicon/{icon_id}.png",
                **ranked_stats
            }
        )

        action = "Created" if created else "Updated"
        logger.info(f"{action} summoner: {game_name}#{tag_line} (PUUID: {puuid})")

        return summoner

    except ApiError as e:
        handle_api_error(e, f"for summoner {game_name}#{tag_line}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error fetching summoner {game_name}#{tag_line}: {e}")
        return None


def _fetch_ranked_stats(puuid: str, platform_region: str) -> Dict:
    """
    Fetch ranked statistics for a summoner.

    This replaces get_all_ranks() from API_Requests.py.

    Args:
        puuid: Summoner's PUUID
        platform_region: Platform region (e.g., 'euw1', 'na1')

    Returns:
        Dictionary with ranked stats to update Summoner model
    """
    try:
        watcher = get_riot_api_client()

        # Get all ranked entries for this summoner
        ranked_entries = watcher.league.by_puuid(
            region=platform_region,
            puuid=puuid
        )

        # Initialize default values
        # Note: Model uses "loses" not "losses", and rank combines tier+rank+LP
        stats = {
            'ranked_solo_rank': 'Unranked',
            'ranked_solo_wins': 0,
            'ranked_solo_loses': 0,
            'ranked_flex_rank': 'Unranked',
            'ranked_flex_wins': 0,
            'ranked_flex_loses': 0,
        }

        # Parse ranked data
        for entry in ranked_entries:
            queue_type = entry.get('queueType')
            tier = entry.get('tier', '')
            rank = entry.get('rank', '')
            lp = entry.get('leaguePoints', 0)

            # Combine tier, rank, and LP into one string
            rank_string = f"{tier} {rank} ({lp} LP)" if tier else "Unranked"

            if queue_type == 'RANKED_SOLO_5x5':
                stats.update({
                    'ranked_solo_rank': rank_string,
                    'ranked_solo_wins': entry.get('wins', 0),
                    'ranked_solo_loses': entry.get('losses', 0),
                })
            elif queue_type == 'RANKED_FLEX_SR':
                stats.update({
                    'ranked_flex_rank': rank_string,
                    'ranked_flex_wins': entry.get('wins', 0),
                    'ranked_flex_loses': entry.get('losses', 0),
                })

        return stats

    except ApiError as e:
        if e.response.status_code == 404:
            # Summoner has no ranked stats - this is normal
            logger.info(f"No ranked stats found for PUUID {puuid}")
            return {}
        else:
            handle_api_error(e, f"fetching ranked stats for {puuid}")
            return {}


def update_summoner_rank(puuid: str, region: str = 'euw') -> Optional[Summoner]:
    """
    Update ranked statistics for an existing summoner.

    Args:
        puuid: Summoner's PUUID
        region: Platform region code

    Returns:
        Updated Summoner object if successful, None otherwise
    """
    try:
        platform_region = get_platform_region(region)

        # Check if summoner exists
        summoner = Summoner.objects.filter(puuid=puuid).first()
        if not summoner:
            logger.warning(f"Summoner with PUUID {puuid} not found in database")
            return None

        logger.info(f"Updating ranked stats for {summoner.username}#{summoner.tag}")

        # Fetch updated ranked stats
        ranked_stats = _fetch_ranked_stats(puuid, platform_region)

        # Update summoner
        for key, value in ranked_stats.items():
            setattr(summoner, key, value)

        summoner.save()

        logger.info(f"Updated ranked stats for {summoner.username}#{summoner.tag}")
        return summoner

    except Exception as e:
        logger.error(f"Error updating summoner rank for {puuid}: {e}")
        return None


def get_summoner_by_puuid(puuid: str) -> Optional[Summoner]:
    """
    Get a summoner from the database by PUUID.

    Args:
        puuid: Summoner's PUUID

    Returns:
        Summoner object if found, None otherwise
    """
    try:
        return Summoner.objects.get(puuid=puuid)
    except Summoner.DoesNotExist:
        logger.warning(f"Summoner with PUUID {puuid} not found in database")
        return None
