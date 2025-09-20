# Real-Time Data Manager using Polygon.io WebSocket
# Manages real-time stock price updates and broadcasts to connected clients

import asyncio
import json
import logging
import os
from typing import Dict, Set, List, Optional, Any
from dataclasses import asdict
from fastapi import WebSocket
from datetime import datetime

from services.polygon_websocket import PolygonWebSocketClient, StockQuote, StockAggregate
from services.redis_cache import RedisCompatibleCache

logger = logging.getLogger(__name__)

class RealTimeDataManager:
    """
    Manages real-time market data streaming and WebSocket connections
    
    Features:
    - Real-time stock price updates via Polygon.io WebSocket
    - Multiple client WebSocket connections
    - Automatic subscription management
    - Data caching and persistence
    - Graceful fallback to mock data
    """
    
    def __init__(self, cache_manager: Optional[RedisCompatibleCache] = None):
        self.polygon_api_key = os.getenv("POLYGON_API_KEY")
        self.cache_manager = cache_manager
        
        # WebSocket connections management
        self.connected_clients: Dict[str, WebSocket] = {}
        self.client_subscriptions: Dict[str, Set[str]] = {}  # client_id -> set of symbols
        self.symbol_subscribers: Dict[str, Set[str]] = {}    # symbol -> set of client_ids
        
        # Polygon WebSocket client
        self.polygon_client: Optional[PolygonWebSocketClient] = None
        self.is_running = False
        self.monitored_symbols: Set[str] = set()
        
        # Fallback mode when no API key
        self.use_fallback = not bool(self.polygon_api_key)
        
        if self.use_fallback:
            logger.warning("POLYGON_API_KEY not found. Running in fallback mode with mock data.")
        else:
            logger.info("Real-time data manager initialized with Polygon.io integration")
    
    async def start(self):
        """Start the real-time data manager"""
        if self.is_running:
            return
            
        self.is_running = True
        
        if not self.use_fallback:
            # Initialize Polygon WebSocket client
            self.polygon_client = PolygonWebSocketClient(
                self.polygon_api_key,
                is_delayed=True  # Use True for free tier
            )
            
            # Add event handlers
            self.polygon_client.add_quote_handler(self._handle_quote_update)
            self.polygon_client.add_aggregate_handler(self._handle_aggregate_update)
            self.polygon_client.add_error_handler(self._handle_error)
            
            # Start monitoring task
            asyncio.create_task(self._start_polygon_monitoring())
        else:
            # Start fallback mock data task
            asyncio.create_task(self._start_fallback_monitoring())
            
        logger.info("Real-time data manager started")
    
    async def stop(self):
        """Stop the real-time data manager"""
        self.is_running = False
        
        if self.polygon_client:
            await self.polygon_client.disconnect()
            
        # Disconnect all clients
        for client_id in list(self.connected_clients.keys()):
            await self.disconnect_client(client_id)
            
        logger.info("Real-time data manager stopped")
    
    async def connect_client(self, client_id: str, websocket: WebSocket) -> bool:
        """Connect a new WebSocket client"""
        try:
            await websocket.accept()
            self.connected_clients[client_id] = websocket
            self.client_subscriptions[client_id] = set()
            
            logger.info(f"Client {client_id} connected")
            
            # Send welcome message
            await self._send_to_client(client_id, {
                "type": "connected",
                "client_id": client_id,
                "timestamp": datetime.now().isoformat(),
                "message": "Connected to real-time data feed"
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Error connecting client {client_id}: {e}")
            return False
    
    async def disconnect_client(self, client_id: str):
        """Disconnect a WebSocket client"""
        if client_id in self.connected_clients:
            # Unsubscribe from all symbols
            if client_id in self.client_subscriptions:
                for symbol in self.client_subscriptions[client_id].copy():
                    await self.unsubscribe_client(client_id, symbol)
            
            # Close WebSocket connection
            try:
                websocket = self.connected_clients[client_id]
                await websocket.close()
            except:
                pass
            
            # Clean up tracking
            del self.connected_clients[client_id]
            if client_id in self.client_subscriptions:
                del self.client_subscriptions[client_id]
            
            logger.info(f"Client {client_id} disconnected")
    
    async def subscribe_client(self, client_id: str, symbols: List[str]):
        """Subscribe a client to real-time updates for symbols"""
        if client_id not in self.connected_clients:
            logger.warning(f"Client {client_id} not connected")
            return
        
        for symbol in symbols:
            symbol = symbol.upper()
            
            # Add to client subscriptions
            self.client_subscriptions[client_id].add(symbol)
            
            # Add to symbol subscribers
            if symbol not in self.symbol_subscribers:
                self.symbol_subscribers[symbol] = set()
            self.symbol_subscribers[symbol].add(client_id)
            
            # Add to monitored symbols if new
            if symbol not in self.monitored_symbols:
                self.monitored_symbols.add(symbol)
                
                # Subscribe to Polygon WebSocket if available
                if self.polygon_client and self.polygon_client.is_connected:
                    await self.polygon_client.subscribe_quotes([symbol])
                    await self.polygon_client.subscribe_aggregates([symbol])
        
        logger.info(f"Client {client_id} subscribed to: {symbols}")
        
        # Send current data for subscribed symbols
        await self._send_current_data_to_client(client_id, symbols)
    
    async def unsubscribe_client(self, client_id: str, symbol: str):
        """Unsubscribe a client from a symbol"""
        symbol = symbol.upper()
        
        if client_id in self.client_subscriptions:
            self.client_subscriptions[client_id].discard(symbol)
        
        if symbol in self.symbol_subscribers:
            self.symbol_subscribers[symbol].discard(client_id)
            
            # If no more subscribers for this symbol, remove from monitoring
            if not self.symbol_subscribers[symbol]:
                self.monitored_symbols.discard(symbol)
                del self.symbol_subscribers[symbol]
        
        logger.info(f"Client {client_id} unsubscribed from {symbol}")
    
    async def _handle_quote_update(self, quote: StockQuote):
        """Handle real-time quote update from Polygon"""
        symbol = quote.symbol
        
        # Cache the quote data
        if self.cache_manager:
            await self.cache_manager.set(
                f"realtime_quote:{symbol}",
                json.dumps(asdict(quote)),
                ttl=60  # 1 minute TTL
            )
        
        # Broadcast to subscribed clients
        if symbol in self.symbol_subscribers:
            message = {
                "type": "quote_update",
                "symbol": symbol,
                "data": asdict(quote),
                "timestamp": datetime.now().isoformat()
            }
            
            await self._broadcast_to_symbol_subscribers(symbol, message)
    
    async def _handle_aggregate_update(self, aggregate: StockAggregate):
        """Handle real-time aggregate update from Polygon"""
        symbol = aggregate.symbol
        
        # Cache the aggregate data
        if self.cache_manager:
            await self.cache_manager.set(
                f"realtime_aggregate:{symbol}",
                json.dumps(asdict(aggregate)),
                ttl=300  # 5 minutes TTL
            )
        
        # Broadcast to subscribed clients
        if symbol in self.symbol_subscribers:
            message = {
                "type": "aggregate_update",
                "symbol": symbol,
                "data": asdict(aggregate),
                "timestamp": datetime.now().isoformat()
            }
            
            await self._broadcast_to_symbol_subscribers(symbol, message)
    
    async def _handle_error(self, error_message: str):
        """Handle WebSocket errors from Polygon"""
        logger.error(f"Polygon WebSocket error: {error_message}")
        
        # Broadcast error to all connected clients
        error_msg = {
            "type": "error",
            "message": error_message,
            "timestamp": datetime.now().isoformat()
        }
        
        await self._broadcast_to_all_clients(error_msg)
    
    async def _start_polygon_monitoring(self):
        """Start Polygon WebSocket monitoring"""
        while self.is_running:
            try:
                if self.monitored_symbols:
                    await self.polygon_client.start_monitoring(
                        list(self.monitored_symbols),
                        subscribe_quotes=True,
                        subscribe_aggregates=True
                    )
                else:
                    # Wait for symbols to monitor
                    await asyncio.sleep(5)
                    
            except Exception as e:
                logger.error(f"Error in Polygon monitoring: {e}")
                await asyncio.sleep(10)  # Wait before retrying
    
    async def _start_fallback_monitoring(self):
        """Start fallback mock data monitoring"""
        from agents.tools import MOCK_STOCK_DATA
        
        while self.is_running:
            try:
                # Send mock price updates every 30 seconds
                for symbol in self.monitored_symbols:
                    if symbol in MOCK_STOCK_DATA:
                        # Generate small random price movements
                        import random
                        base_price = MOCK_STOCK_DATA[symbol]["price"]
                        price_change = random.uniform(-0.02, 0.02)  # ±2%
                        new_price = base_price * (1 + price_change)
                        
                        # Create mock quote update
                        mock_quote = {
                            "symbol": symbol,
                            "price": round(new_price, 2),
                            "size": random.randint(100, 1000),
                            "exchange": 1,
                            "timestamp": int(datetime.now().timestamp() * 1000),
                            "timeframe": "mock_realtime"
                        }
                        
                        # Broadcast to subscribers
                        if symbol in self.symbol_subscribers:
                            message = {
                                "type": "quote_update",
                                "symbol": symbol,
                                "data": mock_quote,
                                "timestamp": datetime.now().isoformat(),
                                "source": "mock_data"
                            }
                            
                            await self._broadcast_to_symbol_subscribers(symbol, message)
                
                await asyncio.sleep(30)  # Update every 30 seconds
                
            except Exception as e:
                logger.error(f"Error in fallback monitoring: {e}")
                await asyncio.sleep(10)
    
    async def _send_current_data_to_client(self, client_id: str, symbols: List[str]):
        """Send current cached data to a newly subscribed client"""
        from agents.real_data_tools import RealMarketDataTool
        
        market_tool = RealMarketDataTool()
        
        for symbol in symbols:
            try:
                # Get current stock data
                stock_data = await market_tool.get_stock_data(symbol)
                
                if "error" not in stock_data:
                    message = {
                        "type": "current_data",
                        "symbol": symbol,
                        "data": stock_data,
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    await self._send_to_client(client_id, message)
            
            except Exception as e:
                logger.error(f"Error sending current data for {symbol}: {e}")
    
    async def _broadcast_to_symbol_subscribers(self, symbol: str, message: Dict[str, Any]):
        """Broadcast message to all clients subscribed to a symbol"""
        if symbol not in self.symbol_subscribers:
            return
        
        disconnected_clients = []
        
        for client_id in self.symbol_subscribers[symbol]:
            try:
                await self._send_to_client(client_id, message)
            except Exception as e:
                logger.warning(f"Failed to send to client {client_id}: {e}")
                disconnected_clients.append(client_id)
        
        # Clean up disconnected clients
        for client_id in disconnected_clients:
            await self.disconnect_client(client_id)
    
    async def _broadcast_to_all_clients(self, message: Dict[str, Any]):
        """Broadcast message to all connected clients"""
        disconnected_clients = []
        
        for client_id in list(self.connected_clients.keys()):
            try:
                await self._send_to_client(client_id, message)
            except Exception as e:
                logger.warning(f"Failed to send to client {client_id}: {e}")
                disconnected_clients.append(client_id)
        
        # Clean up disconnected clients
        for client_id in disconnected_clients:
            await self.disconnect_client(client_id)
    
    async def _send_to_client(self, client_id: str, message: Dict[str, Any]):
        """Send message to a specific client"""
        if client_id not in self.connected_clients:
            return
        
        websocket = self.connected_clients[client_id]
        await websocket.send_json(message)
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get statistics about connections and subscriptions"""
        return {
            "connected_clients": len(self.connected_clients),
            "monitored_symbols": len(self.monitored_symbols),
            "total_subscriptions": sum(len(subs) for subs in self.client_subscriptions.values()),
            "symbols_with_subscribers": len(self.symbol_subscribers),
            "polygon_connected": self.polygon_client.is_connected if self.polygon_client else False,
            "fallback_mode": self.use_fallback
        }


# Global instance
realtime_manager: Optional[RealTimeDataManager] = None

async def get_realtime_manager() -> RealTimeDataManager:
    """Get or create the global real-time data manager"""
    global realtime_manager
    
    if realtime_manager is None:
        from services.redis_cache import get_cache_manager
        cache_manager = await get_cache_manager()
        realtime_manager = RealTimeDataManager(cache_manager)
        await realtime_manager.start()
    
    return realtime_manager

async def shutdown_realtime_manager():
    """Shutdown the global real-time data manager"""
    global realtime_manager
    
    if realtime_manager:
        await realtime_manager.stop()
        realtime_manager = None