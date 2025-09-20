"use client"

import { useState, useEffect, useRef } from 'react'
import { useStockSearch } from '../hooks/useApiData'

interface StockSearchProps {
  onSelectStock?: (stock: any) => void
  placeholder?: string
}

export default function StockSearch({ onSelectStock, placeholder = "Search stocks..." }: StockSearchProps) {
  const [query, setQuery] = useState('')
  const [isOpen, setIsOpen] = useState(false)
  const [selectedIndex, setSelectedIndex] = useState(-1)
  const searchRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  // Use debounced search
  const [debouncedQuery, setDebouncedQuery] = useState('')
  
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedQuery(query)
    }, 300) // 300ms debounce

    return () => clearTimeout(timer)
  }, [query])

  const { data: searchData, loading: searchLoading } = useStockSearch(debouncedQuery)
  const results = searchData?.results || []

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (searchRef.current && !searchRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  // Open dropdown when results are available
  useEffect(() => {
    if (results.length > 0 && query) {
      setIsOpen(true)
      setSelectedIndex(-1)
    } else {
      setIsOpen(false)
    }
  }, [results.length, query])

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setQuery(e.target.value)
    setSelectedIndex(-1)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!isOpen || results.length === 0) return

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault()
        setSelectedIndex(prev => (prev < results.length - 1 ? prev + 1 : 0))
        break
      case 'ArrowUp':
        e.preventDefault()
        setSelectedIndex(prev => (prev > 0 ? prev - 1 : results.length - 1))
        break
      case 'Enter':
        e.preventDefault()
        if (selectedIndex >= 0 && selectedIndex < results.length) {
          handleSelectStock(results[selectedIndex])
        }
        break
      case 'Escape':
        setIsOpen(false)
        setSelectedIndex(-1)
        inputRef.current?.blur()
        break
    }
  }

  const handleSelectStock = (stock: any) => {
    setQuery(stock.symbol)
    setIsOpen(false)
    setSelectedIndex(-1)
    onSelectStock?.(stock)
  }

  const formatPrice = (price: number) => {
    return price > 1000 ? price.toLocaleString() : price.toFixed(2)
  }

  const formatChange = (change: number, changePercent: number) => {
    const isPositive = change >= 0
    const sign = isPositive ? '+' : ''
    return {
      change: `${sign}$${Math.abs(change).toFixed(2)}`,
      percent: `${sign}${changePercent.toFixed(2)}%`,
      isPositive
    }
  }

  return (
    <div ref={searchRef} className="relative w-full">
      {/* Search Input */}
      <div className="relative">
        <div className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400">
          <span className="text-lg">🔍</span>
        </div>
        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          onFocus={() => query && results.length > 0 && setIsOpen(true)}
          className="w-full bg-slate-800 border border-slate-700 rounded-lg pl-10 pr-4 py-3 text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-[#1173d4] focus:border-[#1173d4]"
          placeholder={placeholder}
        />
        {searchLoading && (
          <div className="absolute right-3 top-1/2 -translate-y-1/2">
            <div className="w-4 h-4 border-2 border-[#1173d4] border-t-transparent rounded-full animate-spin"></div>
          </div>
        )}
      </div>

      {/* Search Results Dropdown */}
      {isOpen && (
        <div className="absolute top-full left-0 right-0 mt-1 bg-slate-800 border border-slate-700 rounded-lg shadow-xl z-50 max-h-80 overflow-y-auto">
          {results.length > 0 ? (
            <div className="py-2">
              {results.map((stock, index) => {
                const changeData = formatChange(stock.change || 0, stock.change_percent || 0)
                return (
                  <div
                    key={stock.symbol}
                    className={`px-4 py-3 cursor-pointer transition-colors ${
                      index === selectedIndex 
                        ? 'bg-[#1173d4] bg-opacity-20 border-l-4 border-[#1173d4]' 
                        : 'hover:bg-slate-700'
                    }`}
                    onClick={() => handleSelectStock(stock)}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 bg-slate-700 rounded-full flex items-center justify-center font-bold text-[#1173d4]">
                            {stock.symbol.slice(0, 2)}
                          </div>
                          <div>
                            <div className="font-medium text-white">{stock.symbol}</div>
                            <div className="text-sm text-slate-400 truncate max-w-48">
                              {stock.name}
                            </div>
                          </div>
                        </div>
                      </div>
                      
                      {stock.price > 0 && (
                        <div className="text-right">
                          <div className="font-semibold text-white">
                            ${formatPrice(stock.price)}
                          </div>
                          <div className={`text-sm ${changeData.isPositive ? 'text-green-400' : 'text-red-400'}`}>
                            {changeData.change} ({changeData.percent})
                          </div>
                        </div>
                      )}
                    </div>
                    
                    {stock.type && (
                      <div className="mt-1">
                        <span className="text-xs px-2 py-1 bg-slate-700 text-slate-300 rounded">
                          {stock.type}
                        </span>
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          ) : query && !searchLoading ? (
            <div className="px-4 py-6 text-center text-slate-400">
              <div className="text-2xl mb-2">📈</div>
              <div>No stocks found for "{query}"</div>
              <div className="text-sm mt-1">Try searching for a stock symbol like "AAPL" or company name</div>
            </div>
          ) : null}
        </div>
      )}
    </div>
  )
}