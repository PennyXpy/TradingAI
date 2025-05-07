// app/page.tsx
"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import LoginForm from "./LoginForm"
import api from "@/lib/api"

export default function Home() {
  const router = useRouter()
  // 修改初始状态：只有在客户端且有token时才为true
  const [checking, setChecking] = useState(false)
  
  useEffect(() => {
    // 添加服务器端渲染保护
    if (typeof window === 'undefined') {
      return;
    }
    
    // 检查用户是否已登录
    const token = localStorage.getItem("token")
    if (!token) {
      setChecking(false)
      return
    }
    
    // 设置checking状态为true，表示正在验证token
    setChecking(true)
    
    // 获取用户信息并重定向
    const checkUser = async () => {
      try {
        const response = await api.get("/auth/me")
        const username = response.data.username
        router.push(`/${username}/dashboard`)
      } catch (error) {
        console.error("获取用户信息失败:", error)
        localStorage.removeItem("token")
        setChecking(false)
      }
    }
    
    checkUser()
  }, [router])

  // 显示加载状态
  if (checking) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin h-10 w-10 border-4 border-blue-500 rounded-full border-t-transparent"></div>
      </div>
    )
  }

  // 显示登录表单
  return (
    <main className="flex min-h-screen flex-col items-center justify-center bg-gray-100 dark:bg-gray-900">
      <LoginForm />
    </main>
  )
}