"use client"

import { useState, useEffect, useRef, useCallback } from 'react'

interface Message {
  id: string
  content: string
  isUser: boolean
  timestamp: Date
  type?: 'alert' | 'normal'
}

interface UseAIChatProps {
  userId: string
  enabled?: boolean
}

export function useAIChat({ userId, enabled = true }: UseAIChatProps) {
  const [messages, setMessages] = useState<Message[]>([])
  const [isConnected, setIsConnected] = useState(false)
  const [isTyping, setIsTyping] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const sessionIdRef = useRef<string | null>(null)

  const connect = useCallback(() => {
    if (!enabled || wsRef.current?.readyState === WebSocket.OPEN) {
      return
    }

    try {
      const ws = new WebSocket(`ws://localhost:8000/ws/chat?user_id=${userId}`)
      wsRef.current = ws

      ws.onopen = () => {
        console.log('WebSocket connected for AI chat')
        setIsConnected(true)
        setError(null)
      }

      ws.onmessage = (event) => {
        try {
          const response = JSON.parse(event.data)
          
          if (response.type === 'response') {
            sessionIdRef.current = response.session_id
            
            const aiMessage: Message = {
              id: Date.now().toString(),
              content: response.data.content || response.data.message || 'I received your message.',
              isUser: false,
              timestamp: new Date(response.timestamp || Date.now()),
              type: response.data.alert ? 'alert' : 'normal'
            }
            
            setMessages(prev => [...prev, aiMessage])
            setIsTyping(false)
          } else if (response.type === 'error') {
            console.error('AI Chat error:', response.message)
            setError(response.message)
            setIsTyping(false)
          }
        } catch (err) {
          console.error('Failed to parse AI chat message:', err)
          setIsTyping(false)
        }
      }

      ws.onclose = () => {
        console.log('AI Chat WebSocket connection closed')
        setIsConnected(false)
        setIsTyping(false)
        
        // Attempt to reconnect after 3 seconds
        if (enabled) {
          reconnectTimeoutRef.current = setTimeout(() => {
            connect()
          }, 3000)
        }
      }

      ws.onerror = (error) => {
        console.error('AI Chat WebSocket error:', error)
        setError('AI Chat connection error')
        setIsConnected(false)
        setIsTyping(false)
      }

    } catch (err) {
      console.error('Failed to create AI Chat WebSocket connection:', err)
      setError('Failed to connect to AI assistant')
    }
  }, [enabled, userId])

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
    setIsTyping(false)
  }, [])

  const sendMessage = useCallback((content: string) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      setError('Not connected to AI assistant')
      return false
    }

    try {
      // Add user message to chat
      const userMessage: Message = {
        id: Date.now().toString(),
        content,
        isUser: true,
        timestamp: new Date(),
        type: 'normal'
      }
      setMessages(prev => [...prev, userMessage])
      setIsTyping(true)
      setError(null)

      // Send to WebSocket
      wsRef.current.send(content)
      return true
    } catch (err) {
      console.error('Failed to send message:', err)
      setError('Failed to send message')
      setIsTyping(false)
      return false
    }
  }, [])

  // Initialize connection
  useEffect(() => {
    if (enabled) {
      connect()
    }

    return () => {
      disconnect()
    }
  }, [connect, disconnect, enabled])

  // Add initial welcome message
  useEffect(() => {
    if (isConnected && messages.length === 0) {
      const welcomeMessage: Message = {
        id: 'welcome',
        content: `Hello ${userId}! I'm your AI trading assistant. I can help you analyze market data, track your portfolio, and provide insights on stocks and cryptocurrencies. What can I help you with today?`,
        isUser: false,
        timestamp: new Date(),
        type: 'normal'
      }
      setMessages([welcomeMessage])
    }
  }, [isConnected, messages.length, userId])

  return {
    messages,
    isConnected,
    isTyping,
    error,
    sendMessage,
    connect,
    disconnect,
    sessionId: sessionIdRef.current
  }
}