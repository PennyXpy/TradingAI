// src/app/[investing]/page.tsx
"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import { fetchFollowedStocks, fetchInvestments, followStock, addInvestment } from "@/lib/api";
import FollowedStocks from "./components/FollowedStocks";
import Investments from "./components/Investments";
import StockSearch from "./components/StockSearch";
import RelatedNews from "./components/RelatedNews";

// 类型定义
interface FollowedStock {
  id: string;
  user_id: string;
  symbol: string;
  asset_type: string;
  name?: string;
  notes?: string;
  added_at: string;
}

interface Investment {
  id: string;
  user_id: string;
  symbol: string;
  asset_type: string;
  quantity: number;
  price_per_unit: number;
  transaction_date: string;
  transaction_type: string;
  source: string;
  fees?: number;
  notes?: string;
  created_at: string;
  updated_at: string;
}

interface StockData {
  symbol: string;
  name: string;
  price: number;
  change?: number;
  change_percent?: number;
  [key: string]: any;
}

export default function InvestingPage() {
  const { username } = useParams<{username: string}>();
  const [activeTab, setActiveTab] = useState("followed"); // 'followed' 或 'invested'
  const [followed, setFollowed] = useState<FollowedStock[]>([]);
  const [investments, setInvestments] = useState<Investment[]>([]);
  const [loading, setLoading] = useState(true);

  // 加载用户的关注和投资数据
  useEffect(() => {
    const fetchUserData = async () => {
      setLoading(true);
      try {
        // 获取关注列表
        const followedData = await fetchFollowedStocks();
        setFollowed(followedData);

        // 获取投资列表
        const investmentsData = await fetchInvestments();
        setInvestments(investmentsData);
      } catch (error) {
        console.error("获取用户数据失败:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchUserData();
  }, []);

  // 添加到关注列表的处理函数
  const handleFollow = async (stockData: StockData) => {
    try {
      const response = await followStock({
        symbol: stockData.symbol,
        asset_type: "stock", // 默认为股票类型
        name: stockData.name
      });
      
      // 更新关注列表
      setFollowed([...followed, response]);
    } catch (error: unknown) {
      console.error("添加关注失败:", error);
      alert("添加关注失败: " + ((error as any).response?.data?.detail || "请稍后再试"));
    }
  };

  // 添加投资记录的处理函数
  const handleAddInvestment = async (investmentData: {
    symbol: string;
    quantity: number;
    price_per_unit: number;
    transaction_date: string;
    transaction_type: string;
    notes?: string;
  }) => {
    try {
      const response = await addInvestment({
        ...investmentData,
        asset_type: "stock" // 默认为股票类型
      });
      
      // 更新投资列表
      setInvestments([...investments, response]);
    } catch (error: unknown) {
      console.error("添加投资记录失败:", error);
      alert("添加投资记录失败: " + ((error as any).response?.data?.detail || "请稍后再试"));
    }
  };

  return (
    <div className="flex flex-col min-h-screen bg-gray-100 dark:bg-gray-900">
      <div className="container mx-auto p-4">
        <h1 className="text-2xl font-bold mb-6">投资组合管理</h1>
        
        {/* 标签切换 */}
        <div className="flex mb-6 bg-white dark:bg-gray-800 rounded-lg p-1 shadow">
          <button
            className={`flex-1 py-2 px-4 rounded-lg ${
              activeTab === "followed"
                ? "bg-blue-500 text-white"
                : "text-gray-700 dark:text-gray-300"
            }`}
            onClick={() => setActiveTab("followed")}
          >
            关注列表
          </button>
          <button
            className={`flex-1 py-2 px-4 rounded-lg ${
              activeTab === "invested"
                ? "bg-blue-500 text-white"
                : "text-gray-700 dark:text-gray-300"
            }`}
            onClick={() => setActiveTab("invested")}
          >
            投资记录
          </button>
        </div>

        {/* 主内容区 */}
        <div className="flex flex-col md:flex-row gap-6">
          {/* 左侧面板 */}
          <div className="md:w-2/3 space-y-6">
            {/* 搜索和添加部分 */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
              <h2 className="text-lg font-semibold mb-4">
                {activeTab === "followed" ? "添加关注" : "添加投资记录"}
              </h2>
              <StockSearch 
                onFollow={handleFollow} 
                onAddInvestment={handleAddInvestment}
                mode={activeTab}
              />
            </div>

            {/* 列表显示区域 */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
              {activeTab === "followed" ? (
                <FollowedStocks 
                  followed={followed} 
                  setFollowed={setFollowed}
                  loading={loading}
                />
              ) : (
                <Investments 
                  investments={investments} 
                  setInvestments={setInvestments}
                  loading={loading}
                />
              )}
            </div>
          </div>

          {/* 右侧新闻面板 */}
          <div className="md:w-1/3">
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
              <h2 className="text-lg font-semibold mb-4">相关财经新闻</h2>
              <RelatedNews 
                followedSymbols={followed.map(item => item.symbol)}
                investedSymbols={investments.map(item => item.symbol)}
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}