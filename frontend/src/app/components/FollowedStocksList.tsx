"use client"

import { useState, useEffect } from 'react'
import { useDashboardData } from '../hooks/useApiData'
import { useRealtimeData } from '../hooks/useRealtimeData'

export default function FollowedStocksList() {
  const { data: dashboardData, loading, refetch } = useDashboardData()
  const [sortBy, setSortBy] = useState<'symbol' | 'change' | 'price' | 'volume'>('change')
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc')
  const [filter, setFilter] = useState<'all' | 'gainers' | 'losers'>('all')

  // Get symbols for real-time data
  const symbols = (dashboardData?.followed_stocks || []).map(s => s.symbol)
  const { data: realtimeData, isConnected } = useRealtimeData({ 
    symbols,
    enabled: symbols.length > 0 
  })

  // Enhanced stock data with real-time updates
  const enhancedStocks = (dashboardData?.followed_stocks || []).map(stock => ({
    ...stock,
    price: realtimeData[stock.symbol]?.price || stock.price,
    change: realtimeData[stock.symbol]?.change || stock.change,
    change_percent: realtimeData[stock.symbol]?.change_percent || stock.change_percent,
    volume: realtimeData[stock.symbol]?.volume || stock.volume,
    isPositive: (realtimeData[stock.symbol]?.change || stock.change) >= 0,
    isRealtime: !!realtimeData[stock.symbol]
  }))

  // Apply filtering
  const filteredStocks = enhancedStocks.filter(stock => {
    if (filter === 'gainers') return stock.change >= 0
    if (filter === 'losers') return stock.change < 0
    return true
  })

  // Apply sorting
  const sortedStocks = [...filteredStocks].sort((a, b) => {
    let aVal, bVal
    
    switch (sortBy) {
      case 'symbol':
        aVal = a.symbol
        bVal = b.symbol
        break
      case 'change':
        aVal = a.change_percent || 0
        bVal = b.change_percent || 0
        break
      case 'price':
        aVal = a.price || 0
        bVal = b.price || 0
        break
      case 'volume':
        aVal = a.volume || 0
        bVal = b.volume || 0
        break
      default:
        return 0
    }

    if (typeof aVal === 'string') {
      return sortOrder === 'asc' ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal)
    } else {
      return sortOrder === 'asc' ? aVal - bVal : bVal - aVal
    }
  })

  const handleSort = (newSortBy: typeof sortBy) => {
    if (sortBy === newSortBy) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')
    } else {
      setSortBy(newSortBy)
      setSortOrder('desc')
    }
  }

  const formatNumber = (num: number, decimals: number = 2) => {
    if (num >= 1e9) return `${(num / 1e9).toFixed(1)}B`
    if (num >= 1e6) return `${(num / 1e6).toFixed(1)}M`
    if (num >= 1e3) return `${(num / 1e3).toFixed(1)}K`
    return num.toFixed(decimals)
  }

  const SortButton = ({ column, children }: { column: typeof sortBy, children: React.ReactNode }) => (
    <button
      onClick={() => handleSort(column)}
      className="flex items-center gap-1 text-left font-medium text-slate-300 hover:text-white transition-colors"
    >
      {children}
      {sortBy === column && (
        <span className="text-[#1173d4]">
          {sortOrder === 'asc' ? '↑' : '↓'}
        </span>
      )}
    </button>
  )

  if (loading) {
    return (
      <div className="bg-slate-800 border border-slate-700 rounded-xl p-6">
        <h2 className="text-xl font-semibold text-white mb-6">Followed Stocks</h2>
        <div className="space-y-4">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="animate-pulse flex items-center gap-4 p-4 bg-slate-700 rounded-lg">
              <div className="w-12 h-12 bg-slate-600 rounded-full"></div>
              <div className="flex-1 space-y-2">
                <div className="h-4 bg-slate-600 rounded w-1/4"></div>
                <div className="h-3 bg-slate-600 rounded w-1/2"></div>
              </div>
              <div className="space-y-2">
                <div className="h-4 bg-slate-600 rounded w-16"></div>
                <div className="h-3 bg-slate-600 rounded w-12"></div>
              </div>
            </div>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="bg-slate-800 border border-slate-700 rounded-xl p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-4">
          <h2 className="text-xl font-semibold text-white">Followed Stocks</h2>
          <div className="flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-400' : 'bg-red-400'}`}></div>
            <span className="text-xs text-slate-400">
              {isConnected ? 'Live' : 'Offline'}
            </span>
          </div>
        </div>
        
        <div className="flex items-center gap-3">
          {/* Filter Buttons */}
          <div className="flex bg-slate-700 rounded-lg p-1">
            {(['all', 'gainers', 'losers'] as const).map((filterOption) => (
              <button
                key={filterOption}
                onClick={() => setFilter(filterOption)}
                className={`px-3 py-1 text-sm font-medium rounded-md transition-colors ${
                  filter === filterOption
                    ? 'bg-[#1173d4] text-white'
                    : 'text-slate-300 hover:text-white'
                }`}
              >
                {filterOption === 'all' ? 'All' : filterOption === 'gainers' ? 'Gainers' : 'Losers'}
              </button>
            ))}
          </div>
          
          <button
            onClick={refetch}
            className="p-2 text-slate-400 hover:text-white transition-colors"
            title="Refresh data"
          >
            🔄
          </button>
        </div>
      </div>

      {/* Table Header */}
      <div className="grid grid-cols-12 gap-4 px-4 py-3 border-b border-slate-700 text-sm">
        <div className="col-span-4">
          <SortButton column="symbol">Stock</SortButton>
        </div>
        <div className="col-span-2 text-right">
          <SortButton column="price">Price</SortButton>
        </div>
        <div className="col-span-2 text-right">
          <SortButton column="change">Change</SortButton>
        </div>
        <div className="col-span-2 text-right">
          <SortButton column="volume">Volume</SortButton>
        </div>
        <div className="col-span-2 text-right">
          <span className="text-slate-300">Status</span>
        </div>
      </div>

      {/* Stock List */}
      <div className="space-y-2 mt-4">
        {sortedStocks.length === 0 ? (
          <div className="text-center py-12">
            <div className="text-4xl mb-4">📈</div>
            <h3 className="text-lg font-medium text-white mb-2">No stocks found</h3>
            <p className="text-slate-400">
              {filter === 'gainers' ? 'No gainers today' : 
               filter === 'losers' ? 'No losers today' : 
               'Start following stocks to see them here'}
            </p>
          </div>
        ) : (
          sortedStocks.map((stock) => (
            <div
              key={stock.id}
              className={`grid grid-cols-12 gap-4 items-center p-4 rounded-lg transition-colors hover:bg-slate-700 ${
                stock.isRealtime ? 'bg-slate-750' : 'bg-slate-800'
              }`}
            >
              {/* Stock Info */}
              <div className="col-span-4 flex items-center gap-3">
                <div className={`w-12 h-12 rounded-full flex items-center justify-center font-bold text-lg ${
                  stock.isPositive ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'
                }`}>
                  {stock.symbol.slice(0, 2)}
                </div>
                <div>
                  <div className="font-medium text-white">{stock.symbol}</div>
                  <div className="text-sm text-slate-400 truncate max-w-32">{stock.name}</div>
                </div>
              </div>

              {/* Price */}
              <div className="col-span-2 text-right">
                <div className="font-semibold text-white">
                  ${stock.price.toFixed(2)}
                </div>
              </div>

              {/* Change */}
              <div className="col-span-2 text-right">
                <div className={`font-medium ${stock.isPositive ? 'text-green-400' : 'text-red-400'}`}>
                  {stock.isPositive ? '+' : ''}{stock.change.toFixed(2)}
                </div>
                <div className={`text-sm ${stock.isPositive ? 'text-green-400' : 'text-red-400'}`}>
                  {stock.isPositive ? '+' : ''}{stock.change_percent.toFixed(2)}%
                </div>
              </div>

              {/* Volume */}
              <div className="col-span-2 text-right">
                <div className="text-slate-300">
                  {formatNumber(stock.volume, 0)}
                </div>
              </div>

              {/* Status */}
              <div className="col-span-2 text-right">
                <div className="flex items-center justify-end gap-2">
                  {stock.isRealtime && (
                    <span className="text-xs px-2 py-1 bg-green-500/20 text-green-400 rounded">
                      Live
                    </span>
                  )}
                  <button
                    className="text-slate-400 hover:text-red-400 transition-colors"
                    title="Remove from portfolio"
                    onClick={() => {
                      if (confirm(`Remove ${stock.symbol} from your portfolio tracking?`)) {
                        // In real app, this would call API to unfollow
                        alert(`${stock.symbol} removed from portfolio tracking (demo)`)
                      }
                    }}
                  >
                    ×
                  </button>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Footer Stats */}
      {sortedStocks.length > 0 && (
        <div className="mt-6 pt-4 border-t border-slate-700 flex items-center justify-between text-sm text-slate-400">
          <span>
            Showing {sortedStocks.length} of {enhancedStocks.length} stocks
          </span>
          <span>
            {enhancedStocks.filter(s => s.isRealtime).length} with live data
          </span>
        </div>
      )}
    </div>
  )
}