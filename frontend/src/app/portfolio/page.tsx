"use client"

import { useState, useEffect } from 'react'
import Header from '../components/Header'
import PortfolioOverview from '../components/PortfolioOverview'
import FollowedStocksList from '../components/FollowedStocksList'
import PortfolioAnalytics from '../components/PortfolioAnalytics'
import StockSearch from '../components/StockSearch'

export default function PortfolioPage() {
  const username = 'Alex' // In real app, this would come from auth context

  const handleSelectStock = async (stock: any) => {
    console.log('Selected stock to follow:', stock)
    
    // For demo purposes, just show a success message
    alert(`✅ Stock ${stock.symbol} (${stock.name}) added to your portfolio tracking!\n\nPrice: $${stock.price}\nChange: ${stock.change >= 0 ? '+' : ''}${stock.change} (${stock.change_percent}%)\n\nNote: This is a demo. In the full version, this would be saved to your user profile.`)
  }

  return (
    <div className="relative flex min-h-screen flex-col bg-slate-900 text-slate-200" style={{fontFamily: 'Inter, "Noto Sans", sans-serif'}}>
      <Header username={username} />
      
      {/* Main Content */}
      <div className="px-6 lg:px-10 xl:px-20 flex flex-1 justify-center py-8">
        <div className="flex flex-col max-w-7xl flex-1 gap-8">
          {/* Page Header */}
          <div className="flex flex-col gap-4">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-4xl font-bold text-white">Portfolio Analytics</h1>
                <p className="text-slate-400 mt-2">Track and analyze your followed stocks performance</p>
              </div>
              <div className="flex items-center gap-3 text-sm text-slate-400">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-green-400"></div>
                  <span>Live Data</span>
                </div>
                <span>•</span>
                <span>Last updated: {new Date().toLocaleTimeString()}</span>
              </div>
            </div>
          </div>

          {/* Quick Stock Search */}
          <div className="bg-slate-800 border border-slate-700 rounded-xl p-6">
            <h2 className="text-xl font-semibold text-white mb-4">Add Stocks to Track</h2>
            <StockSearch 
              placeholder="Search and add stocks to your portfolio tracking..."
              onSelectStock={handleSelectStock}
            />
          </div>

          {/* Portfolio Overview Cards */}
          <PortfolioOverview />

          {/* Main Content Grid */}
          <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
            {/* Followed Stocks List */}
            <div className="xl:col-span-2">
              <FollowedStocksList />
            </div>
            
            {/* Analytics Panel */}
            <div className="xl:col-span-1">
              <PortfolioAnalytics />
            </div>
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