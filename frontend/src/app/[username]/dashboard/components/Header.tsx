// src/app/[username]/dashboard/components/Header.tsx
"use client";

import Link from "next/link";
import { useRouter, useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { getUserProfile } from "@/lib/api";

export default function Header() {
  const router = useRouter();
  const { username } = useParams<{username: string}>();
  const [userProfile, setUserProfile] = useState<{username: string} | null>(null);

  useEffect(() => {
    // 获取用户信息
    const fetchUserProfile = async () => {
      try {
        const profile = await getUserProfile();
        setUserProfile(profile);
      } catch (error) {
        console.error("获取用户信息失败", error);
      }
    };
    
    fetchUserProfile();
  }, []);

  const logout = () => {
    localStorage.removeItem("token");
    router.push("/");
  };

  return (
    <header className="w-full bg-blue-600 text-white px-6 py-3 flex items-center justify-between shadow">
      <div className="flex items-center space-x-4">
        <h1 className="text-xl font-bold">TradingAI</h1>
        
        {/* 主导航 */}
        <nav className="flex space-x-6 ml-8">
          <Link 
            href={`/${username}/dashboard`} 
            className="px-3 py-2 bg-blue-700 rounded"
          >
            仪表盘
          </Link>
          <Link 
            href={`/${username}/investment`} 
            className="px-3 py-2 rounded hover:bg-blue-700 transition-colors"
          >
            投资组合
          </Link>
        </nav>
      </div>
      
      {/* 用户区域 */}
      <div className="flex items-center space-x-4">
        {userProfile && (
          <div className="text-sm mr-4">
            欢迎, {userProfile.username}
          </div>
        )}
        <button
          onClick={logout}
          className="bg-blue-500 hover:bg-blue-700 px-4 py-1.5 rounded text-sm font-medium transition-colors"
        >
          退出登录
        </button>
      </div>
    </header>
  );
}