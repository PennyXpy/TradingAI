# TradingAI Database & Caching System

## Database Architecture

### Primary Database: SQLite
- **Location**: `backend/models/tradingai.db`
- **ORM**: SQLModel (built on SQLAlchemy)
- **Purpose**: User data, authentication, portfolio tracking

### Database Models

#### User Model
```python
class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    email: str = Field(index=True, unique=True)
    hashed_password: str
    is_active: bool = Field(default=True)
    is_superuser: bool = Field(default=False)
    is_verified: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

#### UserFollowing Model (Portfolio Tracking)
```python
class UserFollowing(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    symbol: str = Field(index=True)
    asset_type: str = Field(default="stock")  # stock, crypto, etf
    name: Optional[str] = None
    notes: Optional[str] = None
    followed_at: datetime = Field(default_factory=datetime.utcnow)
```

### Database Operations

#### Connection Management
```python
# backend/data.py
from sqlmodel import create_engine, Session

# SQLite database with WAL mode for better concurrency
database_url = "sqlite:///./models/tradingai.db"
engine = create_engine(database_url, echo=False)

def get_db():
    with Session(engine) as session:
        yield session
```

#### Example Queries
```python
# Get user's followed stocks
followed_stocks = db.exec(
    select(UserFollowing).where(
        UserFollowing.user_id == user.id,
        UserFollowing.asset_type == "stock"
    )
).all()

# Add new followed stock
new_follow = UserFollowing(
    user_id=user.id,
    symbol="AAPL",
    asset_type="stock",
    name="Apple Inc."
)
db.add(new_follow)
db.commit()
```

## Caching System

### Redis Cache (Primary)
- **Implementation**: `backend/services/redis_cache.py`
- **Fallback**: In-memory cache when Redis unavailable
- **Purpose**: API response caching, rate limiting, session storage

### Cache Configuration
```python
# Redis settings (optional)
REDIS_URL = "redis://localhost:6379"
DEFAULT_TTL = 60  # seconds

# Cache keys structure
"stock_details:AAPL"     # Stock information
"top_stocks:10"          # Top stocks with limit
"portfolio_analytics:user_123"  # User portfolio data
"market_indexes"         # Market index data
```

### Cache Implementation
```python
class CacheManager:
    def __init__(self):
        try:
            self.redis = redis.Redis.from_url(REDIS_URL)
            self.redis.ping()
            self.use_redis = True
        except:
            self.use_redis = False
            self.memory_cache = {}
    
    async def get(self, key: str):
        if self.use_redis:
            value = self.redis.get(key)
            return json.loads(value) if value else None
        else:
            return self.memory_cache.get(key)
    
    async def set(self, key: str, value: any, ttl: int = 60):
        if self.use_redis:
            self.redis.setex(key, ttl, json.dumps(value))
        else:
            # Simple in-memory cache with expiration
            self.memory_cache[key] = {
                'value': value,
                'expires': time.time() + ttl
            }
```

### Cache Strategy

#### Cache Levels
1. **L1 Cache**: In-memory (immediate access)
2. **L2 Cache**: Redis (shared across instances)
3. **L3 Cache**: External API fallback

#### TTL Configuration
```python
CACHE_TTL = {
    'stock_details': 60,      # 1 minute
    'top_stocks': 120,        # 2 minutes
    'market_indexes': 60,     # 1 minute
    'news': 300,              # 5 minutes
    'portfolio_analytics': 30  # 30 seconds
}
```

#### Cache Invalidation
```python
# Automatic expiration based on TTL
# Manual invalidation for user actions
async def invalidate_user_cache(user_id: int):
    await cache.delete(f"portfolio_analytics:user_{user_id}")
    await cache.delete(f"dashboard_data:user_{user_id}")
```

## Data Flow Architecture

### Read Operations
```
Request → Cache Check → Database/API → Cache Store → Response
    │         │             │             │
    │         └─ HIT ────────┼─────────────┘
    └─ MISS ────────────────┘
```

### Write Operations
```
User Action → Database Update → Cache Invalidation → Fresh Data
```

## Performance Optimizations

### Database Optimizations
```sql
-- Indexes for frequent queries
CREATE INDEX idx_user_following_user_id ON userfollowing(user_id);
CREATE INDEX idx_user_following_symbol ON userfollowing(symbol);
CREATE INDEX idx_user_following_type ON userfollowing(asset_type);

-- Composite index for portfolio queries
CREATE INDEX idx_user_portfolio ON userfollowing(user_id, asset_type);
```

### Connection Pooling
```python
# SQLite connection pool configuration
engine = create_engine(
    database_url,
    pool_size=20,
    max_overflow=0,
    pool_pre_ping=True,
    pool_recycle=300
)
```

### Query Optimization
```python
# Efficient portfolio analytics query
def get_portfolio_summary(user_id: int):
    return db.exec(
        select(UserFollowing)
        .where(UserFollowing.user_id == user_id)
        .options(selectinload(UserFollowing.user))
    ).all()
```

## Backup & Recovery

### Database Backup
```bash
# SQLite backup
sqlite3 tradingai.db ".backup backup_$(date +%Y%m%d).db"

# Scheduled backup (cron)
0 2 * * * sqlite3 /path/to/tradingai.db ".backup /backups/tradingai_$(date +\%Y\%m\%d).db"
```

### Cache Recovery
```python
# Redis persistence configuration
# Automatic RDB snapshots every 60 seconds if at least 1000 keys changed
save 60 1000

# AOF (Append Only File) for durability
appendonly yes
appendfsync everysec
```

## Monitoring & Health Checks

### Database Health
```python
@app.get("/health/database")
async def database_health():
    try:
        with Session(engine) as session:
            session.exec(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
```

### Cache Health
```python
@app.get("/health/cache")
async def cache_health():
    cache = await get_cache()
    await cache.set("health_check", "ok", ttl=10)
    result = await cache.get("health_check")
    
    return {
        "status": "healthy" if result == "ok" else "degraded",
        "cache_type": "redis" if cache.use_redis else "memory"
    }
```

## Migration Strategy

### Database Migrations
```python
# Using Alembic for schema changes
from alembic import command
from alembic.config import Config

def run_migrations():
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")
```

### Data Migration Example
```python
# Migrate legacy user data
def migrate_user_data():
    with Session(engine) as session:
        # Add new fields with defaults
        users = session.exec(select(User)).all()
        for user in users:
            if not hasattr(user, 'created_at'):
                user.created_at = datetime.utcnow()
        session.commit()
```

## Security Considerations

### Database Security
- SQLite file permissions (600)
- Input sanitization via SQLModel
- Parameterized queries prevent SQL injection
- Connection encryption in production

### Cache Security
- Redis AUTH password protection
- Network isolation (localhost only)
- No sensitive data in cache keys
- Automatic expiration of cached data