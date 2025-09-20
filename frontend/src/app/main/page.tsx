"use client"

import Link from 'next/link'
import Header from '../components/Header'
import { useTopStocks, useLatestNews } from '../hooks/useApiData'

// Mock data for top stocks & ETFs
const mockTopAssets = [
  {
    id: 1,
    name: "Tech Titans ETF",
    symbol: "TECH",
    category: "Technology",
    price: 150.25,
    change: 12.5,
    changePercent: "+12.5%",
    isPositive: true,
    chart: "M0 80C21.3333 80 21.3333 20 42.6667 20C64 20 64 40 85.3333 40C106.667 40 106.667 80 128 80C149.333 80 149.333 30 170.667 30C192 30 192 90 213.333 90C234.667 90 234.667 50 256 50C277.333 50 277.333 110 298.667 110C320 110 320 20 320 20"
  },
  {
    id: 2,
    name: "Green Energy ETF",
    symbol: "GREEN",
    category: "Renewable Energy", 
    price: 85.75,
    change: 8.2,
    changePercent: "+8.2%",
    isPositive: true,
    chart: "M0 90C21.3333 90 21.3333 40 42.6667 40C64 40 64 60 85.3333 60C106.667 60 106.667 100 128 100C149.333 100 149.333 50 170.667 50C192 50 192 110 213.333 110C234.667 110 234.667 70 256 70C277.333 70 277.333 120 298.667 120C320 120 320 40 320 40"
  },
  {
    id: 3,
    name: "Health Innovators ETF",
    symbol: "HEALTH",
    category: "Healthcare",
    price: 220.50,
    change: 15.8,
    changePercent: "+15.8%",
    isPositive: true,
    chart: "M0 40C21.3333 40 21.3333 90 42.6667 90C64 90 64 70 85.3333 70C106.667 70 106.667 20 128 20C149.333 20 149.333 80 170.667 80C192 80 192 30 213.333 30C234.667 30 234.667 100 256 100C277.333 100 277.333 50 298.667 50C320 50 320 110 320 110"
  }
]

const mockNews = [
  {
    id: 1,
    category: "Market Update",
    title: "Tech Sector Leads Market Rally",
    description: "The technology sector surged today, driven by strong earnings reports from major companies.",
    image: "/api/placeholder/400/200"
  },
  {
    id: 2,
    category: "Investment Insight",
    title: "Renewable Energy Investments on the Rise",
    description: "Investors are increasingly turning to renewable energy, with the Green Energy Leaders ETF showing promising growth.",
    image: "/api/placeholder/400/200"
  },
  {
    id: 3,
    category: "Healthcare News",
    title: "Healthcare Innovations Drive ETF Growth",
    description: "The Health Innovators ETF is benefiting from breakthroughs in medical technology and pharmaceuticals.",
    image: "/api/placeholder/400/200"
  },
  {
    id: 4,
    category: "Global Markets",
    title: "Global Markets Show Mixed Signals",
    description: "While some international markets are experiencing volatility, others are showing signs of recovery.",
    image: "/api/placeholder/400/200"
  },
  {
    id: 5,
    category: "Expert Analysis",
    title: "Expert Predicts Continued Growth in Tech",
    description: "Leading financial analysts predict that the technology sector will continue to outperform the market.",
    image: "/api/placeholder/400/200"
  },
  {
    id: 6,
    category: "Economy",
    title: "Inflation Concerns and a Volatile Market",
    description: "Inflation remains a key concern for investors, leading to increased market volatility in recent weeks.",
    image: "/api/placeholder/400/200"
  }
]

export default function MainPage() {
  const { data: stocksData, loading: stocksLoading } = useTopStocks(6)
  const { data: newsData, loading: newsLoading } = useLatestNews(6)

  return (
    <div className="relative flex min-h-screen flex-col bg-[#111a22]" style={{fontFamily: 'Inter, "Noto Sans", sans-serif'}}>
      <Header showAuth />

      {/* Main Content */}
      <main className="flex flex-1 gap-8 p-8">
        {/* Left Sidebar - Top Stocks & ETFs */}
        <div className="w-[380px] shrink-0 space-y-6 rounded-lg bg-[#18232f] p-6">
          <h2 className="text-white text-xl font-bold leading-tight">Top Stocks & ETFs</h2>
          <div className="space-y-4">
            {stocksLoading ? (
              // Loading skeleton
              [1,2,3,4,5,6].map((i) => (
                <div key={i} className="animate-pulse rounded-md border border-[#233648] bg-[#111a22] p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <div className="w-12 h-12 bg-slate-600 rounded-md"></div>
                      <div>
                        <div className="h-4 bg-slate-600 rounded w-24 mb-2"></div>
                        <div className="h-3 bg-slate-600 rounded w-16"></div>
                      </div>
                    </div>
                    <div className="h-4 bg-slate-600 rounded w-16"></div>
                  </div>
                  <div className="mt-4">
                    <div className="h-6 bg-slate-600 rounded w-20 mb-4"></div>
                    <div className="h-32 bg-slate-600 rounded"></div>
                  </div>
                </div>
              ))
            ) : stocksData?.stocks ? (
              stocksData.stocks.map((stock, index) => {
                const isPositive = (stock.change || 0) >= 0
                return (
                  <div key={stock.symbol} className="rounded-md border border-[#233648] bg-[#111a22] p-4 hover:bg-[#1a2332] transition-colors cursor-pointer">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-4">
                        <div className={`w-12 h-12 ${isPositive ? 'bg-gradient-to-r from-green-500 to-emerald-500' : 'bg-gradient-to-r from-red-500 to-pink-500'} rounded-md flex items-center justify-center text-white font-bold`}>
                          {stock.symbol.slice(0, 2)}
                        </div>
                        <div>
                          <p className="text-white font-semibold">{stock.symbol}</p>
                          <p className="text-sm text-[#92adc9] truncate max-w-32">{stock.name}</p>
                        </div>
                      </div>
                      <p className="text-lg font-semibold text-white">${stock.price?.toFixed(2) || '0.00'}</p>
                    </div>
                    <div className="mt-4">
                      <div className="flex items-baseline justify-between">
                        <p className={`text-2xl font-bold ${isPositive ? 'text-green-500' : 'text-red-500'}`}>
                          {isPositive ? '+' : ''}{stock.change_percent?.toFixed(2) || '0.00'}%
                        </p>
                        <p className="text-sm text-[#92adc9]">Daily Change</p>
                      </div>
                      <div className="mt-4 p-4 bg-slate-700/50 rounded-lg">
                        <div className="flex justify-between text-sm text-slate-400 mb-2">
                          <span>Volume: {stock.volume ? (stock.volume / 1000000).toFixed(1) + 'M' : 'N/A'}</span>
                          <span className={isPositive ? 'text-green-400' : 'text-red-400'}>
                            {isPositive ? '📈' : '📉'} Live
                          </span>
                        </div>
                        <div className="flex justify-between text-xs text-slate-500">
                          <span>High: ${stock.high?.toFixed(2) || 'N/A'}</span>
                          <span>Low: ${stock.low?.toFixed(2) || 'N/A'}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                )
              })
            ) : (
              <div className="text-center py-8">
                <div className="text-4xl mb-4">📊</div>
                <p className="text-slate-400">No stock data available</p>
              </div>
            )}
          </div>
        </div>

        {/* Right Content - Latest Financial News */}
        <div className="flex-1 space-y-6 rounded-lg bg-[#18232f] p-6">
          <div className="flex items-center justify-between">
            <h2 className="text-white text-xl font-bold leading-tight">Latest Financial News</h2>
            <Link href="/news" className="text-sm font-medium text-[#1173d4] hover:underline">
              View All
            </Link>
          </div>
          <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
            {newsLoading ? (
              // Loading skeleton for news
              [1,2,3,4,5,6].map((i) => (
                <div key={i} className="animate-pulse group flex flex-col overflow-hidden rounded-lg border border-[#233648] bg-[#111a22]">
                  <div className="h-40 w-full bg-slate-600"></div>
                  <div className="flex flex-1 flex-col p-4">
                    <div className="h-4 bg-slate-600 rounded w-20 mb-2"></div>
                    <div className="h-4 bg-slate-600 rounded w-full mb-2"></div>
                    <div className="h-3 bg-slate-600 rounded w-3/4 mb-2"></div>
                    <div className="h-3 bg-slate-600 rounded w-1/2"></div>
                  </div>
                </div>
              ))
            ) : newsData?.news ? (
              newsData.news.map((article, index) => (
                <div key={index} className="group flex flex-col overflow-hidden rounded-lg border border-[#233648] bg-[#111a22] hover:border-[#1173d4] transition-all cursor-pointer">
                  <div className="h-40 w-full overflow-hidden">
                    <div className="h-full w-full bg-gradient-to-br from-blue-600 to-purple-600 transition-transform duration-300 group-hover:scale-105 flex items-center justify-center text-white text-4xl">
                      📰
                    </div>
                  </div>
                  <div className="flex flex-1 flex-col p-4">
                    <p className="text-sm text-blue-400 font-medium">{article.source || 'Financial News'}</p>
                    <h3 className="mt-1 font-semibold text-white group-hover:text-[#1173d4] transition-colors line-clamp-2">{article.title}</h3>
                    <p className="mt-2 text-sm text-[#92adc9] line-clamp-3">{article.description || article.summary}</p>
                    <div className="mt-4 flex items-center justify-between">
                      <button className="text-sm font-medium text-[#1173d4] hover:underline text-left">
                        Read More →
                      </button>
                      {article.sentiment && (
                        <span className={`text-xs px-2 py-1 rounded ${
                          article.sentiment > 0.1 ? 'bg-green-500/20 text-green-400' :
                          article.sentiment < -0.1 ? 'bg-red-500/20 text-red-400' :
                          'bg-gray-500/20 text-gray-400'
                        }`}>
                          {article.sentiment > 0.1 ? 'Positive' :
                           article.sentiment < -0.1 ? 'Negative' : 'Neutral'}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <div className="col-span-full text-center py-8">
                <div className="text-4xl mb-4">📰</div>
                <p className="text-slate-400">No news available</p>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  )
}