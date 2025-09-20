# TradingAI API Structure

## Base URL
- **Development**: `http://localhost:8000`
- **All responses**: JSON format with consistent error handling

## Authentication

### Endpoints
```
POST /auth/register     - User registration
POST /auth/login        - User login (returns JWT token)
GET  /auth/me          - Get current user info
POST /auth/logout      - User logout
```

### JWT Token Usage
```bash
# Include in request headers
Authorization: Bearer <jwt_token>
```

## Stock Data APIs

### Public Stock Data
```
GET /stocks/top?limit=10              - Top performing stocks
GET /stocks/search?query=AAPL&limit=5 - Search stocks by symbol/name
GET /stocks/{symbol}                  - Detailed stock information
```

**Response Format**:
```json
{
  "stocks": [
    {
      "symbol": "AAPL",
      "name": "Apple Inc.",
      "price": 175.43,
      "change": 2.15,
      "change_percent": 1.24,
      "volume": 45231876,
      "market_cap": 2750000000000,
      "timestamp": "2024-01-15T16:00:00Z"
    }
  ],
  "count": 10
}
```

## Portfolio Management APIs

### Portfolio Analytics (Public Testing)
```
GET /portfolio/dashboard/data/public    - Portfolio dashboard data
GET /portfolio/analytics/public        - Advanced portfolio analytics
GET /portfolio/followed/realtime/public - Real-time followed stocks
```

### User Portfolio (Authenticated)
```
GET    /portfolio/followed             - Get user's followed stocks
POST   /portfolio/followed             - Follow a stock
DELETE /portfolio/followed/{item_id}   - Unfollow a stock
GET    /portfolio/dashboard/data       - User dashboard data
```

**Portfolio Analytics Response**:
```json
{
  "summary": {
    "total_stocks": 10,
    "gainers": 7,
    "losers": 3,
    "avg_change": 1.25,
    "risk_level": "Medium",
    "diversification_score": 75.5,
    "total_value": 156890.50
  },
  "sector_breakdown": {
    "Technology": {
      "count": 4,
      "avg_change": 2.1,
      "stocks": ["AAPL", "GOOGL", "MSFT", "NVDA"]
    }
  },
  "top_performer": {
    "symbol": "NVDA",
    "change_percent": 8.5
  },
  "recommendations": [
    "Consider diversifying across more sectors",
    "High-performing tech stocks detected"
  ]
}
```

## Market Data APIs

### Market Information
```
GET /market/indexes                    - Major market indexes (SPY, QQQ, DIA)
GET /cryptos/top?limit=5              - Top cryptocurrencies
GET /news/latest?limit=10             - Latest financial news
GET /news/stock/{symbol}?limit=5      - Stock-specific news
```

**News Response Format**:
```json
{
  "news": [
    {
      "title": "Apple Reports Strong Q4 Earnings",
      "description": "Apple Inc. reported better than expected earnings...",
      "source": "Financial Times",
      "url": "https://...",
      "sentiment": 0.75,
      "published_at": "2024-01-15T14:30:00Z"
    }
  ],
  "count": 10
}
```

## Real-time WebSocket APIs

### WebSocket Connections
```
ws://localhost:8000/ws/realtime?client_id={unique_id}
```

**WebSocket Message Format**:
```json
{
  "type": "stock_update",
  "data": {
    "symbol": "AAPL",
    "price": 175.43,
    "change": 2.15,
    "change_percent": 1.24,
    "volume": 45231876,
    "timestamp": "2024-01-15T16:00:00Z"
  }
}
```

### Subscription Management
```json
// Subscribe to stock updates
{
  "action": "subscribe",
  "symbols": ["AAPL", "GOOGL", "MSFT"]
}

// Unsubscribe from updates
{
  "action": "unsubscribe", 
  "symbols": ["AAPL"]
}
```

## Rate Limiting & Caching

### Rate Limits
- **Polygon API**: 5 requests per second
- **Internal caching**: 30-120 seconds TTL
- **Automatic fallback**: Mock data when APIs unavailable

### Cache Headers
```
Cache-Control: max-age=60
X-Cache-Status: HIT|MISS
X-Rate-Limit-Remaining: 95
```

## Error Handling

### Standard Error Format
```json
{
  "error": {
    "code": "STOCK_NOT_FOUND",
    "message": "Stock symbol INVALID not found",
    "details": {
      "symbol": "INVALID",
      "suggestions": ["NVDA", "INTC"]
    }
  }
}
```

### HTTP Status Codes
- `200` - Success
- `400` - Bad Request (invalid parameters)
- `401` - Unauthorized (invalid/missing token)
- `404` - Not Found
- `429` - Too Many Requests (rate limited)
- `500` - Internal Server Error

## Frontend Integration Examples

### Using Custom Hooks
```typescript
// Fetch top stocks with auto-refresh
const { data, loading, error } = useTopStocks(10)

// Get portfolio analytics
const { data: analytics } = usePortfolioAnalytics()

// Real-time stock data
const { data: realtimeData, isConnected } = useRealtimeData({
  symbols: ['AAPL', 'GOOGL'],
  enabled: true
})
```

### Making Direct API Calls
```typescript
// Fetch with error handling
const response = await fetch('http://localhost:8000/stocks/top?limit=5')
if (!response.ok) {
  throw new Error(`HTTP error! status: ${response.status}`)
}
const data = await response.json()
```

## Development & Testing

### Health Check
```
GET /health                           - API health status
```

### Mock Data Fallback
When external APIs are unavailable, the system automatically serves mock data with similar structure to maintain frontend compatibility.

### CORS Configuration
```
Allowed Origins: http://localhost:3000, http://localhost:5173
Allowed Methods: GET, POST, PUT, DELETE, OPTIONS
Allowed Headers: Authorization, Content-Type
```