"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import LoginForm from "./LoginForm"
import api from "@/lib/api"

export default function Home() {
  const router = useRouter()
  const [checking, setChecking] = useState(false)
  const [showLogin, setShowLogin] = useState(false)
  
  useEffect(() => {
    if (typeof window === 'undefined') return;
    
    const token = localStorage.getItem("token")
    if (!token) {
      setChecking(false)
      return
    }
    
    setChecking(true)
    
    const checkUser = async () => {
      try {
        const response = await api.get("/auth/me")
        const username = response.data.username
        router.push(`/${username}/dashboard`)
      } catch (error) {
        console.error("User check failed:", error)
        localStorage.removeItem("token")
        setChecking(false)
      }
    }
    
    checkUser()
  }, [router])

  if (checking) {
    return (
      <div className="flex items-center justify-center h-screen bg-slate-900">
        <div className="animate-spin h-10 w-10 border-4 border-[#1173d4] rounded-full border-t-transparent"></div>
      </div>
    )
  }

  if (showLogin) {
    return (
      <main className="flex min-h-screen flex-col items-center justify-center bg-slate-900">
        <div className="mb-8">
          <button 
            onClick={() => setShowLogin(false)}
            className="text-slate-400 hover:text-white transition-colors"
          >
            ← Back to Home
          </button>
        </div>
        <LoginForm />
      </main>
    )
  }

  return (
    <div className="min-h-screen bg-slate-900 text-white" style={{fontFamily: 'Inter, "Noto Sans", sans-serif'}}>
      {/* Header */}
      <header className="flex items-center justify-between px-10 py-4 border-b border-slate-800">
        <div className="flex items-center gap-3">
          <span className="text-[#1173d4] text-3xl">📈</span>
          <h1 className="text-xl font-bold">InvestSmart</h1>
        </div>
        <div className="flex items-center gap-4">
          <Link href="/main" className="text-slate-300 hover:text-white transition-colors">
            Explore Markets
          </Link>
          <button 
            onClick={() => setShowLogin(true)}
            className="px-4 py-2 bg-[#1173d4] text-white rounded-md hover:bg-[#0f5aa3] transition-colors font-medium"
          >
            Login
          </button>
        </div>
      </header>

      {/* Hero Section */}
      <main className="flex flex-col items-center justify-center px-10 py-20">
        <div className="text-center max-w-4xl mx-auto">
          <h1 className="text-6xl font-bold mb-6 bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
            Your AI-Powered Trading Assistant
          </h1>
          <p className="text-xl text-slate-300 mb-8 leading-relaxed">
            Make smarter investment decisions with real-time market data, AI-powered insights, 
            and personalized portfolio management.
          </p>
          <div className="flex gap-4 justify-center">
            <button 
              onClick={() => setShowLogin(true)}
              className="px-8 py-4 bg-[#1173d4] text-white rounded-lg hover:bg-[#0f5aa3] transition-colors font-semibold text-lg"
            >
              Get Started
            </button>
            <Link 
              href="/main"
              className="px-8 py-4 border border-slate-700 text-slate-300 rounded-lg hover:border-[#1173d4] hover:text-white transition-colors font-semibold text-lg"
            >
              Explore Markets
            </Link>
          </div>
        </div>

        {/* Features Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mt-20 max-w-6xl mx-auto">
          <div className="bg-slate-800 p-6 rounded-lg border border-slate-700">
            <div className="text-4xl mb-4">🤖</div>
            <h3 className="text-xl font-bold mb-2">AI Assistant</h3>
            <p className="text-slate-400">Get personalized investment insights and market analysis powered by advanced AI.</p>
          </div>
          <div className="bg-slate-800 p-6 rounded-lg border border-slate-700">
            <div className="text-4xl mb-4">📊</div>
            <h3 className="text-xl font-bold mb-2">Real-Time Data</h3>
            <p className="text-slate-400">Stay updated with live market data, news, and alerts for your followed assets.</p>
          </div>
          <div className="bg-slate-800 p-6 rounded-lg border border-slate-700">
            <div className="text-4xl mb-4">💼</div>
            <h3 className="text-xl font-bold mb-2">Portfolio Management</h3>
            <p className="text-slate-400">Track your investments and get analytics on your portfolio performance.</p>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800 py-8 px-10 mt-20">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-[#1173d4] text-2xl">📈</span>
            <span className="text-slate-400">InvestSmart © 2024</span>
          </div>
          <div className="flex gap-6 text-slate-400">
            <Link href="/about" className="hover:text-white transition-colors">About</Link>
            <Link href="/privacy" className="hover:text-white transition-colors">Privacy</Link>
            <Link href="/terms" className="hover:text-white transition-colors">Terms</Link>
          </div>
        </div>
      </footer>
    </div>
  )
}