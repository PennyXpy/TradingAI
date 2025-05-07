// app/[username]/layout.tsx
"use client"

import { useEffect, useState } from "react"
import { useRouter, useParams } from "next/navigation"
import api from "@/lib/api"

export default function UserLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter()
  const params = useParams()
  const [isLoading, setIsLoading] = useState(true)
  
  useEffect(() => {
    // 验证用户是否已登录
    const token = localStorage.getItem("token")
    if (!token) {
      router.push("/")
      return
    }

    // 验证用户名是否匹配
    const validateUser = async () => {
      try {
        const response = await api.get("/auth/me")
        const currentUsername = response.data.username
        
        // 检查URL中的用户名是否与当前登录用户匹配
        if (currentUsername !== params.username) {
          router.push(`/${currentUsername}/dashboard`)
        }
        
        setIsLoading(false)
      } catch (error) {
        console.error("验证用户失败:", error)
        localStorage.removeItem("token")
        router.push("/")
      }
    }
    
    validateUser()
  }, [params.username, router])

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin h-10 w-10 border-4 border-blue-500 rounded-full border-t-transparent"></div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-100 dark:bg-gray-900">
      {children}
    </div>
  )
}