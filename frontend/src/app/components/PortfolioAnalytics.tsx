"use client"

import { useState, useEffect } from 'react'
import { useDashboardData, useLatestNews } from '../hooks/useApiData'

export default function PortfolioAnalytics() {
  const { data: dashboardData, loading: stocksLoading } = useDashboardData()
  const { data: newsData, loading: newsLoading } = useLatestNews(3)
  
  const [activeTab, setActiveTab] = useState<'overview' | 'sectors' | 'alerts' | 'news'>('overview')

  // Calculate analytics
  const analytics = {
    sectorBreakdown: {} as Record<string, { count: number, avgChange: number }>,
    riskLevel: 'Medium' as 'Low' | 'Medium' | 'High',
    diversificationScore: 0,
    recommendations: [] as string[]
  }

  if (dashboardData?.followed_stocks) {
    const stocks = dashboardData.followed_stocks
    
    // Simple sector classification (in real app, this would come from API)
    const sectorMap: Record<string, string> = {
      'AAPL': 'Technology', 'GOOGL': 'Technology', 'MSFT': 'Technology',
      'TSLA': 'Automotive', 'NVDA': 'Technology', 'AMD': 'Technology',
      'META': 'Technology', 'AMZN': 'E-commerce', 'NFLX': 'Entertainment',
      'CRM': 'Technology'
    }

    stocks.forEach(stock => {
      const sector = sectorMap[stock.symbol] || 'Other'
      if (!analytics.sectorBreakdown[sector]) {
        analytics.sectorBreakdown[sector] = { count: 0, avgChange: 0 }
      }
      analytics.sectorBreakdown[sector].count++
      analytics.sectorBreakdown[sector].avgChange += stock.change_percent || 0
    })

    // Calculate average changes
    Object.keys(analytics.sectorBreakdown).forEach(sector => {
      analytics.sectorBreakdown[sector].avgChange /= analytics.sectorBreakdown[sector].count
    })

    // Calculate diversification score (0-100)
    const sectorCount = Object.keys(analytics.sectorBreakdown).length
    analytics.diversificationScore = Math.min(100, (sectorCount / 5) * 100)

    // Risk level based on volatility
    const avgVolatility = stocks.reduce((sum, stock) => sum + Math.abs(stock.change_percent || 0), 0) / stocks.length
    analytics.riskLevel = avgVolatility > 3 ? 'High' : avgVolatility > 1.5 ? 'Medium' : 'Low'

    // Generate recommendations
    if (sectorCount === 1) {
      analytics.recommendations.push('Consider diversifying across different sectors')
    }
    if (stocks.filter(s => s.change < 0).length > stocks.length * 0.6) {
      analytics.recommendations.push('Review underperforming stocks')
    }
    if (analytics.diversificationScore < 50) {
      analytics.recommendations.push('Add more stocks from different sectors')
    }
  }

  const TabButton = ({ tab, children, count }: { tab: typeof activeTab, children: React.ReactNode, count?: number }) => (
    <button
      onClick={() => setActiveTab(tab)}
      className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors relative ${
        activeTab === tab
          ? 'bg-[#1173d4] text-white'
          : 'text-slate-300 hover:text-white hover:bg-slate-700'
      }`}
    >
      {children}
      {count !== undefined && count > 0 && (
        <span className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 text-white text-xs rounded-full flex items-center justify-center">
          {count}
        </span>
      )}
    </button>
  )

  const SectorChart = () => {
    const sectors = Object.entries(analytics.sectorBreakdown)
    const total = sectors.reduce((sum, [, data]) => sum + data.count, 0)

    return (
      <div className="space-y-3">
        {sectors.map(([sector, data]) => {
          const percentage = (data.count / total) * 100
          const isPositive = data.avgChange >= 0
          
          return (
            <div key={sector} className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className="text-white font-medium">{sector}</span>
                <div className="flex items-center gap-2">
                  <span className="text-slate-400">{data.count} stocks</span>
                  <span className={`font-medium ${isPositive ? 'text-green-400' : 'text-red-400'}`}>
                    {isPositive ? '+' : ''}{data.avgChange.toFixed(1)}%
                  </span>
                </div>
              </div>
              <div className="w-full bg-slate-700 rounded-full h-2">
                <div 
                  className={`h-2 rounded-full ${isPositive ? 'bg-green-500' : 'bg-red-500'}`}
                  style={{ width: `${percentage}%` }}
                ></div>
              </div>
            </div>
          )
        })}
      </div>
    )
  }

  const RiskIndicator = () => {
    const riskColors = {
      Low: 'text-green-400 bg-green-500/20',
      Medium: 'text-yellow-400 bg-yellow-500/20', 
      High: 'text-red-400 bg-red-500/20'
    }

    return (
      <div className={`px-3 py-1 rounded-full text-sm font-medium ${riskColors[analytics.riskLevel]}`}>
        {analytics.riskLevel} Risk
      </div>
    )
  }

  return (
    <div className="bg-slate-800 border border-slate-700 rounded-xl p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold text-white">Analytics</h2>
        <RiskIndicator />
      </div>

      {/* Tab Navigation */}
      <div className="flex gap-2 mb-6 p-1 bg-slate-700 rounded-lg">
        <TabButton tab="overview">Overview</TabButton>
        <TabButton tab="sectors">Sectors</TabButton>
        <TabButton tab="alerts" count={analytics.recommendations.length}>Alerts</TabButton>
        <TabButton tab="news">News</TabButton>
      </div>

      {/* Tab Content */}
      <div className="space-y-6">
        {activeTab === 'overview' && (
          <div className="space-y-6">
            {/* Diversification Score */}
            <div>
              <div className="flex items-center justify-between mb-3">
                <span className="text-sm font-medium text-slate-300">Diversification Score</span>
                <span className="text-white font-bold">{analytics.diversificationScore.toFixed(0)}/100</span>
              </div>
              <div className="w-full bg-slate-700 rounded-full h-3">
                <div 
                  className="h-3 rounded-full bg-gradient-to-r from-red-500 via-yellow-500 to-green-500"
                  style={{ width: `${analytics.diversificationScore}%` }}
                ></div>
              </div>
              <p className="text-xs text-slate-400 mt-2">
                {analytics.diversificationScore >= 80 ? 'Excellent diversification' :
                 analytics.diversificationScore >= 60 ? 'Good diversification' :
                 analytics.diversificationScore >= 40 ? 'Moderate diversification' :
                 'Poor diversification - consider adding more sectors'}
              </p>
            </div>

            {/* Quick Stats */}
            <div className="grid grid-cols-2 gap-4">
              <div className="p-4 bg-slate-700 rounded-lg">
                <div className="text-2xl font-bold text-white">
                  {Object.keys(analytics.sectorBreakdown).length}
                </div>
                <div className="text-sm text-slate-400">Sectors</div>
              </div>
              <div className="p-4 bg-slate-700 rounded-lg">
                <div className="text-2xl font-bold text-white">
                  {dashboardData?.followed_stocks?.length || 0}
                </div>
                <div className="text-sm text-slate-400">Stocks</div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'sectors' && (
          <div>
            <div className="mb-4">
              <h3 className="text-lg font-semibold text-white mb-2">Sector Breakdown</h3>
              <p className="text-sm text-slate-400">Distribution of your followed stocks by sector</p>
            </div>
            {Object.keys(analytics.sectorBreakdown).length > 0 ? (
              <SectorChart />
            ) : (
              <div className="text-center py-8">
                <div className="text-3xl mb-2">📊</div>
                <p className="text-slate-400">No sector data available</p>
              </div>
            )}
          </div>
        )}

        {activeTab === 'alerts' && (
          <div>
            <div className="mb-4">
              <h3 className="text-lg font-semibold text-white mb-2">Recommendations</h3>
              <p className="text-sm text-slate-400">Insights to optimize your portfolio</p>
            </div>
            {analytics.recommendations.length > 0 ? (
              <div className="space-y-3">
                {analytics.recommendations.map((rec, index) => (
                  <div key={index} className="flex items-start gap-3 p-3 bg-yellow-500/10 border border-yellow-500/20 rounded-lg">
                    <span className="text-yellow-400 mt-0.5">⚠️</span>
                    <span className="text-sm text-white">{rec}</span>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8">
                <div className="text-3xl mb-2">✅</div>
                <p className="text-green-400 font-medium">Portfolio looks good!</p>
                <p className="text-sm text-slate-400 mt-1">No recommendations at this time</p>
              </div>
            )}
          </div>
        )}

        {activeTab === 'news' && (
          <div>
            <div className="mb-4">
              <h3 className="text-lg font-semibold text-white mb-2">Market News</h3>
              <p className="text-sm text-slate-400">Latest news that might affect your portfolio</p>
            </div>
            {newsLoading ? (
              <div className="space-y-3">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="animate-pulse p-3 bg-slate-700 rounded-lg">
                    <div className="h-4 bg-slate-600 rounded w-3/4 mb-2"></div>
                    <div className="h-3 bg-slate-600 rounded w-1/2"></div>
                  </div>
                ))}
              </div>
            ) : newsData?.news ? (
              <div className="space-y-3">
                {newsData.news.map((article, index) => (
                  <div key={index} className="p-3 bg-slate-700 rounded-lg hover:bg-slate-600 transition-colors">
                    <div className="text-sm font-medium text-white mb-1 line-clamp-2">
                      {article.title}
                    </div>
                    <div className="flex items-center justify-between text-xs text-slate-400">
                      <span>{article.source}</span>
                      <span className={`px-2 py-1 rounded ${
                        article.sentiment > 0.1 ? 'bg-green-500/20 text-green-400' :
                        article.sentiment < -0.1 ? 'bg-red-500/20 text-red-400' :
                        'bg-gray-500/20 text-gray-400'
                      }`}>
                        {article.sentiment > 0.1 ? 'Positive' :
                         article.sentiment < -0.1 ? 'Negative' : 'Neutral'}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8">
                <div className="text-3xl mb-2">📰</div>
                <p className="text-slate-400">No news available</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}