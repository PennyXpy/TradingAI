"use client"

import { useState } from 'react'

interface FollowedAsset {
  id: string
  symbol: string
  name: string
  type: 'stock' | 'etf' | 'crypto'
  price: number
  change: number
  changePercent: string
  isPositive: boolean
}

interface FollowedAssetCardProps {
  asset: FollowedAsset
  onViewDetails?: (asset: FollowedAsset) => void
}

export default function FollowedAssetCard({ asset, onViewDetails }: FollowedAssetCardProps) {
  const [isHovered, setIsHovered] = useState(false)

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'crypto':
        return 'text-yellow-400'
      case 'etf':
        return 'text-green-400'
      default:
        return 'text-[#1173d4]'
    }
  }

  const getHoverShadow = (isPositive: boolean) => {
    return isPositive ? 'hover:shadow-green-500/20' : 'hover:shadow-red-500/20'
  }

  return (
    <div 
      className={`relative group overflow-hidden rounded-xl bg-slate-800 border border-slate-700 p-5 transform transition-all duration-300 hover:scale-105 hover:shadow-2xl ${getHoverShadow(asset.isPositive)} cursor-pointer`}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {/* Change indicator in top right */}
      <div className={`absolute top-0 right-0 p-2 ${
        asset.isPositive ? 'bg-green-500/10 text-green-400' : 'bg-red-500/10 text-red-400'
      } rounded-bl-xl text-xs font-bold`}>
        {typeof asset.changePercent === 'string' ? asset.changePercent : `${asset.changePercent >= 0 ? '+' : ''}${asset.changePercent.toFixed(2)}%`}
      </div>
      
      <div className="flex flex-col gap-4">
        {/* Asset info */}
        <div className="flex items-center gap-3">
          <div className={`w-12 h-12 bg-slate-700 rounded-full flex items-center justify-center font-bold text-xl ${getTypeColor(asset.type)}`}>
            {asset.symbol.slice(0, 2).toUpperCase()}
          </div>
          <div>
            <h3 className="text-lg font-bold text-white">{asset.name}</h3>
            <p className="text-sm text-slate-400 capitalize">{asset.type}</p>
          </div>
        </div>
        
        {/* Price info */}
        <div>
          <p className="text-3xl font-black tracking-tighter text-white">
            ${asset.type === 'crypto' ? asset.price.toLocaleString() : asset.price.toFixed(2)}
          </p>
          <p className={`text-sm font-semibold ${
            asset.isPositive ? 'text-green-400' : 'text-red-400'
          }`}>
            {asset.isPositive ? '+' : ''}${Math.abs(asset.change).toFixed(2)}
          </p>
        </div>
      </div>
      
      {/* Hover overlay with action button */}
      <div className={`absolute inset-0 bg-gradient-to-t from-slate-900/80 to-transparent transition-opacity duration-300 flex items-center justify-center ${
        isHovered ? 'opacity-100' : 'opacity-0'
      }`}>
        <button 
          onClick={() => onViewDetails?.(asset)}
          className="px-4 py-2 bg-[#1173d4] text-white rounded-full text-sm font-semibold hover:bg-[#0f5aa3] transition-colors"
        >
          View Details
        </button>
      </div>
    </div>
  )
}