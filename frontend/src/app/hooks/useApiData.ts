"use client"

import { useState, useEffect } from 'react'

interface ApiDataOptions {
  refreshInterval?: number
  enabled?: boolean
}

export function useApiData<T>(endpoint: string, options: ApiDataOptions = {}) {
  const { refreshInterval = 30000, enabled = true } = options
  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchData = async () => {
    if (!enabled) return

    try {
      const response = await fetch(`http://localhost:8000${endpoint}`)
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const result = await response.json()
      setData(result)
      setError(null)
    } catch (err) {
      console.error(`Failed to fetch data from ${endpoint}:`, err)
      setError(err instanceof Error ? err.message : 'Failed to fetch data')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()

    if (refreshInterval > 0) {
      const interval = setInterval(fetchData, refreshInterval)
      return () => clearInterval(interval)
    }
  }, [endpoint, refreshInterval, enabled])

  const refetch = () => {
    setLoading(true)
    fetchData()
  }

  return { data, loading, error, refetch }
}

// Specific hooks for different API endpoints
export function useTopStocks(limit: number = 5) {
  return useApiData<{stocks: any[], count: number}>(`/stocks/top?limit=${limit}`)
}

export function useTopCryptos(limit: number = 5) {
  return useApiData<{cryptos: any[], count: number}>(`/cryptos/top?limit=${limit}`)
}

export function useMarketIndexes() {
  return useApiData<{indexes: any[], last_updated: string}>('/market/indexes')
}

export function useLatestNews(limit: number = 10) {
  return useApiData<{news: any[], count: number}>(`/news/latest?limit=${limit}`)
}

export function useStockDetails(symbol: string) {
  return useApiData<{stock: any}>(`/stocks/${symbol}`, { 
    enabled: !!symbol,
    refreshInterval: 15000 // Refresh every 15 seconds for individual stocks
  })
}

export function useStockNews(symbol: string, limit: number = 5) {
  return useApiData<{news: any[], symbol: string, count: number}>(`/news/stock/${symbol}?limit=${limit}`, {
    enabled: !!symbol
  })
}

export function useDashboardData() {
  return useApiData<{followed_stocks: any[], user_has_followed_stocks: boolean, last_updated: string}>('/portfolio/dashboard/data/public', {
    refreshInterval: 10000 // Refresh every 10 seconds for dashboard
  })
}

export function useStockSearch(query: string, limit: number = 10) {
  return useApiData<{results: any[], query: string, count: number}>(`/stocks/search?query=${encodeURIComponent(query)}&limit=${limit}`, {
    enabled: !!query && query.length > 0,
    refreshInterval: 0 // No auto-refresh for search
  })
}

export function usePortfolioAnalytics() {
  return useApiData<{
    summary: any,
    sector_breakdown: any,
    top_performer: any,
    worst_performer: any,
    recommendations: string[],
    stocks: any[],
    last_updated: string
  }>('/portfolio/analytics/public', {
    refreshInterval: 15000 // Refresh every 15 seconds
  })
}

export function useFollowedStocksRealtime() {
  return useApiData<{
    followed_items: any[],
    count: number,
    last_updated: string
  }>('/portfolio/followed/realtime/public', {
    refreshInterval: 5000 // Refresh every 5 seconds for realtime data
  })
}