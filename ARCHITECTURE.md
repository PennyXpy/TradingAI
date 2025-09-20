# TradingAI Application Architecture

## System Overview

TradingAI is a modern full-stack financial application built with FastAPI backend and Next.js frontend, featuring real-time market data integration via Polygon.io APIs.

## Architecture Diagram

```
Frontend (Next.js)     Backend (FastAPI)      External APIs
     │                       │                     │
     ├─ Landing Page          ├─ Auth Routes        ├─ Polygon.io REST
     ├─ Main Market Page      ├─ Stock Routes       ├─ Polygon.io WebSocket
     ├─ Portfolio Dashboard   ├─ Portfolio Routes   └─ OpenRouter AI
     └─ User Dashboard        ├─ News Routes
                             ├─ WebSocket Manager
                             └─ Database (SQLite)
```

## Backend Architecture

### Core Services

1. **Real-time Data Layer**
   - `polygon_rest_service.py` - REST API integration with rate limiting
   - `polygon_websocket_service.py` - WebSocket streaming for live data
   - `realtime_data_manager.py` - Connection management and data distribution

2. **Portfolio Management**
   - `user_portfolio.py` - Portfolio analytics, statistics, and tracking
   - Sector analysis, risk assessment, diversification scoring
   - Public endpoints for testing without authentication

3. **Caching & Performance**
   - `redis_cache.py` - Redis caching with in-memory fallback
   - Rate limiting to prevent API quota exhaustion
   - Graceful degradation to mock data when APIs unavailable

4. **Authentication & Users**
   - fastapi-users integration with JWT tokens
   - SQLModel/SQLAlchemy for user management
   - Bcrypt password hashing

### Data Flow

```
External APIs → Rate Limiting → Caching → Business Logic → WebSocket/HTTP → Frontend
                                   ↓
                              Database (User Data)
```

### Key Design Patterns

- **Service Layer Pattern**: Separate services for different data sources
- **Repository Pattern**: Database operations abstracted through SQLModel
- **Observer Pattern**: WebSocket connections for real-time updates
- **Fallback Strategy**: Graceful degradation when external services fail

## Frontend Architecture

### Page Structure

```
/                    - Landing page with auth
/main               - Public market data (stocks, news)
/portfolio          - Portfolio analytics dashboard
/[username]/dashboard - User-specific dashboard
```

### Component Hierarchy

```
App
├── Header (navigation)
├── Pages
│   ├── LandingPage
│   ├── MainMarketPage
│   │   ├── StocksList (with real-time data)
│   │   └── NewsList
│   ├── PortfolioPage
│   │   ├── PortfolioOverview (stats cards)
│   │   ├── FollowedStocksList (interactive table)
│   │   └── PortfolioAnalytics (multi-tab dashboard)
│   └── UserDashboard
└── Real-time Hooks (useApiData, useRealtimeData)
```

### State Management

- **Custom Hooks**: `useApiData` for HTTP requests with auto-refresh
- **Real-time Updates**: WebSocket integration for live price updates
- **Local State**: React hooks for component-level state
- **Caching**: Built-in request caching with TTL

## Technology Stack

### Backend
- **Framework**: FastAPI 0.104+
- **Database**: SQLite with SQLModel ORM
- **Authentication**: fastapi-users with JWT
- **WebSockets**: Native FastAPI WebSocket support
- **Caching**: Redis (optional) + in-memory fallback
- **HTTP Client**: httpx for external API calls

### Frontend
- **Framework**: Next.js 15 with TypeScript
- **Styling**: Tailwind CSS
- **HTTP Client**: Fetch API with custom hooks
- **WebSockets**: Native WebSocket API
- **Build Tools**: Next.js built-in tooling

### External Integrations
- **Polygon.io**: Real-time and historical market data
- **OpenRouter**: AI-powered insights (optional)

## Security Considerations

- JWT token-based authentication
- CORS configuration for specific origins
- Rate limiting on external API calls
- Input validation and sanitization
- No sensitive data in frontend code

## Performance Optimizations

- Request caching with TTL
- Connection pooling for database
- Rate limiting to prevent API abuse
- Lazy loading of components
- WebSocket connection management
- Graceful fallback mechanisms

## Scalability Design

- Modular service architecture
- Stateless backend design
- Caching layer for reduced API calls
- Database connection pooling
- Horizontal scaling ready (stateless services)