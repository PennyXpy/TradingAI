# Configuration settings for TradingAI backend

import os
from datetime import timedelta

# JWT Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "tradingai-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./models/tradingai.db")

# Redis Configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

# OpenRouter API Configuration (for AI features)
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")

# CORS Configuration
CORS_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173"
]

# Cache Configuration
DEFAULT_CACHE_TTL = 300  # 5 minutes in seconds
MARKET_DATA_CACHE_TTL = 60  # 1 minute for market data
NEWS_CACHE_TTL = 1800  # 30 minutes for news data

# Agent Configuration
AGENT_MODEL = "deepseek/deepseek-chat"
AGENT_MAX_TOKENS = 2000
AGENT_TEMPERATURE = 0.7

# WebSocket Configuration
WEBSOCKET_HEARTBEAT_INTERVAL = 30  # seconds
WEBSOCKET_MAX_MESSAGE_SIZE = 10000  # bytes