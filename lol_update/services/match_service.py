"""
Match Service for fetching and storing match data.

This service uses RiotWatcher to fetch match history and details,
integrating the logic from API_Requests.py (matches_ids, match_info, timeline).
"""

import logging
import json
from typing import List, Optional, Dict
from datetime import datetime
from riotwatcher import ApiError

from lol_navo.models import Match, MatchSummoners, Summoner, Champion
from .riot_api_client import (
    get_riot_api_client,
    handle_api_error,
    get_platform_region,
    get_regional_endpoint,
)

logger = logging.getLogger(__name__)


def fetch_match_history(
    puuid: str,
    region: str = 'euw',
    count: int = 20,
    start: int = 0,
    queue_type: Optional[str] = None
) -> List[str]:
    """
    Fetch match history IDs for a summoner.

    This replaces matches_ids() from API_Requests.py.

    Args:
        puuid: Summoner's PUUID
        region: Platform region code
        count: Number of matches to fetch (max 100)
        start: Starting index for pagination
        queue_type: Optional queue filter ('ranked', 'normal', etc.)

    Returns:
        List of match IDs

    Examples:
        >>> match_ids = fetch_match_history('PUUID123', 'euw', count=10)
        >>> print(len(match_ids))
        10
    """
    try:
        watcher = get_riot_api_client()
        platform_region = get_platform_region(region)
        regional_endpoint = get_regional_endpoint(platform_region)

        logger.info(
            f"Fetching {count} matches for PUUID {puuid[:8]}... "
            f"from {regional_endpoint} (start={start})"
        )

        # Build parameters
        params = {
            'start': start,
            'count': min(count, 100),  # API limit is 100
        }

        if queue_type:
            params['type'] = queue_type

        # Fetch match IDs
        match_ids = watcher.match.matchlist_by_puuid(
            region=regional_endpoint,
            puuid=puuid,
            **params
        )

        logger.info(f"Found {len(match_ids)} matches")
        return match_ids

    except ApiError as e:
        handle_api_error(e, f"fetching match history for {puuid[:8]}...")
        return []
    except Exception as e:
        logger.error(f"Unexpected error fetching match history: {e}")
        return []


def fetch_match_details(match_id: str, region: str = 'euw') -> Optional[Match]:
    """
    Fetch full match details and save to database.

    This replaces match_info() from API_Requests.py and implements the
    participant extraction logic from the bottom of that file.

    Args:
        match_id: Match ID (e.g., 'EUW1_1234567890')
        region: Platform region code

    Returns:
        Match object if successful, None otherwise

    Examples:
        >>> match = fetch_match_details('EUW1_1234567890', 'euw')
        >>> print(match.duration)
    """
    try:
        # Check if match already exists
        if Match.objects.filter(id=match_id).exists():
            logger.info(f"Match {match_id} already exists in database")
            return Match.objects.get(id=match_id)

        watcher = get_riot_api_client()
        platform_region = get_platform_region(region)
        regional_endpoint = get_regional_endpoint(platform_region)

        logger.info(f"Fetching match details for {match_id}")

        # Fetch match data
        match_data = watcher.match.by_id(
            region=regional_endpoint,
            match_id=match_id
        )

        # Parse match metadata
        info = match_data['info']
        metadata = match_data['metadata']

        # Create Match object - using model field names
        from datetime import timedelta

        match = Match.objects.create(
            id=match_id,  # Match model uses 'id' not 'match_id'
            duration=timedelta(seconds=info.get('gameDuration', 0)),  # DurationField
            winner_team=100 if _determine_winner(info) == 1 else 200,  # WINNER_CHOICES format
            region=_extract_region_from_match_id(match_id),
            match_timestamp=datetime.fromtimestamp(info.get('gameCreation', 0) / 1000),
            queue_type=info.get('queueId'),
            time_lane='',  # Default value
            gold_diff=0,  # We'll calculate this later if needed
            raw_data=json.dumps(match_data)  # Store full JSON for future reprocessing
        )

        logger.info(f"Created Match {match_id}")

        # Parse participants and create MatchSummoners
        participants = info.get('participants', [])
        _create_match_summoners(match, participants)

        return match

    except ApiError as e:
        handle_api_error(e, f"fetching match {match_id}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error fetching match {match_id}: {e}")
        return None


def _determine_winner(match_info: Dict) -> int:
    """
    Determine which team won the match.

    Args:
        match_info: Match info section from API response

    Returns:
        1 if blue team won, 2 if red team won, 0 if unknown
    """
    teams = match_info.get('teams', [])

    for team in teams:
        if team.get('win'):
            return 1 if team.get('teamId') == 100 else 2

    return 0


def _extract_region_from_match_id(match_id: str) -> str:
    """
    Extract region from match ID.

    Args:
        match_id: Match ID (e.g., 'EUW1_1234567890')

    Returns:
        Region code (e.g., 'EUW1')
    """
    return match_id.split('_')[0] if '_' in match_id else 'UNKNOWN'


def _create_match_summoners(match: Match, participants: List[Dict]) -> None:
    """
    Create MatchSummoners entries for all participants.

    This implements the participant extraction logic from API_Requests.py
    (lines 91-123).

    Args:
        match: Match object
        participants: List of participant data from API
    """
    for participant in participants:
        try:
            # Get or create summoner
            puuid = participant.get('puuid')
            if not puuid:
                logger.warning(f"Participant in match {match.id} missing PUUID")
                continue

            summoner, created = Summoner.objects.get_or_create(
                puuid=puuid,
                defaults={
                    'username': participant.get('riotIdGameName', 'Unknown'),
                    'tag': participant.get('riotIdTagline', 'Unknown'),
                    'server': match.region,
                }
            )

            if created:
                logger.info(f"Created new summoner from match: {summoner.username}#{summoner.tag}")

            # Get champion
            champion_id = participant.get('championId')
            try:
                champion = Champion.objects.get(id=champion_id)
            except Champion.DoesNotExist:
                logger.warning(f"Champion {champion_id} not found in database")
                champion = None

            # Extract items (item0-item6)
            items = [
                participant.get(f'item{i}')
                for i in range(7)
            ]

            # Extract rune data
            perks = participant.get('perks', {})
            rune_ids = []
            for style in perks.get('styles', []):
                for selection in style.get('selections', []):
                    rune_ids.append(selection.get('perk'))

            # Extract summoner spells
            summoner_spell_ids = [
                participant.get('summoner1Id'),
                participant.get('summoner2Id')
            ]

            # Create MatchSummoners entry
            MatchSummoners.objects.create(
                match=match,
                summoner=summoner,
                champion=champion,
                result=participant.get('win', False),
                kills=participant.get('kills', 0),
                deaths=participant.get('deaths', 0),
                assists=participant.get('assists', 0),
                items=json.dumps(items),
                rune_ids=json.dumps(rune_ids),
                summoner_spell_ids=json.dumps(summoner_spell_ids),
                cs=participant.get('totalMinionsKilled', 0),
                wards_placed=participant.get('wardsPlaced', 0),
                vision_score=participant.get('visionScore', 0),
                damage_dealt=participant.get('totalDamageDealt', 0),
                damage_taken=participant.get('totalDamageTaken', 0),
                healing=participant.get('totalHeal', 0),
                damage_mitigated=participant.get('damageSelfMitigated', 0),
                gold=participant.get('goldEarned', 0),
                role=participant.get('teamPosition', 'UNKNOWN'),  # TOP, JUNGLE, MIDDLE, BOTTOM, UTILITY
                lane=participant.get('lane', 'UNKNOWN'),
            )

            logger.debug(f"Created MatchSummoner for {summoner.username} in {match.id}")

        except Exception as e:
            logger.error(f"Error creating MatchSummoner for participant in {match.id}: {e}")
            continue


def fetch_match_timeline(match_id: str, region: str = 'euw') -> Optional[Dict]:
    """
    Fetch match timeline for detailed event data.

    This replaces timeline() from API_Requests.py.
    Timeline data can be used for more accurate role detection and detailed analysis.

    Args:
        match_id: Match ID
        region: Platform region code

    Returns:
        Timeline data dictionary, or None if error

    Note:
        This is optional and can be used for enhanced analysis.
        Basic role data is already available in match details.
    """
    try:
        watcher = get_riot_api_client()
        platform_region = get_platform_region(region)
        regional_endpoint = get_regional_endpoint(platform_region)

        logger.info(f"Fetching timeline for match {match_id}")

        timeline_data = watcher.match.timeline_by_match(
            region=regional_endpoint,
            match_id=match_id
        )

        return timeline_data

    except ApiError as e:
        handle_api_error(e, f"fetching timeline for {match_id}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error fetching timeline: {e}")
        return None


def bulk_fetch_matches(
    puuid: str,
    region: str = 'euw',
    count: int = 20,
    queue_type: Optional[str] = None
) -> List[Match]:
    """
    Fetch and store multiple matches for a summoner.

    This is a convenience function that combines fetch_match_history
    and fetch_match_details.

    Args:
        puuid: Summoner's PUUID
        region: Platform region code
        count: Number of matches to fetch
        queue_type: Optional queue filter

    Returns:
        List of Match objects created
    """
    match_ids = fetch_match_history(puuid, region, count, queue_type=queue_type)

    matches = []
    for match_id in match_ids:
        match = fetch_match_details(match_id, region)
        if match:
            matches.append(match)

    logger.info(f"Fetched and stored {len(matches)}/{len(match_ids)} matches")
    return matches
