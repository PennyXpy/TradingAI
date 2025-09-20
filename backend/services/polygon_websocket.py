# Polygon.io WebSocket Client for Real-Time Market Data
# Based on official Polygon.io WebSocket documentation

import asyncio
import json
import logging
import os
import websockets
from typing import Dict, List, Callable, Optional, Any
from datetime import datetime
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class StockQuote:
    """Real-time stock quote data from Polygon.io"""
    symbol: str
    price: float
    size: int
    exchange: int
    timestamp: int
    timeframe: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "price": self.price,
            "size": self.size,
            "exchange": self.exchange,
            "timestamp": self.timestamp,
            "timeframe": self.timeframe,
            "datetime": datetime.fromtimestamp(self.timestamp / 1000).isoformat()
        }

@dataclass
class StockAggregate:
    """Stock aggregate (OHLC) data from Polygon.io"""
    symbol: str
    open: float
    high: float
    low: float
    close: float
    volume: int
    vwap: float
    timestamp: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume,
            "vwap": self.vwap,
            "timestamp": self.timestamp,
            "datetime": datetime.fromtimestamp(self.timestamp / 1000).isoformat()
        }

class PolygonWebSocketClient:
    """
    Real-time WebSocket client for Polygon.io market data
    
    Based on Polygon.io WebSocket API documentation:
    - Supports real-time quotes, aggregates, and trades
    - Handles authentication with API key
    - Manages subscriptions and reconnections
    """
    
    def __init__(self, api_key: str, is_delayed: bool = False):
        self.api_key = api_key
        self.is_delayed = is_delayed
        
        # WebSocket endpoints
        if is_delayed:
            self.ws_url = "wss://delayed.polygon.io/stocks"
        else:
            self.ws_url = "wss://socket.polygon.io/stocks"
            
        self.websocket = None
        self.is_connected = False
        self.subscriptions: List[str] = []
        
        # Event handlers
        self.quote_handlers: List[Callable[[StockQuote], None]] = []
        self.aggregate_handlers: List[Callable[[StockAggregate], None]] = []
        self.error_handlers: List[Callable[[str], None]] = []
        
    async def connect(self):
        """Connect to Polygon WebSocket and authenticate"""
        try:
            logger.info(f"Connecting to Polygon WebSocket: {self.ws_url}")
            self.websocket = await websockets.connect(self.ws_url)
            
            # Send authentication message
            auth_message = {
                "action": "auth",
                "params": self.api_key
            }
            await self.websocket.send(json.dumps(auth_message))
            logger.info("Authentication message sent")
            
            # Wait for authentication response
            response = await self.websocket.recv()
            auth_response = json.loads(response)
            
            # Handle different response formats
            if isinstance(auth_response, list) and len(auth_response) > 0:
                status_msg = auth_response[0]
            else:
                status_msg = auth_response
                
            # Check for successful connection status
            if (status_msg.get("status") == "auth_success" or 
                status_msg.get("status") == "connected" or 
                status_msg.get("message") == "Connected Successfully"):
                self.is_connected = True
                logger.info("Successfully authenticated with Polygon WebSocket")
                
                # Re-subscribe to previous subscriptions if any
                if self.subscriptions:
                    await self._resubscribe()
                    
            else:
                logger.error(f"Authentication failed: {auth_response}")
                self.is_connected = False
                
        except Exception as e:
            logger.error(f"Failed to connect to Polygon WebSocket: {e}")
            self.is_connected = False
            await self._handle_error(f"Connection error: {e}")
            
    async def disconnect(self):
        """Disconnect from WebSocket"""
        if self.websocket:
            await self.websocket.close()
            self.is_connected = False
            logger.info("Disconnected from Polygon WebSocket")
            
    async def subscribe_quotes(self, symbols: List[str]):
        """
        Subscribe to real-time quotes for given symbols
        
        Args:
            symbols: List of stock symbols (e.g., ['AAPL', 'GOOGL'])
        """
        if not self.is_connected:
            logger.warning("Not connected to WebSocket. Storing subscription for later.")
            
        # Format subscription message for quotes
        subscription_message = {
            "action": "subscribe",
            "params": f"Q.{',Q.'.join(symbols)}"
        }
        
        if self.is_connected:
            await self.websocket.send(json.dumps(subscription_message))
            logger.info(f"Subscribed to quotes for: {symbols}")
        
        # Store subscriptions for reconnection
        for symbol in symbols:
            subscription = f"Q.{symbol}"
            if subscription not in self.subscriptions:
                self.subscriptions.append(subscription)
                
    async def subscribe_aggregates(self, symbols: List[str], timeframe: str = "1"):
        """
        Subscribe to real-time aggregates (OHLC) for given symbols
        
        Args:
            symbols: List of stock symbols
            timeframe: Timeframe for aggregates ('1' for 1-minute)
        """
        if not self.is_connected:
            logger.warning("Not connected to WebSocket. Storing subscription for later.")
            
        # Format subscription message for aggregates
        if timeframe == "1":
            # Subscribe to minute aggregates
            subscription_message = {
                "action": "subscribe", 
                "params": f"AM.{',AM.'.join(symbols)}"
            }
            subscription_prefix = "AM"
        else:
            # Default to minute aggregates
            subscription_message = {
                "action": "subscribe",
                "params": f"AM.{',AM.'.join(symbols)}"
            }
            subscription_prefix = "AM"
            
        if self.is_connected:
            await self.websocket.send(json.dumps(subscription_message))
            logger.info(f"Subscribed to {timeframe}-minute aggregates for: {symbols}")
        
        # Store subscriptions for reconnection
        for symbol in symbols:
            subscription = f"{subscription_prefix}.{symbol}"
            if subscription not in self.subscriptions:
                self.subscriptions.append(subscription)
                
    async def _resubscribe(self):
        """Re-subscribe to all stored subscriptions after reconnection"""
        if self.subscriptions and self.is_connected:
            subscription_message = {
                "action": "subscribe",
                "params": ",".join(self.subscriptions)
            }
            await self.websocket.send(json.dumps(subscription_message))
            logger.info(f"Re-subscribed to: {self.subscriptions}")
            
    async def listen(self):
        """
        Listen for incoming WebSocket messages and dispatch to handlers
        """
        if not self.is_connected or not self.websocket:
            logger.error("WebSocket not connected")
            return
            
        try:
            async for message in self.websocket:
                await self._process_message(message)
                
        except websockets.exceptions.ConnectionClosed:
            logger.warning("WebSocket connection closed")
            self.is_connected = False
            await self._handle_error("Connection closed")
            
        except Exception as e:
            logger.error(f"Error listening to WebSocket: {e}")
            await self._handle_error(f"Listen error: {e}")
            
    async def _process_message(self, message: str):
        """Process incoming WebSocket message"""
        try:
            data = json.loads(message)
            
            # Handle array of events
            if isinstance(data, list):
                for event in data:
                    await self._handle_event(event)
            else:
                await self._handle_event(data)
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse WebSocket message: {e}")
            
    async def _handle_event(self, event: Dict[str, Any]):
        """Handle individual event from WebSocket"""
        event_type = event.get("ev")
        
        if event_type == "Q":
            # Quote event
            quote = StockQuote(
                symbol=event.get("sym", ""),
                price=event.get("ap", 0.0),  # Ask price
                size=event.get("as", 0),     # Ask size
                exchange=event.get("ax", 0), # Ask exchange
                timestamp=event.get("t", 0),
                timeframe="real-time"
            )
            
            # Dispatch to quote handlers
            for handler in self.quote_handlers:
                try:
                    handler(quote)
                except Exception as e:
                    logger.error(f"Error in quote handler: {e}")
                    
        elif event_type == "AM":
            # Aggregate minute event
            aggregate = StockAggregate(
                symbol=event.get("sym", ""),
                open=event.get("o", 0.0),
                high=event.get("h", 0.0),
                low=event.get("l", 0.0),
                close=event.get("c", 0.0),
                volume=event.get("v", 0),
                vwap=event.get("a", 0.0),
                timestamp=event.get("s", 0)  # Start timestamp
            )
            
            # Dispatch to aggregate handlers
            for handler in self.aggregate_handlers:
                try:
                    handler(aggregate)
                except Exception as e:
                    logger.error(f"Error in aggregate handler: {e}")
                    
        elif event_type == "status":
            # Status message
            status = event.get("status")
            message = event.get("message", "")
            logger.info(f"Polygon WebSocket status: {status} - {message}")
            
        else:
            logger.debug(f"Unhandled event type: {event_type}")
            
    async def _handle_error(self, error_message: str):
        """Handle WebSocket errors"""
        for handler in self.error_handlers:
            try:
                handler(error_message)
            except Exception as e:
                logger.error(f"Error in error handler: {e}")
                
    def add_quote_handler(self, handler: Callable[[StockQuote], None]):
        """Add handler for quote events"""
        self.quote_handlers.append(handler)
        
    def add_aggregate_handler(self, handler: Callable[[StockAggregate], None]):
        """Add handler for aggregate events"""
        self.aggregate_handlers.append(handler)
        
    def add_error_handler(self, handler: Callable[[str], None]):
        """Add handler for error events"""
        self.error_handlers.append(handler)
        
    async def start_monitoring(self, symbols: List[str], subscribe_quotes: bool = True, subscribe_aggregates: bool = True, max_retries: int = 3):
        """
        Start monitoring symbols with limited reconnection attempts
        
        Args:
            symbols: List of symbols to monitor
            subscribe_quotes: Whether to subscribe to real-time quotes
            subscribe_aggregates: Whether to subscribe to minute aggregates
            max_retries: Maximum number of reconnection attempts
        """
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                if not self.is_connected:
                    await self.connect()
                    
                if self.is_connected:
                    if subscribe_quotes:
                        await self.subscribe_quotes(symbols)
                    if subscribe_aggregates:
                        await self.subscribe_aggregates(symbols)
                        
                    await self.listen()
                    break  # Exit loop if listening completes successfully
                    
            except Exception as e:
                retry_count += 1
                logger.error(f"Error in monitoring loop (attempt {retry_count}/{max_retries}): {e}")
                await self._handle_error(f"Monitoring error: {e}")
                
                if retry_count < max_retries:
                    # Wait before reconnection attempt
                    await asyncio.sleep(5)
                    logger.info(f"Attempting to reconnect... ({retry_count}/{max_retries})")
                else:
                    logger.error("Max reconnection attempts reached. Stopping WebSocket monitoring.")
                    break


# Example usage and testing
async def example_usage():
    """Example of how to use the Polygon WebSocket client"""
    
    # Get API key from environment
    api_key = os.getenv("POLYGON_API_KEY")
    if not api_key:
        logger.error("POLYGON_API_KEY not found in environment variables")
        return
        
    # Create client (use delayed=True for free tier)
    client = PolygonWebSocketClient(api_key, is_delayed=True)
    
    # Add event handlers
    def on_quote(quote: StockQuote):
        print(f"Quote: {quote.symbol} @ ${quote.price:.2f}")
        
    def on_aggregate(aggregate: StockAggregate):
        print(f"Aggregate: {aggregate.symbol} OHLC: {aggregate.open:.2f}/{aggregate.high:.2f}/{aggregate.low:.2f}/{aggregate.close:.2f}")
        
    def on_error(error: str):
        print(f"Error: {error}")
        
    client.add_quote_handler(on_quote)
    client.add_aggregate_handler(on_aggregate)
    client.add_error_handler(on_error)
    
    # Start monitoring
    symbols = ["AAPL", "GOOGL", "MSFT", "TSLA"]
    await client.start_monitoring(symbols)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(example_usage())