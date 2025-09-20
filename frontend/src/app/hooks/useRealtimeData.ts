"use client"

import { useState, useEffect, useRef, useCallback } from 'react'

interface RealtimeData {
  symbol: string
  price: number
  change: number
  change_percent: number
  volume: number
  timestamp: string
}

interface UseRealtimeDataProps {
  symbols?: string[]
  enabled?: boolean
}

export function useRealtimeData({ symbols = [], enabled = true }: UseRealtimeDataProps = {}) {
  const [data, setData] = useState<Record<string, RealtimeData>>({})
  const [isConnected, setIsConnected] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const clientId = useRef<string>(`client_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`)

  const connect = useCallback(() => {
    if (!enabled || wsRef.current?.readyState === WebSocket.OPEN) {
      return
    }

    try {
      const ws = new WebSocket(`ws://localhost:8000/ws/realtime?client_id=${clientId.current}`)
      wsRef.current = ws

      ws.onopen = () => {
        console.log('WebSocket connected for real-time data')
        setIsConnected(true)
        setError(null)

        // Subscribe to symbols if any
        if (symbols.length > 0) {
          ws.send(JSON.stringify({
            action: 'subscribe',
            symbols: symbols
          }))
        }
      }

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data)
          
          if (message.type === 'price_update') {
            const update = message.data as RealtimeData
            setData(prev => ({
              ...prev,
              [update.symbol]: update
            }))
          } else if (message.type === 'pong') {
            // Handle ping/pong for connection health
            console.log('Received pong from server')
          } else if (message.type === 'error') {
            console.error('WebSocket error:', message.message)
            setError(message.message)
          }
        } catch (err) {
          console.error('Failed to parse WebSocket message:', err)
        }
      }

      ws.onclose = () => {
        console.log('WebSocket connection closed')
        setIsConnected(false)
        
        // Attempt to reconnect after 3 seconds
        if (enabled) {
          reconnectTimeoutRef.current = setTimeout(() => {
            connect()
          }, 3000)
        }
      }

      ws.onerror = (error) => {
        console.error('WebSocket error:', error)
        setError('WebSocket connection error')
        setIsConnected(false)
      }

    } catch (err) {
      console.error('Failed to create WebSocket connection:', err)
      setError('Failed to connect to real-time data server')
    }
  }, [enabled, symbols])

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
      reconnectTimeoutRef.current = null
    }

    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }
    setIsConnected(false)
  }, [])

  const subscribe = useCallback((newSymbols: string[]) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        action: 'subscribe',
        symbols: newSymbols
      }))
    }
  }, [])

  const unsubscribe = useCallback((symbol: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        action: 'unsubscribe',
        symbol: symbol
      }))
    }
  }, [])

  // Send periodic pings to keep connection alive
  useEffect(() => {
    if (!isConnected || !wsRef.current) return

    const pingInterval = setInterval(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ action: 'ping' }))
      }
    }, 30000) // Send ping every 30 seconds

    return () => clearInterval(pingInterval)
  }, [isConnected])

  useEffect(() => {
    if (enabled) {
      connect()
    }

    return () => {
      disconnect()
    }
  }, [connect, disconnect, enabled])

  // Update subscriptions when symbols change
  useEffect(() => {
    if (isConnected && symbols.length > 0) {
      subscribe(symbols)
    }
  }, [symbols, isConnected, subscribe])

  return {
    data,
    isConnected,
    error,
    subscribe,
    unsubscribe,
    connect,
    disconnect
  }
}