# Polygon WebSocket Service for Real-time Stock Data
import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Set, Optional, Callable

# Try to import Polygon client, handle gracefully if not available
try:
    from polygon import WebSocketClient, STOCKS_CLUSTER
    from polygon.websocket.models import WebSocketMessage, EquityAgg
    POLYGON_AVAILABLE = True
except ImportError:
    POLYGON_AVAILABLE = False
    WebSocketClient = None
    STOCKS_CLUSTER = None
    WebSocketMessage = None
    EquityAgg = None
    logging.warning("Polygon API client not available. Using mock data mode.")

import websockets

logger = logging.getLogger(__name__)

class PolygonWebSocketService:
    """
    Polygon WebSocket service for real-time stock data
    Handles minute aggregates and real-time price updates
    """
    
    def __init__(self):
        self.api_key = os.getenv("POLYGON_API_KEY")
        if not self.api_key or not POLYGON_AVAILABLE:
            logger.warning("POLYGON_API_KEY not found or Polygon client not available, using mock data")
            
        self.client: Optional[WebSocketClient] = None
        self.subscribed_symbols: Set[str] = set()
        self.latest_data: Dict[str, Dict] = {}
        self.subscribers: Dict[str, List[Callable]] = {}  # client_id -> [callback functions]
        self.is_connected = False
        self._connection_lock = asyncio.Lock()
        
    async def initialize(self):
        """Initialize Polygon WebSocket connection"""
        if not self.api_key or not POLYGON_AVAILABLE:
            logger.info("No Polygon API key or client not available, using mock data mode")
            self.is_connected = True
            await self._start_mock_data_stream()
            return
            
        try:
            # Initialize Polygon WebSocket client
            self.client = WebSocketClient(
                api_key=self.api_key,
                cluster=STOCKS_CLUSTER,
                on_message=self._handle_polygon_message
            )
            
            # Connect to Polygon
            await asyncio.get_event_loop().run_in_executor(
                None, self.client.connect
            )
            
            self.is_connected = True
            logger.info("✅ Polygon WebSocket connected")
            
        except Exception as e:
            logger.error(f"Failed to connect to Polygon WebSocket: {e}")
            logger.info("Falling back to mock data mode")
            self.is_connected = True
            await self._start_mock_data_stream()
    
    def _handle_polygon_message(self, message: WebSocketMessage):
        """Handle incoming messages from Polygon WebSocket"""
        try:
            if isinstance(message, EquityAgg):
                # Process minute aggregate data
                symbol = message.symbol
                
                # Calculate change from previous close
                # Note: In production, you'd want to store previous close prices
                change = 0.0
                change_percent = 0.0
                
                data = {
                    "symbol": symbol,
                    "price": float(message.close),
                    "volume": int(message.volume),
                    "high": float(message.high),
                    "low": float(message.low),
                    "open": float(message.open),
                    "change": change,
                    "change_percent": change_percent,
                    "timestamp": datetime.fromtimestamp(message.start_timestamp / 1000).isoformat(),
                    "source": "polygon"
                }
                
                self.latest_data[symbol] = data
                
                # Notify all subscribers
                asyncio.create_task(self._notify_subscribers(symbol, data))
                
        except Exception as e:
            logger.error(f"Error processing Polygon message: {e}")
    
    async def _start_mock_data_stream(self):
        """Start mock data stream when Polygon is not available"""
        asyncio.create_task(self._mock_data_generator())
    
    async def _mock_data_generator(self):
        """Generate mock real-time data for testing"""
        import random
        
        mock_symbols = ["AAPL", "GOOGL", "MSFT", "TSLA", "NVDA", "AMD", "META", "AMZN", "NFLX", "CRM"]
        base_prices = {
            "AAPL": 175.0, "GOOGL": 140.0, "MSFT": 380.0, "TSLA": 250.0, "NVDA": 450.0,
            "AMD": 145.0, "META": 320.0, "AMZN": 145.0, "NFLX": 480.0, "CRM": 250.0
        }
        
        while self.is_connected:
            try:
                for symbol in self.subscribed_symbols:
                    if symbol in mock_symbols:
                        base_price = base_prices.get(symbol, 100.0)
                        
                        # Generate realistic price movement
                        price_change = random.uniform(-0.02, 0.02)  # +/- 2%
                        new_price = base_price * (1 + price_change)
                        change = new_price - base_price
                        change_percent = (change / base_price) * 100
                        
                        data = {
                            "symbol": symbol,
                            "price": round(new_price, 2),
                            "volume": random.randint(100000, 2000000),
                            "high": round(new_price * random.uniform(1.0, 1.02), 2),
                            "low": round(new_price * random.uniform(0.98, 1.0), 2),
                            "open": round(base_price * random.uniform(0.99, 1.01), 2),
                            "change": round(change, 2),
                            "change_percent": round(change_percent, 2),
                            "timestamp": datetime.now().isoformat(),
                            "source": "mock"
                        }
                        
                        self.latest_data[symbol] = data
                        await self._notify_subscribers(symbol, data)
                
                await asyncio.sleep(5)  # Update every 5 seconds for testing
                
            except Exception as e:
                logger.error(f"Error in mock data generator: {e}")
                await asyncio.sleep(1)
    
    async def subscribe_to_symbol(self, symbol: str):
        """Subscribe to real-time data for a symbol"""
        async with self._connection_lock:
            if symbol not in self.subscribed_symbols:
                self.subscribed_symbols.add(symbol)
                
                if self.client and self.api_key:
                    try:
                        # Subscribe to minute aggregates
                        await asyncio.get_event_loop().run_in_executor(
                            None, 
                            lambda: self.client.subscribe_minute_aggregates([symbol])
                        )
                        logger.info(f"Subscribed to Polygon data for {symbol}")
                    except Exception as e:
                        logger.error(f"Failed to subscribe to {symbol}: {e}")
                else:
                    logger.info(f"Added {symbol} to mock data stream")
    
    async def unsubscribe_from_symbol(self, symbol: str):
        """Unsubscribe from real-time data for a symbol"""
        async with self._connection_lock:
            if symbol in self.subscribed_symbols:
                self.subscribed_symbols.remove(symbol)
                
                if self.client and self.api_key:
                    try:
                        await asyncio.get_event_loop().run_in_executor(
                            None,
                            lambda: self.client.unsubscribe_minute_aggregates([symbol])
                        )
                        logger.info(f"Unsubscribed from Polygon data for {symbol}")
                    except Exception as e:
                        logger.error(f"Failed to unsubscribe from {symbol}: {e}")
                
                # Clean up data
                if symbol in self.latest_data:
                    del self.latest_data[symbol]
    
    async def add_subscriber(self, client_id: str, callback: Callable):
        """Add a subscriber callback for real-time updates"""
        if client_id not in self.subscribers:
            self.subscribers[client_id] = []
        self.subscribers[client_id].append(callback)
    
    async def remove_subscriber(self, client_id: str):
        """Remove all callbacks for a client"""
        if client_id in self.subscribers:
            del self.subscribers[client_id]
    
    async def _notify_subscribers(self, symbol: str, data: Dict):
        """Notify all subscribers of new data"""
        for client_id, callbacks in self.subscribers.items():
            for callback in callbacks:
                try:
                    await callback(symbol, data)
                except Exception as e:
                    logger.error(f"Error notifying subscriber {client_id}: {e}")
    
    def get_latest_data(self, symbol: str) -> Optional[Dict]:
        """Get the latest data for a symbol"""
        return self.latest_data.get(symbol)
    
    def get_all_latest_data(self) -> Dict[str, Dict]:
        """Get all latest data"""
        return self.latest_data.copy()
    
    async def close(self):
        """Close the WebSocket connection"""
        self.is_connected = False
        
        if self.client:
            try:
                await asyncio.get_event_loop().run_in_executor(
                    None, self.client.close
                )
                logger.info("Polygon WebSocket connection closed")
            except Exception as e:
                logger.error(f"Error closing Polygon WebSocket: {e}")

# Global service instance
_polygon_service: Optional[PolygonWebSocketService] = None

async def get_polygon_service() -> PolygonWebSocketService:
    """Get or create the global Polygon WebSocket service"""
    global _polygon_service
    
    if _polygon_service is None:
        _polygon_service = PolygonWebSocketService()
        await _polygon_service.initialize()
    
    return _polygon_service

async def shutdown_polygon_service():
    """Shutdown the global Polygon WebSocket service"""
    global _polygon_service
    
    if _polygon_service:
        await _polygon_service.close()
        _polygon_service = None