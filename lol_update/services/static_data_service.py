"""
Static Data Service for syncing champions, items, and runes from Data Dragon.

This service improves upon the existing views.py implementation by adding:
- Dynamic version fetching
- Better error handling and logging
- Rune data support
- Batch processing for performance
"""

import requests
import logging
from typing import Optional, Dict, List, Tuple
from django.db import transaction

from lol_navo.models import Champion, Item, Rune

logger = logging.getLogger(__name__)

# Data Dragon base URLs
DDRAGON_VERSION_URL = "https://ddragon.leagueoflegends.com/api/versions.json"
DDRAGON_CDN_BASE = "https://ddragon.leagueoflegends.com/cdn"


def get_latest_version() -> Optional[str]:
    """
    Fetch the latest League of Legends patch version from Data Dragon.

    Returns:
        Version string (e.g., '15.21.1') or None if error

    Examples:
        >>> version = get_latest_version()
        >>> print(version)
        '15.21.1'
    """
    try:
        logger.info("Fetching latest Data Dragon version")
        response = requests.get(DDRAGON_VERSION_URL, timeout=10)
        response.raise_for_status()

        versions = response.json()
        latest = versions[0]

        logger.info(f"Latest version: {latest}")
        return latest

    except requests.RequestException as e:
        logger.error(f"Error fetching Data Dragon version: {e}")
        return None
    except (IndexError, ValueError) as e:
        logger.error(f"Error parsing version data: {e}")
        return None


def sync_champions(version: Optional[str] = None, language: str = 'en_US') -> Tuple[int, int]:
    """
    Sync champion data from Data Dragon to database.

    This improves upon get_champions() from views.py by:
    - Using dynamic version (not hardcoded)
    - Adding transaction safety
    - Better error handling
    - Configurable language

    Args:
        version: Specific version to fetch (defaults to latest)
        language: Language code for champion data (default: 'en_US')

    Returns:
        Tuple of (created_count, updated_count)

    Examples:
        >>> created, updated = sync_champions()
        >>> print(f"Created {created}, updated {updated} champions")
    """
    if not version:
        version = get_latest_version()
        if not version:
            logger.error("Could not determine Data Dragon version")
            return 0, 0

    try:
        url = f"{DDRAGON_CDN_BASE}/{version}/data/{language}/champion.json"
        logger.info(f"Fetching champions from {url}")

        response = requests.get(url, timeout=30)
        response.raise_for_status()

        data = response.json()
        champions_data = data.get('data', {})

        created_count = 0
        updated_count = 0

        with transaction.atomic():
            for champion_key, champion in champions_data.items():
                try:
                    # Parse champion data
                    champion_id = int(champion['key'])

                    champion_obj, created = Champion.objects.update_or_create(
                        id=champion_id,
                        defaults={
                            'icon': f'{DDRAGON_CDN_BASE}/{version}/img/champion/{champion["image"]["full"]}',
                            'name': champion.get('name', ''),
                            'tags': champion.get('tags', []),
                            'title': champion.get('title', ''),
                            'description': champion.get('blurb', ''),
                            'attack': champion['info'].get('attack', 0),
                            'defense': champion['info'].get('defense', 0),
                            'magic': champion['info'].get('magic', 0),
                            'difficulty': champion['info'].get('difficulty', 0),
                            'partype': champion.get('partype', ''),
                            'hp': champion['stats'].get('hp', 0),
                            'hp_per_level': champion['stats'].get('hpperlevel', 0),
                            'mp': champion['stats'].get('mp', 0),
                            'mp_per_level': champion['stats'].get('mpperlevel', 0),
                            'move_speed': champion['stats'].get('movespeed', 0),
                            'armor': champion['stats'].get('armor', 0),
                            'armor_per_level': champion['stats'].get('armorperlevel', 0),
                            'spell_block': champion['stats'].get('spellblock', 0),
                            'spell_block_per_level': champion['stats'].get('spellblockperlevel', 0),
                            'attack_range': champion['stats'].get('attackrange', 0),
                            'hp_regen': champion['stats'].get('hpregen', 0),
                            'hp_regen_per_level': champion['stats'].get('hpregenperlevel', 0),
                            'crit': champion['stats'].get('crit', 0),
                            'crit_per_level': champion['stats'].get('critperlevel', 0),
                            'attack_damage': champion['stats'].get('attackdamage', 0),
                            'attack_damage_per_level': champion['stats'].get('attackdamageperlevel', 0),
                            'attack_speed': champion['stats'].get('attackspeed', 0),
                            'attack_speed_per_level': champion['stats'].get('attackspeedperlevel', 0),
                        }
                    )

                    if created:
                        created_count += 1
                    else:
                        updated_count += 1

                except Exception as e:
                    logger.error(f"Error processing champion {champion.get('name', 'Unknown')}: {e}")
                    continue

        logger.info(f"Champion sync complete: {created_count} created, {updated_count} updated")
        return created_count, updated_count

    except requests.RequestException as e:
        logger.error(f"Error fetching champions: {e}")
        return 0, 0
    except Exception as e:
        logger.error(f"Unexpected error syncing champions: {e}")
        return 0, 0


def sync_items(version: Optional[str] = None, language: str = 'en_US') -> Tuple[int, int]:
    """
    Sync item data from Data Dragon to database.

    This improves upon get_items() from views.py.

    Args:
        version: Specific version to fetch (defaults to latest)
        language: Language code for item data (default: 'en_US')

    Returns:
        Tuple of (created_count, updated_count)
    """
    if not version:
        version = get_latest_version()
        if not version:
            logger.error("Could not determine Data Dragon version")
            return 0, 0

    try:
        url = f"{DDRAGON_CDN_BASE}/{version}/data/{language}/item.json"
        logger.info(f"Fetching items from {url}")

        response = requests.get(url, timeout=30)
        response.raise_for_status()

        data = response.json()
        items_data = data.get('data', {})

        created_count = 0
        updated_count = 0

        with transaction.atomic():
            for item_key, item in items_data.items():
                try:
                    # Extract nested data safely
                    gold_data = item.get('gold', {})
                    image_data = item.get('image', {})

                    item_obj, created = Item.objects.update_or_create(
                        id=item_key,
                        defaults={
                            'name': item.get('name', ''),
                            'plaintext': item.get('plaintext', ''),
                            'description': item.get('description', ''),
                            'colloq': item.get('colloq', ''),
                            'stacks': item.get('stacks'),
                            'depth': item.get('depth'),
                            'consumed': item.get('consumed'),
                            'consume_on_full': item.get('consume_on_full'),
                            'in_store': item.get('inStore', True),
                            'hide_from_all': item.get('hideFromAll', False),
                            'required_champion': item.get('requiredChampion', ''),
                            'required_ally': item.get('requiredAlly', ''),
                            'special_recipe': item.get('specialRecipe'),
                            'required_buff_currency_name': item.get('requiredBuffCurrencyName', ''),
                            'required_buff_currency_cost': item.get('requiredBuffCurrencyCost'),
                            'base_gold': gold_data.get('base', 0),
                            'purchasable': gold_data.get('purchasable', False),
                            'total_gold': gold_data.get('total', 0),
                            'sell_gold': gold_data.get('sell', 0),
                            'image': f"{DDRAGON_CDN_BASE}/{version}/img/item/{image_data.get('full', '')}" if image_data.get('full') else "",
                            'stats': item.get('stats', {}),
                            'effect': item.get('effect', {}),
                            'builds_into': item.get('into', []),
                            'builds_from': item.get('from', []),
                            'tags': item.get('tags', []),
                            'maps': item.get('maps', {}),
                        }
                    )

                    if created:
                        created_count += 1
                    else:
                        updated_count += 1

                except Exception as e:
                    logger.error(f"Error processing item {item.get('name', 'Unknown')}: {e}")
                    continue

        logger.info(f"Item sync complete: {created_count} created, {updated_count} updated")
        return created_count, updated_count

    except requests.RequestException as e:
        logger.error(f"Error fetching items: {e}")
        return 0, 0
    except Exception as e:
        logger.error(f"Unexpected error syncing items: {e}")
        return 0, 0


def sync_runes(version: Optional[str] = None, language: str = 'en_US') -> Tuple[int, int]:
    """
    Sync rune data from Data Dragon to database.

    Args:
        version: Specific version to fetch (defaults to latest)
        language: Language code for rune data (default: 'en_US')

    Returns:
        Tuple of (created_count, updated_count)
    """
    if not version:
        version = get_latest_version()
        if not version:
            logger.error("Could not determine Data Dragon version")
            return 0, 0

    try:
        url = f"{DDRAGON_CDN_BASE}/{version}/data/{language}/runesReforged.json"
        logger.info(f"Fetching runes from {url}")

        response = requests.get(url, timeout=30)
        response.raise_for_status()

        runes_data = response.json()

        created_count = 0
        updated_count = 0

        with transaction.atomic():
            # Each element is a rune tree (Precision, Domination, etc.)
            for tree in runes_data:
                tree_id = tree.get('id')
                tree_name = tree.get('name', '')

                # Process slots (keystones and regular runes)
                for slot_idx, slot in enumerate(tree.get('slots', [])):
                    for rune in slot.get('runes', []):
                        try:
                            rune_id = rune.get('id')
                            if not rune_id:
                                continue

                            rune_obj, created = Rune.objects.update_or_create(
                                id=rune_id,
                                defaults={
                                    'rune_name': rune.get('name', '')[:20],  # max_length=20
                                    'rune_value': slot_idx,  # Use slot index as value
                                    'rune_description': rune.get('shortDesc', '')[:200],  # max_length=200
                                }
                            )

                            if created:
                                created_count += 1
                            else:
                                updated_count += 1

                        except Exception as e:
                            logger.error(f"Error processing rune {rune.get('name', 'Unknown')}: {e}")
                            continue

        logger.info(f"Rune sync complete: {created_count} created, {updated_count} updated")
        return created_count, updated_count

    except requests.RequestException as e:
        logger.error(f"Error fetching runes: {e}")
        return 0, 0
    except Exception as e:
        logger.error(f"Unexpected error syncing runes: {e}")
        return 0, 0


def sync_all_static_data(version: Optional[str] = None) -> Dict[str, Tuple[int, int]]:
    """
    Sync all static data (champions, items, runes) in one call.

    Args:
        version: Specific version to fetch (defaults to latest)

    Returns:
        Dictionary with sync results for each data type

    Examples:
        >>> results = sync_all_static_data()
        >>> print(results)
        {
            'champions': (172, 0),
            'items': (398, 0),
            'runes': (60, 0)
        }
    """
    if not version:
        version = get_latest_version()

    logger.info(f"Starting full static data sync for version {version}")

    results = {
        'champions': sync_champions(version),
        'items': sync_items(version),
        'runes': sync_runes(version),
    }

    logger.info(f"Full static data sync complete for version {version}")
    return results
