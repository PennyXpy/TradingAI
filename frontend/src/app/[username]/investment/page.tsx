// src/app/[username]/investing/page.tsx
"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import { fetchFollowedStocks, fetchInvestments, followStock, addInvestment } from "@/lib/api";
import FollowedStocks from "./components/FollowedStocks";
import Investments from "./components/Investments";
import StockSearch from "./components/StockSearch";
import RelatedNews from "./components/RelatedNews";
import Header from "../dashboard/components/Header";

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
  
  // 搜索和添加的状态
  const [activeMode, setActiveMode] = useState<"follow" | "invest" | null>(null);
  const [followed, setFollowed] = useState<FollowedStock[]>([]);
  const [investments, setInvestments] = useState<Investment[]>([]);
  const [loading, setLoading] = useState(true);

  // 加载用户数据
  useEffect(() => {
    const fetchUserData = async () => {
      setLoading(true);
      try {
        // 并行加载数据
        const [followedData, investmentsData] = await Promise.all([
          fetchFollowedStocks(),
          fetchInvestments()
        ]);
        
        setFollowed(followedData);
        setInvestments(investmentsData);
      } catch (error) {
        console.error("获取用户数据失败:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchUserData();
  }, []);

  // 处理函数
  const handleFollow = async (stockData: StockData) => {
    try {
      const response = await followStock({
        symbol: stockData.symbol,
        asset_type: "stock",
        name: stockData.name
      });
      
      setFollowed([...followed, response]);
      setActiveMode(null); // 添加成功后关闭添加表单
    } catch (error: unknown) {
      console.error("添加关注失败:", error);
      alert("添加关注失败: " + ((error as any).response?.data?.detail || "请稍后再试"));
    }
  };

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
        asset_type: "stock"
      });
      
      setInvestments([...investments, response]);
      setActiveMode(null); // 添加成功后关闭添加表单
    } catch (error: unknown) {
      console.error("添加投资记录失败:", error);
      alert("添加投资记录失败: " + ((error as any).response?.data?.detail || "请稍后再试"));
    }
  };

  return (
    <div className="flex flex-col min-h-screen bg-gray-100 dark:bg-gray-900">
      <Header />
      
      {/* 修改：去除容器的padding限制，使用全宽布局 */}
      <div className="flex-1 w-full">
        <div className="p-4">
          <h1 className="text-2xl font-bold mb-6">投资组合管理</h1>
        </div>
        
        {/* 修改：强制使用左右布局，无论屏幕大小 */}
        <div className="flex w-full h-[calc(100vh-150px)]"> {/* 固定高度确保填满屏幕 */}
          {/* 左侧面板 - 强制1/3宽度 */}
          <div className="w-1/3 p-4 space-y-4 overflow-auto">
            {/* 投资记录部分 */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow mb-4">
              <div className="p-4 border-b border-gray-200 dark:border-gray-700 flex justify-between items-center">
                <h2 className="text-lg font-semibold">投资记录</h2>
                <button 
                  onClick={() => setActiveMode(activeMode === "invest" ? null : "invest")}
                  className="px-3 py-1 bg-blue-500 hover:bg-blue-600 text-white text-sm rounded"
                >
                  {activeMode === "invest" ? "取消" : "添加"}
                </button>
              </div>
              
              {/* 添加投资表单 */}
              {activeMode === "invest" && (
                <div className="p-4 bg-blue-50 dark:bg-gray-700">
                  <StockSearch 
                    onFollow={(stock: StockData) => Promise.resolve()} 
                    onAddInvestment={handleAddInvestment}
                    mode="invested"
                  />
                </div>
              )}
              
              {/* 投资列表 - 设置固定高度，保证视图整洁 */}
              <div className="p-4 max-h-60 overflow-auto">
                <Investments 
                  investments={investments} 
                  setInvestments={setInvestments}
                  loading={loading}
                />
              </div>
            </div>
            
            {/* 关注列表部分 */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
              <div className="p-4 border-b border-gray-200 dark:border-gray-700 flex justify-between items-center">
                <h2 className="text-lg font-semibold">关注列表</h2>
                <button 
                  onClick={() => setActiveMode(activeMode === "follow" ? null : "follow")}
                  className="px-3 py-1 bg-blue-500 hover:bg-blue-600 text-white text-sm rounded"
                >
                  {activeMode === "follow" ? "取消" : "添加"}
                </button>
              </div>
              
              {/* 添加关注表单 */}
              {activeMode === "follow" && (
                <div className="p-4 bg-blue-50 dark:bg-gray-700">
                  <StockSearch 
                    onFollow={handleFollow} 
                    onAddInvestment={(data: any) => Promise.resolve()}
                    mode="followed"
                  />
                </div>
              )}
              
              {/* 关注列表 - 设置固定高度 */}
              <div className="p-4 max-h-60 overflow-auto">
                <FollowedStocks 
                  followed={followed} 
                  setFollowed={setFollowed}
                  loading={loading}
                />
              </div>
            </div>
          </div>

          {/* 右侧新闻面板 - 强制2/3宽度 */}
          <div className="w-2/3 p-4 overflow-auto">
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4 h-full">
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