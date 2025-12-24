import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from lol_navo.models import Champion, Item

from .services.summoner_service import fetch_summoner_by_riot_id, update_summoner_rank
from .services.match_service import fetch_match_history, fetch_match_details
from .services.static_data_service import sync_champions, sync_items, sync_runes


# ===========================
# Service Trigger Endpoints (New REST API)
# ===========================

class FetchSummonerView(APIView):
    """
    POST /lol_update/api/fetch-summoner/

    Fetch and store a summoner's data from Riot API.

    Body:
    {
        "game_name": "Faker",
        "tag_line": "KR1",
        "region": "kr"
    }
    """
    def post(self, request):
        game_name = request.data.get('game_name')
        tag_line = request.data.get('tag_line')
        region = request.data.get('region', 'euw')

        if not game_name or not tag_line:
            return Response(
                {'error': 'game_name and tag_line are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        summoner = fetch_summoner_by_riot_id(game_name, tag_line, region)

        if summoner:
            return Response({
                'message': 'Summoner fetched successfully',
                'summoner': {
                    'puuid': summoner.puuid,
                    'username': summoner.username,
                    'tag': summoner.tag,
                    'server': summoner.server,
                    'ranked_solo_rank': summoner.ranked_solo_rank,
                    'ranked_flex_rank': summoner.ranked_flex_rank,
                }
            }, status=status.HTTP_200_OK)
        else:
            return Response(
                {'error': 'Failed to fetch summoner'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class FetchMatchesView(APIView):
    """
    POST /lol_update/api/fetch-matches/

    Fetch and store match history for a summoner.

    Body:
    {
        "puuid": "summoner-puuid-here",
        "count": 20,
        "region": "euw",
        "queue_type": 420  // optional
    }
    """
    def post(self, request):
        puuid = request.data.get('puuid')
        count = request.data.get('count', 20)
        region = request.data.get('region', 'euw')
        queue_type = request.data.get('queue_type')

        if not puuid:
            return Response(
                {'error': 'puuid is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        match_ids = fetch_match_history(
            puuid=puuid,
            region=region,
            count=int(count),
            queue_type=queue_type
        )

        if match_ids is None:
            return Response(
                {'error': 'Failed to fetch match history'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Fetch details for each match
        fetched_matches = []
        failed_matches = []

        for match_id in match_ids:
            match = fetch_match_details(match_id, region)
            if match:
                fetched_matches.append(match_id)
            else:
                failed_matches.append(match_id)

        return Response({
            'message': f'Fetched {len(fetched_matches)} matches',
            'fetched_count': len(fetched_matches),
            'failed_count': len(failed_matches),
            'fetched_matches': fetched_matches,
            'failed_matches': failed_matches,
        }, status=status.HTTP_200_OK)


class SyncStaticDataView(APIView):
    """
    POST /lol_update/api/sync-static-data/

    Sync champions, items, and/or runes from Data Dragon.

    Body:
    {
        "data_types": ["champions", "items", "runes"],  // optional, defaults to all
        "patch": "14.23",  // optional, defaults to latest
        "language": "en_US"  // optional, defaults to en_US
    }
    """
    def post(self, request):
        data_types = request.data.get('data_types', ['champions', 'items', 'runes'])
        patch = request.data.get('patch')
        language = request.data.get('language', 'en_US')

        results = {}

        if 'champions' in data_types:
            champ_result = sync_champions(patch_version=patch, language=language)
            results['champions'] = {
                'created': champ_result[0],
                'updated': champ_result[1]
            }

        if 'items' in data_types:
            item_result = sync_items(patch_version=patch, language=language)
            results['items'] = {
                'created': item_result[0],
                'updated': item_result[1]
            }

        if 'runes' in data_types:
            rune_result = sync_runes(patch_version=patch, language=language)
            results['runes'] = {
                'created': rune_result[0],
                'updated': rune_result[1]
            }

        return Response({
            'message': 'Static data sync completed',
            'results': results
        }, status=status.HTTP_200_OK)


class UpdateSummonerRankView(APIView):
    """
    POST /lol_update/api/update-rank/

    Update a summoner's ranked stats.

    Body:
    {
        "puuid": "summoner-puuid-here",
        "region": "euw"
    }
    """
    def post(self, request):
        puuid = request.data.get('puuid')
        region = request.data.get('region', 'euw')

        if not puuid:
            return Response(
                {'error': 'puuid is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        summoner = update_summoner_rank(puuid, region)

        if summoner:
            return Response({
                'message': 'Rank updated successfully',
                'summoner': {
                    'puuid': summoner.puuid,
                    'username': summoner.username,
                    'ranked_solo_rank': summoner.ranked_solo_rank,
                    'ranked_flex_rank': summoner.ranked_flex_rank,
                }
            }, status=status.HTTP_200_OK)
        else:
            return Response(
                {'error': 'Failed to update rank'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ===========================
# Legacy Endpoints (Keep for backward compatibility)
# ===========================
def get_champions(request):
    version_url = "https://ddragon.leagueoflegends.com/api/versions.json"
    version = requests.get(version_url).json()[0]
    champion_url = f"https://ddragon.leagueoflegends.com/cdn/{version}/data/es_ES/champion.json"
    champions = requests.get(champion_url).json()
    for champion in champions["data"].values():
        Champion.objects.update_or_create (id = champion["key"],
                                icon = f'https://ddragon.leagueoflegends.com/cdn/15.21.1/img/champion/{champion["image"]["full"]}',
                                name = f'{champion["name"]}',
                                tags = champion["tags"],
                                title = champion["title"],
                                description = f'{champion["blurb"]}',
                                attack = champion["info"]["attack"],
                                defense = champion["info"]["defense"],
                                magic = champion["info"]["magic"],
                                difficulty = champion["info"]["difficulty"],
                                partype = champion["partype"],
                                hp = champion["stats"]["hp"],
                                hp_per_level = champion["stats"]["hpperlevel"],
                                mp = champion["stats"]["mp"],
                                mp_per_level = champion["stats"]["mpperlevel"],
                                move_speed = champion["stats"]["movespeed"],
                                armor = champion["stats"]["armor"],
                                armor_per_level = champion["stats"]["armorperlevel"],
                                spell_block = champion["stats"]["spellblock"],
                                spell_block_per_level = champion["stats"]["spellblockperlevel"],
                                attack_range = champion["stats"]["attackrange"],
                                hp_regen = champion["stats"]["hpregen"],
                                hp_regen_per_level = champion["stats"]["hpregenperlevel"],
                                crit = champion["stats"]["crit"],
                                crit_per_level = champion["stats"]["critperlevel"],
                                attack_damage = champion["stats"]["attackdamage"],
                                attack_damage_per_level = champion["stats"]["attackdamageperlevel"],
                                attack_speed = champion["stats"]["attackspeed"],
                                attack_speed_per_level = champion["stats"]["attackspeedperlevel"],
                                )
def get_items(request):
    version_url = "https://ddragon.leagueoflegends.com/api/versions.json"
    version = requests.get(version_url).json()[0]
    url = f"https://ddragon.leagueoflegends.com/cdn/{version}/data/en_US/item.json"
    items = requests.get(url).json()
    for key, item in items["data"].items():
        # print(key, item["name"])

        # Extract nested gold and image data with null checks
        gold_data = item.get("gold", {})
        image_data = item.get("image", {})

        Item.objects.update_or_create(
            id = key,
            defaults={
                "name": item.get("name", ""),
                "plaintext": item.get("plaintext", ""),
                "description": item.get("description", ""),
                "colloq": item.get("colloq", ""),
                "stacks": item.get("stacks"),
                "depth": item.get("depth"),
                "consumed": item.get("consumed"),
                "consume_on_full": item.get("consume_on_full"),
                "in_store": item.get("in_store", True),
                "hide_from_all": item.get("hide_from_all", False),
                "required_champion": item.get("required_champion", ""),
                "required_ally": item.get("required_ally", ""),
                "special_recipe": item.get("special_recipe"),
                "required_buff_currency_name": item.get("requiredBuffCurrencyName", ""),
                "required_buff_currency_cost": item.get("requiredBuffCurrencyCost"),
                "base_gold": gold_data.get("base", 0),
                "purchasable": gold_data.get("purchasable", False),
                "total_gold": gold_data.get("total", 0),
                "sell_gold": gold_data.get("sell", 0),
                "image": f"https://ddragon.leagueoflegends.com/cdn/{version}/img/item/{image_data.get('full', '')}" if image_data.get("full") else "",
                "stats": item.get("stats", {}),
                "effect": item.get("effect", {}),
                "builds_into": item.get("into", []),
                "builds_from": item.get("from", []),
                "tags": item.get("tags", []),
                "maps": item.get("maps", {}),
            }
        )



# def upsert_item(item_id_str: str, raw: Dict[str, Any], version: str) -> Tuple[Item, bool]:
#     """Crea/actualiza un Item a partir del JSON crudo."""
#     try:
#         item_id = int(item_id_str)
#     except ValueError:
        # A veces hay claves no numéricas, las ignoramos
#         raise CommandError(f"Item id no numérico: {item_id_str}")

#     values = map_item_fields(raw, item_id, version)
#     obj, created = Item.objects.update_or_create(
#         id=item_id,
#         defaults=values,
#     )
#     return obj, created


