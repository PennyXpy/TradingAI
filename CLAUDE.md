# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

TradingAI is a full-stack financial analysis application with a FastAPI backend and Next.js frontend, providing real-time market data, portfolio management, and AI-powered insights with Polygon.io integration.

## Architecture

### Backend Structure
- **FastAPI application** (`backend/main.py`) with CORS enabled for localhost:3000 and localhost:5173
- **Modular routing**: Auth (`/auth`), portfolio (`/portfolio`), stocks, news, and WebSocket routes
- **SQLModel/SQLAlchemy** for database operations with SQLite (`tradingai.db`)
- **User authentication** via fastapi-users with bcrypt password hashing
- **Real-time data**: Polygon.io WebSocket and REST API integration with rate limiting
- **Services**:
  - `polygon_rest_service.py` - REST API calls with rate limiting
  - `polygon_websocket_service.py` - WebSocket real-time data streaming
  - `realtime_data_manager.py` - WebSocket connection management
  - `user_portfolio.py` - Portfolio analytics and statistics
  - `redis_cache.py` - Caching layer (falls back to in-memory)

### Frontend Structure
- **Next.js 15** with TypeScript and Tailwind CSS
- **Key pages**: `/` (landing), `/main` (public market data), `/portfolio` (analytics), `/[username]/dashboard`
- **Real-time hooks**: Custom hooks for API data fetching with auto-refresh
- **Components**:
  - `PortfolioOverview` - Statistics cards and performance metrics
  - `FollowedStocksList` - Interactive stock list with sorting/filtering
  - `PortfolioAnalytics` - Multi-tab analytics dashboard
  - `Header` - Navigation with portfolio routing

### Database Models
- Users, UserFollowing (followed stocks), authentication tokens
- SQLite database with SQLModel ORM

## Development Commands

### Backend
```bash
# IMPORTANT: Always activate virtual environment first
cd /path/to/TradingAI && source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run development server (from backend directory)
cd backend && uvicorn main:app --reload
```

### Frontend
```bash
# Install dependencies (from frontend directory)
cd frontend && npm install

# Run development server
npm run dev

# Build for production
npm run build

# Lint code
npm run lint
```

## Key Configuration

- Backend runs on port 8000 by default
- Frontend runs on port 3000
- **Environment variables needed**:
  - `POLYGON_API_KEY` - For real-time stock data (optional, falls back to mock data)
  - `OPENROUTER_API_KEY` - For AI features (optional)
- Database: SQLite file at `backend/models/tradingai.db`

## Important Notes

- **Rate Limiting**: Polygon API calls are rate-limited (5 requests/second) to avoid 429 errors
- **Fallback Strategy**: Application gracefully falls back to mock data when APIs are unavailable
- **WebSocket Management**: Connection loops are limited to prevent infinite reconnection attempts
- **Virtual Environment**: Always use `source venv/bin/activate` before running backend commands
- **Portfolio Features**: Comprehensive analytics without buy/sell functionality (tracking only)

## Key Integrations

- **Polygon.io**: Real-time and historical stock data with WebSocket streaming
- **Portfolio Analytics**: Sector breakdown, risk assessment, diversification scoring
- **Real-time Updates**: Live price updates via WebSocket connections
- **Caching**: Redis-based caching with in-memory fallback