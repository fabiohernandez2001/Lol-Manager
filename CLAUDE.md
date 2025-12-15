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
python manage.py runserver
```

### Database operations
```bash
# Apply migrations
python manage.py migrate

# Create migrations after model changes
python manage.py makemigrations

# Access Django shell
python manage.py shell
```

### Administrative
```bash
# Create superuser for admin panel
python manage.py createsuperuser
```

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
- Everytime we make a commit write down the whole explanation of the commit in the COMMITS.md file. But make the commit comment very concise