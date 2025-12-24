# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Lol-Manager is a Django REST Framework API for League of Legends data management. The project fetches and stores champion, item, summoner, and match data from Riot's Data Dragon API.

**Project name**: ChallengerBrain (Django project)
**Main apps**:
- `lol_navo`: Read-only API endpoints for champions and summoners
- `lol_update`: Data update endpoints that fetch from Riot Data Dragon API
- `faker_AI`: (Appears to be a placeholder app with minimal implementation)

## Development Commands

### Running the server
```bash
python3 manage.py runserver
```

### Database operations
```bash
# Apply migrations
python3 manage.py migrate

# Create migrations after model changes
python3 manage.py makemigrations

# Access Django shell
python3 manage.py shell
```

### Administrative
```bash
# Create superuser for admin panel
python3 manage.py createsuperuser
```

## Celery Task Queue

The project uses Celery for asynchronous task processing and periodic tasks.

### Running Celery Services

You need to run these in separate terminals:

**Terminal 1 - Celery Worker:**
```bash
celery -A ChallengerBrain worker --loglevel=info
```

**Terminal 2 - Celery Beat (periodic tasks):**
```bash
celery -A ChallengerBrain beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

**Terminal 3 - Flower (monitoring dashboard):**
```bash
celery -A ChallengerBrain flower --port=5555
# Access at: http://localhost:5555
```

**Terminal 4 - Django Development Server:**
```bash
python3 manage.py runserver
```

### Available Tasks

**High Priority (User-facing):**
- `fetch_summoner_task(game_name, tag_line, region)` - Fetch summoner by Riot ID (2-5s)
- `bulk_fetch_matches_task(puuid, region, count)` - Fetch multiple matches (30-120s)
- `fetch_match_details_task(match_id, region)` - Fetch single match (2-8s)

**Medium Priority (Periodic):**
- `sync_champions_task(version)` - Sync champions from Data Dragon (15-30s)
- `sync_items_task(version)` - Sync items from Data Dragon (20-40s)
- `sync_runes_task(version)` - Sync runes from Data Dragon (5-15s)
- `sync_all_static_data_task(version, force)` - Sync all static data with smart version checking
  - **Smart sync**: Only syncs if new Data Dragon version detected
  - **Schedule**: Checks every 6 hours for new versions
  - **Version tracking**: Stores last synced version in database
  - **Duration**: 40-90s when sync needed, <1s when skipped

**Low Priority (Batch):**
- `update_tracked_summoners_ranks_task(batch_size)` - Update ranks for tracked summoners (2-10min, runs hourly)
- `update_summoner_rank_task(puuid, region)` - Update single summoner rank (1-3s)

### Triggering Tasks Manually

You can trigger tasks in Django shell:

```python
# Start Django shell
python3 manage.py shell

# Import tasks
from lol_update.tasks import fetch_summoner_task, sync_all_static_data_task

# Trigger async task
result = fetch_summoner_task.delay('koldi', 'doggy', 'euw')

# Check status
print(result.status)  # 'PENDING', 'STARTED', 'SUCCESS', 'FAILURE'

# Get result (blocks until complete)
puuid = result.get(timeout=10)

# Trigger static data sync (only syncs if new version detected)
result = sync_all_static_data_task.delay()
print(result.get(timeout=180))

# Force sync even if version hasn't changed (rare)
result = sync_all_static_data_task.delay(force=True)
print(result.get(timeout=180))
```

### Periodic Tasks

Two periodic tasks are pre-configured:

1. **Static Data Version Check** - Runs every 6 hours
   - Task: `sync_all_static_data_task`
   - **Smart behavior**: Only syncs champions/items/runes if new Data Dragon version detected
   - **Efficiency**: Reduces unnecessary syncs by ~93% (365/year → ~26/year)
   - Data Dragon versions only change when Riot releases patches (~every 2 weeks)
   - Version tracking stored in `DataDragonVersion` model

2. **Hourly Rank Updates** - Runs every 1 hour
   - Task: `update_tracked_summoners_ranks_task`
   - Updates ranks for summoners with matches (batch of 50)

You can manage periodic tasks in Django Admin at `/admin/django_celery_beat/`

### Production Setup (Upstash Redis)

For production deployment with Upstash (managed Redis):

1. Create account at https://upstash.com
2. Create Redis database
3. Update `.env`:
   ```bash
   CELERY_BROKER_URL=rediss://default:PASSWORD@endpoint.upstash.io:6379
   CELERY_RESULT_BACKEND=rediss://default:PASSWORD@endpoint.upstash.io:6379
   ```

### Monitoring

- **Flower Dashboard**: http://localhost:5555 - Real-time task monitoring
- **Django Admin**: http://localhost:8000/admin/django_celery_results/ - Task execution history

## Dependencies

Install required packages:
```bash
pip install -r requirements.txt
```

Key dependencies:
- Django 5.2.7
- Django REST Framework 3.16.1
- django-cors-headers 4.9.0
- requests 2.32.5
- psycopg2-binary 2.9.11 (PostgreSQL support, though currently using SQLite)

## Architecture

### Data Flow

1. **Data Update Flow** (`lol_update`):
   - `/lol_update/champions` - Fetches champion data from Data Dragon API and updates database
   - `/lol_update/items` - Fetches item data from Data Dragon API and updates database
   - Both endpoints automatically fetch the latest version from Riot's API

2. **Data Access Flow** (`lol_navo`):
   - `/lol_navo/champions/` - REST API for browsing champions (supports `?name=` query parameter)
   - `/lol_navo/champions/get_name/` - Custom action to search champions by name
   - Uses Django REST Framework's ViewSet pattern with read-only access

### Database Models

All models are in `lol_navo/models.py`:

- **Champion**: Complete champion data including stats, base attributes, and per-level scaling
- **Summoner**: Player profiles with ranked stats across different game modes
- **Item**: Full item data including gold costs, stats, build paths, and metadata
- **Match**: Match records with duration, winner, and game metadata
- **Rune**: Rune configurations
- **MatchSummoners**: Junction table linking summoners to matches with performance data (items, CS, KDA, etc.)
- **ChampionStat**: Junction table tracking summoner performance on specific champions

### Key Relationships

- Champions and Summoners have many-to-many relationship through `ChampionStat`
- Matches and Summoners have many-to-many relationship through `MatchSummoners`
- Items are stored with JSONField for build paths (`builds_into`, `builds_from`), stats, and maps

### API Patterns

The project uses two distinct API patterns:

1. **lol_navo**: Standard DRF ViewSets with routers for CRUD operations (read-only)
2. **lol_update**: Function-based views for data synchronization with external API

### CORS Configuration

CORS is enabled for all origins (`CORS_ORIGIN_ALLOW_ALL = True`). This is suitable for development but should be restricted in production.

## Data Source

Champions and items are fetched from Riot Games Data Dragon:
- Version endpoint: `https://ddragon.leagueoflegends.com/api/versions.json`
- Champion data: `https://ddragon.leagueoflegends.com/cdn/{version}/data/es_ES/champion.json`
- Item data: `https://ddragon.leagueoflegends.com/cdn/{version}/data/en_US/item.json`

Note: Champion data uses Spanish (`es_ES`) while item data uses English (`en_US`).

## Known Issues

1. **Item model** has duplicate `description` field (line 108 and 111 in models.py)
2. **Champion model** `__str__` method references `self.name` but model uses `name` field
3. **Item model** `__str__` method references `self.item_name` but model uses `name` field
4. **lol_update views** may have issues with null values when extracting from Item data (noted in git commit history)
5. **SummonerViewSet** has inconsistent method implementations (line 53 uses wrong serializer)
- Don't make references to yourself in the commit comments
- # Project Context (Read First)

We are building a stats and recommendation web app for League of Legends, similar to OP.GG / U.GG.

Tech stack:
- Frontend: **React**
- Backend: **Django** (REST API layer + business logic)
- Database: **PostgreSQL**

What the app does:
1) **Riot API ingestion**
   - Fetch and store data about summoners/players, match history, match details, champions, items, ranks, etc.
   - Respect Riot routing (platform vs regional), handle 429 rate limits, retries/backoff, and timeouts.

2) **User-facing features**
   - Player profile pages:
     - Recent matches, champions played, W/L, winrate, KDA, role/lane, items, runes, and match summaries.
     - Optional: filters by queue type, patch, champion, timeframe.
   - Champion and item pages:
     - Champion performance by patch/role (winrate/pickrate/banrate), recommended builds, counters and matchup stats.
     - Item performance and synergies (what items work best with which champs/roles).
   - Statistics/meta pages:
     - Patch-based meta trends, best builds by situation, counters, matchup winrate deltas, sample sizes, etc.

3) **Data processing approach**
   - Store raw match payloads (JSON) for reliability and future recomputation.
   - Compute aggregated tables (materialized or precomputed) for fast UI:
     - champion_stats_by_patch_role
     - build_stats_by_champion_patch_role
     - matchup/counter_stats
   - Always include sample size and patch context, so results are trustworthy.

Core principles:
- **Reliability**: accurate stats, transparent assumptions, patch-awareness, and strong error handling.
- **Performance**: caching and precomputed aggregates for fast responses.
- **Maintainability**: clean architecture, clear logging, and tests for key logic.
- **Avoid misleading output**: do not invent stats; if data is missing, show “not enough data”.

Future addition (AI assistant):
- Provide recommendations and explanations grounded in our stored aggregated stats (RAG-like behavior).
- Must not hallucinate; must reference patch and available data.

Please keep code changes consistent with existing patterns and focus on clean, production-minded implementation.

## Commit Documentation Workflow

Every time we make a commit:
1. Create a detailed explanation file in `.commits/` directory
2. File naming format: `YYYY-MM-DD-concise-description.md` (e.g., `2025-12-17-complete-database-schema.md`)
3. File structure should include:
   - Title and date
   - Commit hash (if available)
   - Changes made (detailed breakdown)
   - Why the changes matter
   - Testing/verification results
   - Database/architecture impact (if applicable)
4. Keep the actual git commit message concise but informative
5. The `.commits/` directory is gitignored - these are local documentation files

## Daily Closure Workflow

After calling the daily-closer agent:
1. **Update ROADMAP.md** with recent progress:
   - Mark completed tasks with [x] and completion dates
   - Update "Recent Progress" section at the bottom
   - Update completion percentage if major phase completed
2. **Keep README.md static** - do not update with current status
3. This ensures the next Claude instance has clear context about:
   - What was accomplished today
   - Current project state
   - What to work on next
- make commits ONLY when I eplicitly ask you