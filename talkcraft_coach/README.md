# TalkCraft Phase 4 — Advanced Communication Intelligence + Personalized Coaching

## Overview

TalkCraft Phase 4 transforms the platform into a fully-featured AI communication coaching system with personalized analytics, adaptive learning, and long-term progress tracking.

## Features

### 1. User Authentication
- Secure registration and login
- JWT-based sessions
- User profiles with skill level tracking

### 2. Session History & Analytics
- Complete session recording
- Per-session deep analysis
- Weakness and strength detection
- Session replay analytics

### 3. Progress Analytics
- Long-term metric tracking
- Trend analysis (30+ metrics)
- Weekly summaries
- Grammar improvement tracking
- Streak tracking (practice consistency)

### 4. Personalized Improvement Plans
- Auto-generated based on weaknesses
- Targeted exercises for each area
- Difficulty-adapted recommendations
- Progress tracking per plan

### 5. Adaptive AI Coaching
- Dynamic difficulty adjustment (Beginner/Intermediate/Advanced)
- Weakness-aware conversation adaptation
- Personalized coaching style
- Context-aware mode recommendations

### 6. Achievement System
- 25+ badges across 8 categories
- Automatic detection and awarding
- Progress tracking per badge
- Category-based organization

### 7. Daily Practice Recommendations
- AI-generated daily exercises
- Weakness-targeted practice
- Completion tracking
- Difficulty-appropriate suggestions

### 8. Learning Paths
- 5 structured learning paths
- Beginner to Advanced progression
- Topic-based organization
- Focus area alignment

## Architecture

```
talkcraft_coach/
├── __init__.py          # Module definition
├── main.py              # CLI entry point
├── server.py            # FastAPI server + WebSocket
├── requirements.txt     # Dependencies
├── README.md            # This file
├── config.json          # Server configuration
├── database/
│   ├── models.py        # SQLAlchemy models
│   ├── database.py      # DB engine + session
├── auth/
│   ├── auth_handler.py  # JWT + password hashing
├── analytics/
│   ├── progress_analyzer.py  # Long-term progress
│   ├── trend_analyzer.py     # Trend computation
│   ├── weakness_detector.py  # Weakness detection
│   ├── session_analyzer.py   # Per-session analysis
├── coaching/
│   ├── adaptive_coach.py     # Difficulty adaptation
│   ├── improvement_planner.py # Improvement plans
│   ├── practice_recommender.py # Daily recommendations
│   ├── topic_paths.py        # Learning paths
├── gamification/
│   ├── achievement_system.py # Achievement engine
│   ├── badges.py             # Badge definitions
├── api/
│   ├── auth_routes.py        # Auth endpoints
│   ├── analytics_routes.py   # Analytics endpoints
│   ├── coaching_routes.py    # Coaching endpoints
│   ├── achievement_routes.py # Achievement endpoints
│   ├── dashboard_routes.py   # Dashboard aggregation
│   ├── session_routes.py     # Session management
├── dashboard/
│   ├── app.py                # Streamlit dashboard
└── utils/
    ├── config.py             # Configuration
    └── logger.py             # Logging setup
```

## Quick Start

### Installation

```bash
cd talkcraft_coach
pip install -r requirements.txt
```

### Initialize Database

```bash
python main.py --init-db
```

### Run Server

```bash
python main.py --mode server
```

Server starts on `http://0.0.0.0:8004`

### Run Dashboard (Streamlit)

```bash
python main.py --mode dashboard
```

### Configuration

Edit `config.json` in the `talkcraft_coach` directory:

```json
{
  "server": {
    "host": "0.0.0.0",
    "port": 8004
  },
  "auth": {
    "secret_key": "change-this-to-a-secure-random-key"
  },
  "database": {
    "url": "sqlite:///./talkcraft_coach.db"
  }
}
```

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login
- `GET /api/auth/me` - Get current user
- `POST /api/auth/refresh` - Refresh token

### Analytics
- `GET /api/analytics/summary` - User progress summary
- `GET /api/analytics/weekly` - Weekly summary
- `GET /api/analytics/weekly-progress` - Weekly progress chart data
- `GET /api/analytics/trends` - All metric trends
- `GET /api/analytics/trends/{metric}` - Specific metric history
- `GET /api/analytics/weaknesses` - Detected weaknesses
- `GET /api/analytics/grammar` - Grammar improvement
- `GET /api/analytics/sessions` - Session history
- `GET /api/analytics/sessions/{id}` - Session detail

### Coaching
- `GET /api/coaching/difficulty` - Adaptive difficulty
- `GET /api/coaching/focus` - Coaching focus areas
- `GET /api/coaching/parameters` - Conversation parameters
- `GET /api/coaching/plan` - Improvement plan
- `POST /api/coaching/plan/generate` - Regenerate plan
- `POST /api/coaching/plan/{id}/complete` - Complete plan
- `GET /api/coaching/recommendations` - Daily recommendations
- `POST /api/coaching/recommendations/generate` - Generate new
- `GET /api/coaching/paths` - Learning paths
- `GET /api/coaching/paths/{id}` - Path details

### Achievements
- `GET /api/achievements` - All achievements
- `POST /api/achievements/check` - Check for new ones

### Dashboard
- `GET /api/dashboard/overview` - Full dashboard data

### Sessions
- `POST /api/sessions/create` - Save session data
- `GET /api/sessions/{id}` - Session details

## Integration with Other TalkCraft Servers

The coaching server integrates with:
- **Phase 1** (port 8000): Speech analysis data
- **Phase 2** (port 8765): Vision analysis data
- **Phase 3** (port 8002): AI conversation data

Session data flows from these servers to the coaching server via the `/api/sync/session` endpoint for persistence and analysis.

## Performance

Designed for CPU-efficient operation:
- SQLite with WAL mode for concurrent reads
- Lightweight analytics algorithms
- No GPU dependencies
- Minimal memory footprint
- Async FastAPI for concurrent requests
