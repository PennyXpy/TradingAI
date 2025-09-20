"use client"

import { useState } from 'react'
import Link from 'next/link'
import { useRouter, usePathname } from 'next/navigation'

interface HeaderProps {
  username?: string
  showAuth?: boolean
}

export default function Header({ username, showAuth = false }: HeaderProps) {
  const [searchQuery, setSearchQuery] = useState('')
  const router = useRouter()
  const pathname = usePathname()

  const handleLogout = () => {
    localStorage.removeItem('token')
    router.push('/')
  }

  const isActivePath = (path: string) => {
    return pathname.includes(path)
  }

  return (
    <header className="flex items-center justify-between whitespace-nowrap border-b border-solid border-b-[#233648] px-10 py-4 bg-[#111a22]">
      <div className="flex items-center gap-12">
        <Link href={username ? `/${username}/dashboard` : "/main"} className="flex items-center gap-3 text-white">
          <span className="text-[#1173d4] text-3xl">📈</span>
          <h2 className="text-white text-xl font-bold leading-tight tracking-[-0.015em]">InvestSmart</h2>
        </Link>
        
        <nav className="flex items-center gap-8">
          {username ? (
            <>
              <Link 
                href={`/${username}/dashboard`}
                className={`text-base font-medium leading-normal transition-colors ${
                  isActivePath('/dashboard') 
                    ? 'text-[#1173d4] relative' 
                    : 'text-white hover:text-[#1173d4]'
                }`}
              >
                Dashboard
                {isActivePath('/dashboard') && (
                  <div className="absolute bottom-[-6px] left-0 w-full h-0.5 bg-[#1173d4]"></div>
                )}
              </Link>
              <Link 
                href="/portfolio"
                className={`text-base font-medium leading-normal transition-colors ${
                  isActivePath('/portfolio') 
                    ? 'text-[#1173d4] relative' 
                    : 'text-white hover:text-[#1173d4]'
                }`}
              >
                Portfolio
                {isActivePath('/portfolio') && (
                  <div className="absolute bottom-[-6px] left-0 w-full h-0.5 bg-[#1173d4]"></div>
                )}
              </Link>
            </>
          ) : (
            <>
              <Link href="/dashboard" className="text-white text-base font-medium leading-normal hover:text-[#1173d4] transition-colors">
                Dashboard
              </Link>
              <Link 
                href="/main" 
                className={`text-base font-medium leading-normal transition-colors ${
                  isActivePath('/main') 
                    ? 'text-[#1173d4] relative' 
                    : 'text-white hover:text-[#1173d4]'
                }`}
              >
                Stocks & ETFs
                {isActivePath('/main') && (
                  <div className="absolute bottom-[-6px] left-0 w-full h-0.5 bg-[#1173d4]"></div>
                )}
              </Link>
              <Link href="/portfolio" className="text-white text-base font-medium leading-normal hover:text-[#1173d4] transition-colors">
                Portfolio
              </Link>
              <Link href="/news" className="text-white text-base font-medium leading-normal hover:text-[#1173d4] transition-colors">
                News
              </Link>
            </>
          )}
        </nav>
      </div>
      
      <div className="flex items-center gap-4">
        {!username && (
          <div className="relative">
            <span className="absolute left-3 top-1/2 -translate-y-1/2 text-[#92adc9] text-xl">🔍</span>
            <input 
              className="rounded-md border-none bg-[#233648] py-2 pl-10 pr-4 text-white placeholder:text-[#92adc9] focus:ring-2 focus:ring-inset focus:ring-[#1173d4] focus:outline-none" 
              placeholder="Search for stocks, ETFs, and more..." 
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
        )}
        
        <button className="relative rounded-md bg-[#233648] p-2 text-white hover:bg-[#2c4053] transition-colors">
          <span className="text-xl">🔔</span>
          <span className="absolute right-1 top-1 flex h-2 w-2">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-red-400 opacity-75"></span>
            <span className="relative inline-flex h-2 w-2 rounded-full bg-red-500"></span>
          </span>
        </button>
        
        {username ? (
          <div className="relative group">
            <button className="w-10 h-10 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full flex items-center justify-center text-white font-semibold hover:scale-105 transition-transform">
              {username.charAt(0).toUpperCase()}
            </button>
            <div className="absolute right-0 mt-2 w-48 bg-[#18232f] border border-[#233648] rounded-lg shadow-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-50">
              <div className="py-1">
                <Link href={`/${username}/profile`} className="block px-4 py-2 text-sm text-white hover:bg-[#233648] transition-colors">
                  Profile
                </Link>
                <Link href={`/${username}/settings`} className="block px-4 py-2 text-sm text-white hover:bg-[#233648] transition-colors">
                  Settings
                </Link>
                <button 
                  onClick={handleLogout}
                  className="block w-full text-left px-4 py-2 text-sm text-white hover:bg-[#233648] transition-colors"
                >
                  Logout
                </button>
              </div>
            </div>
          </div>
        ) : showAuth ? (
          <Link 
            href="/" 
            className="px-4 py-2 bg-[#1173d4] text-white rounded-md hover:bg-[#0f5aa3] transition-colors font-medium"
          >
            Login
          </Link>
        ) : (
          <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full flex items-center justify-center text-white font-semibold hover:scale-105 transition-transform">
            A
          </div>
        )}
      </div>
    </header>
  )
}