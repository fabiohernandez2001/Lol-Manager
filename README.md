# Lol-Manager

A comprehensive League of Legends performance tracking and analytics platform that helps players analyze their gameplay, discover optimal builds, and improve their competitive edge.

## Project Overview

Lol-Manager provides in-depth statistics and insights for League of Legends players by aggregating match data, champion performance metrics, and item builds. The platform processes match history to deliver actionable insights about player performance, champion mastery, and meta trends across different patches and game modes.

**Key Features:**
- **Player Profiles**: Track your match history, win rates, KDA ratios, and champion performance across ranked, normal, and ARAM game modes
- **Champion Analytics**: Detailed statistics for each champion including win rates, pick rates, and performance by role and patch
- **Build Recommendations**: Data-driven item builds based on actual match outcomes and situational contexts
- **Match Analysis**: Comprehensive match breakdowns with detailed statistics on CS, damage, vision, and objective control
- **Meta Insights**: Track patch-based trends to understand the current meta and champion viability

## Technology Stack

**Backend:**
- **Django 5.2** - Web framework and REST API layer
- **Django REST Framework 3.16** - API endpoints and serialization
- **PostgreSQL (Supabase)** - Primary database for storing player data, matches, and statistics
- **Riot Games API** - Official data source for champion, item, and match information

**Frontend:**
- **React** - Modern UI framework for responsive, interactive user experience

**Data Pipeline:**
- Automated data ingestion from Riot's Data Dragon and Match API
- Intelligent caching and rate limit handling
- Precomputed aggregations for fast query performance

## Getting Started

### Prerequisites
- Python 3.12+
- PostgreSQL database
- Riot Games API key

### Installation

1. Clone the repository
```bash
git clone https://github.com/yourusername/Lol-Manager.git
cd Lol-Manager
```

2. Install dependencies
```bash
pip install -r requirements.txt
```

3. Configure database settings in `ChallengerBrain/settings.py`

4. Run migrations
```bash
python manage.py migrate
```

5. Fetch initial data from Riot API
```bash
# Fetch champion data
curl http://localhost:8000/lol_update/champions

# Fetch item data
curl http://localhost:8000/lol_update/items
```

6. Start the development server
```bash
python manage.py runserver
```

## API Endpoints

### Data Update Endpoints
- `GET /lol_update/champions` - Fetch and update champion data from Riot API
- `GET /lol_update/items` - Fetch and update item data from Riot API

### Data Access Endpoints
- `GET /lol_navo/champions/` - List all champions with filtering support
- `GET /lol_navo/champions/?name=<name>` - Search champions by name

## License

This project is licensed under the MIT License.

---

*Lol-Manager isn't endorsed by Riot Games and doesn't reflect the views or opinions of Riot Games or anyone officially involved in producing or managing Riot Games properties. Riot Games, and all associated properties are trademarks or registered trademarks of Riot Games, Inc.*
