"""
Celery tasks for asynchronous data fetching and processing.

All tasks wrap existing service functions and add:
- Retry logic for API rate limits (429 errors)
- Retry logic for server errors (5xx)
- Error handling and logging
- Result tracking

Task Categories:
- Summoner Tasks: Fetch and update player profiles
- Match Tasks: Fetch match history and details
- Static Data Tasks: Sync champions, items, runes from Data Dragon
- Batch Tasks: Periodic updates for tracked summoners
"""

import logging
from typing import List, Optional, Dict, Any

from celery import shared_task
from riotwatcher import ApiError

from .services.summoner_service import (
    fetch_summoner_by_riot_id,
    update_summoner_rank,
)
from .services.match_service import (
    fetch_match_details,
    bulk_fetch_matches,
)
from .services.static_data_service import (
    sync_champions,
    sync_items,
    sync_runes,
    sync_all_static_data,
    get_latest_version,
    should_sync_static_data,
)
from lol_navo.models import Summoner

logger = logging.getLogger(__name__)


# ============================================================================
# SUMMONER TASKS
# ============================================================================

@shared_task(
    bind=True,
    name='lol_update.tasks.fetch_summoner_task',
    max_retries=3,
    default_retry_delay=60,  # Retry after 1 minute
)
def fetch_summoner_task(self, game_name: str, tag_line: str, region: str = 'euw') -> Optional[str]:
    """
    Async task to fetch summoner by Riot ID.

    Args:
        game_name: Summoner's game name
        tag_line: Summoner's tag line (without #)
        region: Platform region code (euw, na, kr, etc.)

    Returns:
        Summoner PUUID if successful, None otherwise

    Retries:
        - 429 (rate limit): Retry with exponential backoff
        - 5xx (server error): Retry up to 3 times
    """
    try:
        logger.info(f"Task: Fetching summoner {game_name}#{tag_line} ({region})")

        summoner = fetch_summoner_by_riot_id(game_name, tag_line, region)

        if summoner:
            logger.info(f"Task: Successfully fetched summoner {summoner.puuid}")
            return summoner.puuid
        else:
            logger.warning(f"Task: Failed to fetch summoner {game_name}#{tag_line}")
            return None

    except ApiError as e:
        # Retry on rate limit or server errors
        if e.response.status_code in [429, 500, 502, 503, 504]:
            logger.warning(
                f"Task: API error {e.response.status_code}, "
                f"retrying... (attempt {self.request.retries + 1}/3)"
            )
            raise self.retry(exc=e, countdown=60 * (self.request.retries + 1))
        else:
            logger.error(f"Task: Non-retryable API error: {e}")
            return None

    except Exception as e:
        logger.error(f"Task: Unexpected error fetching summoner: {e}")
        return None


@shared_task(
    bind=True,
    name='lol_update.tasks.update_summoner_rank_task',
    max_retries=3,
    default_retry_delay=30,
)
def update_summoner_rank_task(self, puuid: str, region: str = 'euw') -> bool:
    """
    Async task to update summoner ranked stats.

    Args:
        puuid: Summoner's PUUID
        region: Platform region code

    Returns:
        True if successful, False otherwise
    """
    try:
        logger.info(f"Task: Updating rank for PUUID {puuid[:8]}...")

        summoner = update_summoner_rank(puuid, region)

        if summoner:
            logger.info(f"Task: Updated rank for {summoner.username}")
            return True
        else:
            return False

    except ApiError as e:
        if e.response.status_code in [429, 500, 502, 503, 504]:
            logger.warning(f"Task: API error {e.response.status_code}, retrying...")
            raise self.retry(exc=e, countdown=30 * (self.request.retries + 1))
        else:
            logger.error(f"Task: Non-retryable API error: {e}")
            return False

    except Exception as e:
        logger.error(f"Task: Error updating summoner rank: {e}")
        return False


# ============================================================================
# MATCH TASKS
# ============================================================================

@shared_task(
    bind=True,
    name='lol_update.tasks.fetch_match_details_task',
    max_retries=3,
    default_retry_delay=30,
)
def fetch_match_details_task(self, match_id: str, region: str = 'euw') -> bool:
    """
    Async task to fetch and store match details.

    Args:
        match_id: Match ID to fetch (e.g., EUW1_12345678)
        region: Platform region code

    Returns:
        True if successful, False otherwise
    """
    try:
        logger.info(f"Task: Fetching match {match_id}")

        match = fetch_match_details(match_id, region)

        if match:
            logger.info(f"Task: Successfully fetched match {match_id}")
            return True
        else:
            logger.warning(f"Task: Failed to fetch match {match_id}")
            return False

    except ApiError as e:
        if e.response.status_code in [429, 500, 502, 503, 504]:
            logger.warning(f"Task: API error {e.response.status_code}, retrying...")
            raise self.retry(exc=e, countdown=30 * (self.request.retries + 1))
        else:
            logger.error(f"Task: Non-retryable API error: {e}")
            return False

    except Exception as e:
        logger.error(f"Task: Error fetching match: {e}")
        return False


@shared_task(
    bind=True,
    name='lol_update.tasks.bulk_fetch_matches_task',
    max_retries=2,
    default_retry_delay=120,
    time_limit=300,  # 5 minutes max
)
def bulk_fetch_matches_task(
    self,
    puuid: str,
    region: str = 'euw',
    count: int = 20,
    queue_type: Optional[str] = None
) -> Dict[str, Any]:
    """
    Async task to fetch multiple matches for a summoner.

    This is a long-running task (30-120 seconds typical duration).

    Args:
        puuid: Summoner's PUUID
        region: Platform region code
        count: Number of matches to fetch
        queue_type: Optional queue filter ('ranked', 'normal', etc.)

    Returns:
        Dict with success status and match count
    """
    try:
        logger.info(f"Task: Fetching {count} matches for PUUID {puuid[:8]}...")

        matches = bulk_fetch_matches(puuid, region, count, queue_type)

        logger.info(f"Task: Fetched {len(matches)} matches successfully")

        return {
            'success': True,
            'matches_fetched': len(matches),
            'puuid': puuid,
        }

    except ApiError as e:
        if e.response.status_code in [429, 500, 502, 503, 504]:
            logger.warning(f"Task: API error {e.response.status_code}, retrying...")
            raise self.retry(exc=e, countdown=120 * (self.request.retries + 1))
        else:
            logger.error(f"Task: Non-retryable API error: {e}")
            return {'success': False, 'error': str(e)}

    except Exception as e:
        logger.error(f"Task: Error bulk fetching matches: {e}")
        return {'success': False, 'error': str(e)}


# ============================================================================
# STATIC DATA TASKS
# ============================================================================

@shared_task(
    bind=True,
    name='lol_update.tasks.sync_champions_task',
    max_retries=3,
    default_retry_delay=60,
)
def sync_champions_task(self, version: Optional[str] = None) -> Dict[str, int]:
    """
    Async task to sync champion data from Data Dragon.

    Args:
        version: Specific patch version (e.g., '15.1.1'), or None for latest

    Returns:
        Dict with created and updated counts
    """
    try:
        logger.info(f"Task: Syncing champions (version: {version or 'latest'})")

        created, updated = sync_champions(version)

        logger.info(f"Task: Champions synced - {created} created, {updated} updated")

        return {'created': created, 'updated': updated}

    except Exception as e:
        logger.error(f"Task: Error syncing champions: {e}")
        raise self.retry(exc=e, countdown=60 * (self.request.retries + 1))


@shared_task(
    bind=True,
    name='lol_update.tasks.sync_items_task',
    max_retries=3,
    default_retry_delay=60,
)
def sync_items_task(self, version: Optional[str] = None) -> Dict[str, int]:
    """
    Async task to sync item data from Data Dragon.

    Args:
        version: Specific patch version, or None for latest

    Returns:
        Dict with created and updated counts
    """
    try:
        logger.info(f"Task: Syncing items (version: {version or 'latest'})")

        created, updated = sync_items(version)

        logger.info(f"Task: Items synced - {created} created, {updated} updated")

        return {'created': created, 'updated': updated}

    except Exception as e:
        logger.error(f"Task: Error syncing items: {e}")
        raise self.retry(exc=e, countdown=60 * (self.request.retries + 1))


@shared_task(
    bind=True,
    name='lol_update.tasks.sync_runes_task',
    max_retries=3,
    default_retry_delay=60,
)
def sync_runes_task(self, version: Optional[str] = None) -> Dict[str, int]:
    """
    Async task to sync rune data from Data Dragon.

    Args:
        version: Specific patch version, or None for latest

    Returns:
        Dict with created and updated counts
    """
    try:
        logger.info(f"Task: Syncing runes (version: {version or 'latest'})")

        created, updated = sync_runes(version)

        logger.info(f"Task: Runes synced - {created} created, {updated} updated")

        return {'created': created, 'updated': updated}

    except Exception as e:
        logger.error(f"Task: Error syncing runes: {e}")
        raise self.retry(exc=e, countdown=60 * (self.request.retries + 1))


@shared_task(
    bind=True,
    name='lol_update.tasks.sync_all_static_data_task',
    max_retries=2,
    default_retry_delay=120,
    time_limit=180,  # 3 minutes max
)
def sync_all_static_data_task(self, version: Optional[str] = None, force: bool = False) -> Dict[str, Any]:
    """
    Async task to sync all static data (champions, items, runes).

    This task ONLY syncs if a new Data Dragon version is detected,
    avoiding unnecessary API calls and database writes. Since Data
    Dragon versions only change when Riot releases patches (~every 2 weeks),
    this prevents wasteful daily syncs of unchanged data.

    This is a periodic task that runs every 6 hours to check for new versions.

    Args:
        version: Specific patch version, or None to auto-detect latest
        force: Force sync even if version hasn't changed (default: False)

    Returns:
        Dict with sync results including version info and whether sync occurred
    """
    from lol_navo.models import DataDragonVersion

    try:
        # Check if sync is needed (unless forced)
        if not force:
            should_sync, latest_version, stored_version = should_sync_static_data()

            if not should_sync:
                logger.info(
                    f"Task: Static data already up-to-date (version {latest_version}), "
                    f"skipping sync"
                )
                return {
                    'success': True,
                    'skipped': True,
                    'reason': 'Already on latest version',
                    'version': latest_version,
                    'stored_version': stored_version,
                }

            # Use detected version if not specified
            if not version:
                version = latest_version

        # If forced or no version check done, get latest version
        if not version:
            version = get_latest_version()
            if not version:
                logger.error("Task: Could not determine Data Dragon version")
                return {'success': False, 'error': 'Could not fetch version'}

        logger.info(f"Task: Syncing all static data for version {version}")

        # Perform sync
        results = sync_all_static_data(version)

        # Update stored version after successful sync
        DataDragonVersion.update_version(version)

        logger.info(f"Task: All static data synced to version {version} - {results}")

        return {
            'success': True,
            'skipped': False,
            'version': version,
            'results': results,
        }

    except Exception as e:
        logger.error(f"Task: Error syncing all static data: {e}")
        raise self.retry(exc=e, countdown=120 * (self.request.retries + 1))


# ============================================================================
# BATCH TASKS
# ============================================================================

@shared_task(
    bind=True,
    name='lol_update.tasks.update_tracked_summoners_ranks_task',
    max_retries=2,
    default_retry_delay=300,
    time_limit=600,  # 10 minutes max
)
def update_tracked_summoners_ranks_task(self, batch_size: int = 50) -> Dict[str, Any]:
    """
    Periodic task to update ranked stats for tracked summoners.

    This runs hourly and updates ranks for summoners who have matches.
    "Tracked" = summoners with at least one match in the database.

    Args:
        batch_size: Number of summoners to update per run

    Returns:
        Dict with update results
    """
    try:
        logger.info(f"Task: Updating ranks for {batch_size} tracked summoners")

        # Get summoners with matches (tracked users)
        tracked_summoners = Summoner.objects.filter(
            matches__isnull=False
        ).distinct()[:batch_size]

        updated_count = 0
        failed_count = 0

        for summoner in tracked_summoners:
            try:
                result = update_summoner_rank(summoner.puuid, summoner.server)
                if result:
                    updated_count += 1
                else:
                    failed_count += 1
            except Exception as e:
                logger.warning(f"Failed to update {summoner.username}: {e}")
                failed_count += 1

        logger.info(
            f"Task: Updated {updated_count}/{batch_size} summoners "
            f"({failed_count} failed)"
        )

        return {
            'success': True,
            'updated': updated_count,
            'failed': failed_count,
            'total': batch_size,
        }

    except Exception as e:
        logger.error(f"Task: Error updating tracked summoners: {e}")
        raise self.retry(exc=e, countdown=300 * (self.request.retries + 1))
