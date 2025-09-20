"use client"

import { useState, useEffect } from 'react'
import { useDashboardData } from '../hooks/useApiData'

export default function PortfolioOverview() {
  const { data: dashboardData, loading } = useDashboardData()
  
  // Calculate portfolio statistics
  const stats = {
    totalFollowed: dashboardData?.followed_stocks?.length || 0,
    gainers: 0,
    losers: 0,
    avgChange: 0,
    totalValue: 0,
    topPerformer: null as any,
    worstPerformer: null as any
  }

  if (dashboardData?.followed_stocks) {
    const stocks = dashboardData.followed_stocks
    
    stats.gainers = stocks.filter(stock => stock.change >= 0).length
    stats.losers = stocks.filter(stock => stock.change < 0).length
    
    if (stocks.length > 0) {
      stats.avgChange = stocks.reduce((sum, stock) => sum + (stock.change_percent || 0), 0) / stocks.length
      stats.totalValue = stocks.reduce((sum, stock) => sum + (stock.price * 100), 0) // Assume 100 shares each for demo
      
      // Find top and worst performers
      const sortedByChange = [...stocks].sort((a, b) => (b.change_percent || 0) - (a.change_percent || 0))
      stats.topPerformer = sortedByChange[0]
      stats.worstPerformer = sortedByChange[sortedByChange.length - 1]
    }
  }

  const StatCard = ({ title, value, subtitle, trend, icon, color = "blue" }: {
    title: string
    value: string | number
    subtitle?: string
    trend?: "up" | "down" | "neutral"
    icon: string
    color?: "blue" | "green" | "red" | "yellow" | "purple"
  }) => {
    const colorClasses = {
      blue: "border-blue-500/20 bg-blue-500/10",
      green: "border-green-500/20 bg-green-500/10", 
      red: "border-red-500/20 bg-red-500/10",
      yellow: "border-yellow-500/20 bg-yellow-500/10",
      purple: "border-purple-500/20 bg-purple-500/10"
    }

    const trendIcon = trend === "up" ? "📈" : trend === "down" ? "📉" : "📊"
    const trendColor = trend === "up" ? "text-green-400" : trend === "down" ? "text-red-400" : "text-slate-400"

    return (
      <div className={`p-6 rounded-xl border ${colorClasses[color]} backdrop-blur-sm`}>
        <div className="flex items-center justify-between mb-4">
          <div className="text-2xl">{icon}</div>
          {trend && (
            <div className={`text-lg ${trendColor}`}>
              {trendIcon}
            </div>
          )}
        </div>
        <div className="space-y-1">
          <p className="text-2xl font-bold text-white">{value}</p>
          <p className="text-sm font-medium text-slate-300">{title}</p>
          {subtitle && (
            <p className="text-xs text-slate-400">{subtitle}</p>
          )}
        </div>
      </div>
    )
  }

  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="animate-pulse">
            <div className="p-6 rounded-xl border border-slate-700 bg-slate-800">
              <div className="h-8 bg-slate-700 rounded mb-4"></div>
              <div className="h-6 bg-slate-700 rounded w-2/3 mb-2"></div>
              <div className="h-4 bg-slate-700 rounded w-1/2"></div>
            </div>
          </div>
        ))}
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Main Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Followed Stocks"
          value={stats.totalFollowed}
          subtitle={`${stats.gainers} gaining, ${stats.losers} declining`}
          icon="📊"
          color="blue"
        />
        
        <StatCard
          title="Average Change"
          value={`${stats.avgChange >= 0 ? '+' : ''}${stats.avgChange.toFixed(2)}%`}
          subtitle="Across all followed stocks"
          trend={stats.avgChange > 0 ? "up" : stats.avgChange < 0 ? "down" : "neutral"}
          icon="📈"
          color={stats.avgChange > 0 ? "green" : stats.avgChange < 0 ? "red" : "blue"}
        />
        
        <StatCard
          title="Portfolio Value"
          value={`$${stats.totalValue.toLocaleString()}`}
          subtitle="Hypothetical value (100 shares each)"
          icon="💰"
          color="yellow"
        />
        
        <StatCard
          title="Today's Gainers"
          value={stats.gainers}
          subtitle={`${((stats.gainers / Math.max(stats.totalFollowed, 1)) * 100).toFixed(0)}% of portfolio`}
          trend="up"
          icon="🚀"
          color="green"
        />
      </div>

      {/* Performance Highlights */}
      {stats.topPerformer && stats.worstPerformer && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="p-6 rounded-xl border border-green-500/20 bg-green-500/10">
            <div className="flex items-center gap-3 mb-4">
              <span className="text-2xl">🏆</span>
              <h3 className="text-lg font-semibold text-white">Top Performer</h3>
            </div>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="font-medium text-white">{stats.topPerformer.symbol}</span>
                <span className="text-green-400 font-bold">
                  +{stats.topPerformer.change_percent?.toFixed(2)}%
                </span>
              </div>
              <p className="text-sm text-slate-300">{stats.topPerformer.name}</p>
              <p className="text-lg font-bold text-white">${stats.topPerformer.price?.toFixed(2)}</p>
            </div>
          </div>

          <div className="p-6 rounded-xl border border-red-500/20 bg-red-500/10">
            <div className="flex items-center gap-3 mb-4">
              <span className="text-2xl">📉</span>
              <h3 className="text-lg font-semibold text-white">Needs Attention</h3>
            </div>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="font-medium text-white">{stats.worstPerformer.symbol}</span>
                <span className="text-red-400 font-bold">
                  {stats.worstPerformer.change_percent?.toFixed(2)}%
                </span>
              </div>
              <p className="text-sm text-slate-300">{stats.worstPerformer.name}</p>
              <p className="text-lg font-bold text-white">${stats.worstPerformer.price?.toFixed(2)}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}