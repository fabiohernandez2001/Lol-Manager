# Riot API Services

This directory contains services for fetching and processing data from Riot's APIs.

## Services Overview

### 1. `riot_api_client.py`
Base client using RiotWatcher library with automatic rate limiting and error handling.

**Features:**
- Singleton LolWatcher instance
- Region mapping utilities
- Error handling helpers
- Automatic retries and backoff

### 2. `summoner_service.py`
Fetch and store summoner (player) data.

**Functions:**
- `fetch_summoner_by_riot_id(game_name, tag_line, region)` - Fetch summoner by Riot ID
- `update_summoner_rank(puuid, region)` - Update ranked stats
- `get_summoner_by_puuid(puuid)` - Get summoner from database

**Replaces:** `get_puuid()`, `get_icon_lvl()`, `get_all_ranks()` from API_Requests.py

### 3. `match_service.py`
Fetch and store match history and details.

**Functions:**
- `fetch_match_history(puuid, region, count, start, queue_type)` - Get match IDs
- `fetch_match_details(match_id, region)` - Fetch full match data
- `fetch_match_timeline(match_id, region)` - Get timeline data (optional)
- `bulk_fetch_matches(puuid, region, count, queue_type)` - Fetch multiple matches

**Replaces:** `matches_ids()`, `match_info()`, `timeline()` from API_Requests.py

### 4. `static_data_service.py`
Sync champions, items, and runes from Data Dragon.

**Functions:**
- `get_latest_version()` - Get latest patch version
- `sync_champions(version, language)` - Sync champions
- `sync_items(version, language)` - Sync items
- `sync_runes(version, language)` - Sync runes
- `sync_all_static_data(version)` - Sync everything

**Improves:** `get_champions()`, `get_items()` from views.py

## Management Commands

### Sync Static Data
```bash
# Sync all static data (champions, items, runes)
python3 manage.py sync_static_data

# Sync specific data type
python3 manage.py sync_static_data --champions-only
python3 manage.py sync_static_data --items-only
python3 manage.py sync_static_data --runes-only

# Use specific version
python3 manage.py sync_static_data --version=15.21.1
```

### Fetch Summoner
```bash
# Fetch summoner by Riot ID
python3 manage.py fetch_summoner koldi doggy --region=euw
python3 manage.py fetch_summoner "Hide on bush" KR1 --region=kr
```

### Fetch Matches
```bash
# Fetch matches by PUUID
python3 manage.py fetch_matches <puuid> --count=20 --region=euw
python3 manage.py fetch_matches <puuid> --count=50 --queue=ranked
```

## Usage Examples

### Python Code

```python
from lol_update.services import (
    fetch_summoner_by_riot_id,
    bulk_fetch_matches,
    sync_all_static_data
)

# Fetch a summoner
summoner = fetch_summoner_by_riot_id('koldi', 'doggy', 'euw')
print(f"Summoner: {summoner.username}#{summoner.tag}")
print(f"Level: {summoner.level}")
print(f"Rank: {summoner.ranked_solo_tier} {summoner.ranked_solo_rank}")

# Fetch their matches
matches = bulk_fetch_matches(
    puuid=summoner.puuid,
    region='euw',
    count=20
)
print(f"Fetched {len(matches)} matches")

# Sync static data
results = sync_all_static_data()
print(f"Champions: {results['champions']}")
print(f"Items: {results['items']}")
print(f"Runes: {results['runes']}")
```

## Configuration

### Environment Variables

Add to `.env` file:
```
RIOT_API_KEY=RGAPI-your-api-key-here
```

### Supported Regions

Platform regions:
- `na` - North America (na1)
- `euw` - Europe West (euw1)
- `eune` - Europe Nordic & East (eun1)
- `kr` - Korea
- `br` - Brazil (br1)
- `lan` - Latin America North (la1)
- `las` - Latin America South (la2)
- `oce` - Oceania (oc1)
- `tr` - Turkey (tr1)
- `ru` - Russia
- `jp` - Japan (jp1)
- `ph` - Philippines (ph2)
- `sg` - Singapore (sg2)
- `th` - Thailand (th2)
- `tw` - Taiwan (tw2)
- `vn` - Vietnam (vn2)

## Error Handling

All services include:
- ✅ Automatic retry on rate limits (via RiotWatcher)
- ✅ Detailed error logging
- ✅ Graceful degradation on failures
- ✅ Input validation

## Rate Limiting

RiotWatcher automatically handles Riot's rate limits:
- Respects both application and method rate limits
- Automatically retries with exponential backoff
- No manual rate limit handling needed

## Future Improvements

- [ ] Add Celery tasks for async processing
- [ ] Implement match timeline parsing for advanced stats
- [ ] Add progress bars for bulk operations
- [ ] Cache frequently accessed data
- [ ] Add webhook support for live game tracking
