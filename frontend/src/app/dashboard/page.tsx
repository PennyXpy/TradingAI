"use client"

import { useState, useEffect } from 'react'
import Header from '../components/Header'
import FollowedAssetCard from '../components/FollowedAssetCard'
import StockSearch from '../components/StockSearch'
import AIAssistant from '../components/AIAssistant'
import { useDashboardData, useTopCryptos } from '../hooks/useApiData'
import { useRealtimeData } from '../hooks/useRealtimeData'

export default function DashboardPage() {
  const [searchQuery, setSearchQuery] = useState('')
  const username = 'Alex' // In real app, this would come from auth context

  // Fetch dashboard data (includes user's followed stocks + popular stocks)
  const { data: dashboardData, loading: dashboardLoading } = useDashboardData()
  const { data: cryptosData, loading: cryptosLoading } = useTopCryptos(2)
  
  // Get symbols for real-time data from followed stocks
  const stockSymbols = (dashboardData?.followed_stocks || []).map(s => s.symbol)
  const cryptoSymbols = (cryptosData?.cryptos || []).map(c => c.symbol)
  const symbols = [...stockSymbols, ...cryptoSymbols]
  
  // Connect to real-time WebSocket data
  const { data: realtimeData, isConnected } = useRealtimeData({ 
    symbols,
    enabled: symbols.length > 0 
  })

  // Transform API data to match our component interface
  const followedAssets = [
    // User's followed stocks from dashboard data (already enhanced with real-time data from backend)
    ...(dashboardData?.followed_stocks || []).map((stock: any) => ({
      id: stock.id,
      symbol: stock.symbol,
      name: stock.name,
      type: stock.type as const,
      price: realtimeData[stock.symbol]?.price || stock.price,
      change: realtimeData[stock.symbol]?.change || stock.change,
      changePercent: realtimeData[stock.symbol]?.change_percent || stock.change_percent,
      isPositive: (realtimeData[stock.symbol]?.change || stock.change) >= 0
    })),
    // Add some crypto data for variety
    ...(cryptosData?.cryptos || []).slice(0, 2).map((crypto: any) => ({
      id: crypto.symbol,
      symbol: crypto.symbol,
      name: crypto.name,
      type: 'crypto' as const,
      price: realtimeData[crypto.symbol]?.price || crypto.price,
      change: realtimeData[crypto.symbol]?.change || crypto.change,
      changePercent: realtimeData[crypto.symbol]?.change_percent || crypto.change_percent,
      isPositive: (realtimeData[crypto.symbol]?.change || crypto.change) >= 0
    }))
  ]

  // Count assets by type
  const assetCounts = followedAssets.reduce((acc, asset) => {
    if (asset.type === 'stock') acc.stocks += 1
    else if (asset.type === 'etf') acc.etfs += 1
    else if (asset.type === 'crypto') acc.cryptos += 1
    return acc
  }, { stocks: 0, etfs: 0, cryptos: 0 })

  const handleViewAssetDetails = (asset: any) => {
    console.log('View details for:', asset)
    // In real app, navigate to asset detail page
  }

  const handleSelectStock = async (stock: any) => {
    console.log('Selected stock to follow:', stock)
    
    // For demo purposes, just show a success message
    // In a real app with authentication, this would make an API call
    alert(`✅ Stock ${stock.symbol} (${stock.name}) added to your watchlist!\n\nPrice: $${stock.price}\nChange: ${stock.change >= 0 ? '+' : ''}${stock.change} (${stock.change_percent}%)\n\nNote: This is a demo. In the full version, this would be saved to your user profile.`)
  }

  return (
    <div className="relative flex min-h-screen flex-col bg-slate-900 text-slate-200" style={{fontFamily: 'Inter, "Noto Sans", sans-serif'}}>
      <Header username={username} />
      
      {/* Main Content */}
      <div className="px-10 lg:px-20 xl:px-40 flex flex-1 justify-center py-8">
        <div className="flex flex-col max-w-7xl flex-1 gap-8">
          {/* Welcome Section */}
          <div className="flex flex-col gap-2">
            <div className="flex items-center gap-4">
              <h1 className="text-4xl font-bold text-white">Welcome Back, {username}</h1>
              {/* Real-time connection indicator */}
              <div className="flex items-center gap-2">
                <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-400' : 'bg-red-400'}`}></div>
                <span className="text-sm text-slate-400">
                  {isConnected ? 'Live Data' : 'Offline'}
                </span>
              </div>
            </div>
            <p className="text-slate-400">Here's your personalized dashboard for today.</p>
          </div>
          
          {/* Stock Search */}
          <div className="px-4 py-3">
            <StockSearch 
              placeholder="Search and follow stocks (e.g., AAPL, GOOGL)..."
              onSelectStock={handleSelectStock}
            />
          </div>
          
          {/* Stats Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="flex flex-col gap-2 rounded-lg p-6 bg-slate-800 border border-slate-700 hover:border-[#1173d4] transition-colors">
              <p className="text-slate-400 text-sm font-medium">Followed Stocks</p>
              <p className="text-3xl font-bold text-white">{assetCounts.stocks}</p>
            </div>
            <div className="flex flex-col gap-2 rounded-lg p-6 bg-slate-800 border border-slate-700 hover:border-[#1173d4] transition-colors">
              <p className="text-slate-400 text-sm font-medium">Followed ETFs</p>
              <p className="text-3xl font-bold text-white">{assetCounts.etfs}</p>
            </div>
            <div className="flex flex-col gap-2 rounded-lg p-6 bg-slate-800 border border-slate-700 hover:border-[#1173d4] transition-colors">
              <p className="text-slate-400 text-sm font-medium">Followed Cryptos</p>
              <p className="text-3xl font-bold text-white">{assetCounts.cryptos}</p>
            </div>
          </div>
          
          {/* Main Content Grid */}
          <div className="grid grid-cols-1 xl:grid-cols-5 gap-8">
            {/* Followed Assets */}
            <div className="xl:col-span-3 flex flex-col gap-6">
              <h2 className="text-2xl font-bold leading-tight tracking-tight text-white">Your Followed Assets</h2>
              
              {/* Loading state */}
              {(dashboardLoading || cryptosLoading) ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {[1, 2, 3, 4, 5].map((i) => (
                    <div key={i} className="animate-pulse">
                      <div className="bg-slate-800 border border-slate-700 rounded-xl p-5 h-40">
                        <div className="h-4 bg-slate-700 rounded w-3/4 mb-4"></div>
                        <div className="h-6 bg-slate-700 rounded w-1/2 mb-2"></div>
                        <div className="h-8 bg-slate-700 rounded w-2/3"></div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {followedAssets.map((asset) => (
                    <FollowedAssetCard
                      key={asset.id}
                      asset={asset}
                      onViewDetails={handleViewAssetDetails}
                    />
                  ))}
                </div>
              )}
              
              {/* Add more assets button */}
              <div className="flex justify-center mt-4">
                <button className="px-6 py-3 bg-slate-800 border border-slate-700 hover:border-[#1173d4] rounded-lg text-white font-medium transition-colors hover:bg-slate-750">
                  + Follow More Assets
                </button>
              </div>
            </div>
            
            {/* AI Assistant */}
            <AIAssistant username={username} />
          </div>
        </div>
      </div>
      
      <style jsx>{`
        :root {
          --primary-500: #1173d4;
          --primary-400: #3b8fe9;
        }
      `}</style>
    </div>
  )
}