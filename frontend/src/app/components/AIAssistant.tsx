"use client"

import { useState, useRef, useEffect } from 'react'
import { useAIChat } from '../hooks/useAIChat'

interface AIAssistantProps {
  username?: string
}

export default function AIAssistant({ username = 'User' }: AIAssistantProps) {
  const [newMessage, setNewMessage] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  
  // Use the AI chat hook
  const { 
    messages, 
    isConnected, 
    isTyping, 
    error, 
    sendMessage 
  } = useAIChat({ userId: username })

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSendMessage = async () => {
    if (!newMessage.trim() || !isConnected) return

    const success = sendMessage(newMessage)
    if (success) {
      setNewMessage('')
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  return (
    <div className="xl:col-span-2 flex flex-col gap-4 rounded-lg bg-slate-800 border border-slate-700 p-6 h-full min-h-[500px]">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="text-xl font-semibold flex items-center gap-2 text-white">
          <span className="text-[#1173d4] text-2xl">🤖</span> AI Assistant
        </h3>
        <div className="flex items-center gap-2">
          <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-400' : 'bg-red-400'}`}></div>
          <span className="text-xs text-slate-400">
            {isConnected ? 'Connected' : 'Disconnected'}
          </span>
        </div>
      </div>
      
      {error && (
        <div className="text-red-400 text-sm bg-red-900/20 border border-red-500/50 rounded p-2">
          {error}
        </div>
      )}
      
      {/* Chat Container */}
      <div className="flex flex-col flex-1 bg-slate-900 rounded-md overflow-hidden">
        {/* Messages */}
        <div className="flex-1 p-4 space-y-4 overflow-y-auto max-h-[400px]">
          {messages.map((message) => (
            <div key={message.id} className={`flex ${message.isUser ? 'justify-end' : 'items-start gap-2.5'}`}>
              {!message.isUser && (
                <span className="text-[#1173d4] text-xl mt-1">🤖</span>
              )}
              <div className={`rounded-lg max-w-[80%] p-3 ${
                message.isUser 
                  ? 'bg-[#1173d4] text-white' 
                  : message.type === 'alert'
                    ? 'bg-red-900/20 border border-red-500/50 text-red-300'
                    : 'bg-slate-700 text-white'
              }`}>
                {message.type === 'alert' && (
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-red-400 animate-pulse">⚠️</span>
                    <span className="text-xs font-semibold text-red-300">MARKET ALERT</span>
                  </div>
                )}
                <div className="text-sm whitespace-pre-wrap">
                  {message.content}
                </div>
                <div className="text-xs opacity-70 mt-2">
                  {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </div>
              </div>
            </div>
          ))}
          
          {/* Typing indicator */}
          {isTyping && (
            <div className="flex items-start gap-2.5">
              <span className="text-[#1173d4] text-xl mt-1">🤖</span>
              <div className="bg-slate-700 p-3 rounded-lg">
                <div className="flex space-x-1">
                  <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce"></div>
                  <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                  <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
        
        {/* Input */}
        <div className="p-4 bg-slate-800 border-t border-slate-700">
          <div className="relative">
            <input
              ref={inputRef}
              type="text"
              value={newMessage}
              onChange={(e) => setNewMessage(e.target.value)}
              onKeyDown={handleKeyPress}
              className="w-full bg-slate-700 rounded-full pl-4 pr-12 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#1173d4] border-transparent placeholder:text-slate-400 text-white"
              placeholder="Ask me anything..."
              disabled={isTyping}
            />
            <button
              onClick={handleSendMessage}
              disabled={!newMessage.trim() || isTyping || !isConnected}
              className="absolute right-2 top-1/2 -translate-y-1/2 p-2 rounded-full bg-[#1173d4] text-white hover:bg-[#0f5aa3] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <span className="text-sm">📤</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}