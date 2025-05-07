// src/app/[investing]/components/FollowedStocks.tsx
"use client";

import { useState, useEffect } from "react";
import { getStockDetails, unfollowStock } from "@/lib/api";

// 添加类型定义
interface FollowedStock {
  id: string;
  user_id: string;
  symbol: string;
  asset_type: string;
  name?: string;
  notes?: string;
  added_at: string;
}

interface StockData {
  symbol: string;
  name: string;
  price: number;
  change: number;
  change_percent: number;
  [key: string]: any;
}

interface FollowedStocksProps {
  followed: FollowedStock[];
  setFollowed: React.Dispatch<React.SetStateAction<FollowedStock[]>>;
  loading: boolean;
}

export default function FollowedStocks({ followed, setFollowed, loading }: FollowedStocksProps) {
  const [stocksData, setStocksData] = useState<Record<string, StockData>>({});

  // 加载关注股票的最新数据
  useEffect(() => {
    if (followed.length === 0) return;

    const fetchStocksData = async () => {
      try {
        // 创建股票数据请求
        const promises = followed.map(item => 
          getStockDetails(item.symbol)
            .catch(err => {
              console.error(`获取${item.symbol}数据失败:`, err);
              return null;
            })
        );

        const results = await Promise.all(promises);
        
        // 处理结果
        const newStocksData: Record<string, StockData> = {};
        results.forEach((result, index) => {
          if (result) {
            newStocksData[followed[index].symbol] = result;
          }
        });

        setStocksData(newStocksData);
      } catch (error) {
        console.error("获取股票数据失败:", error);
      }
    };

    fetchStocksData();

    // 设置定时刷新（每分钟更新一次）
    const intervalId = setInterval(fetchStocksData, 60000);
    return () => clearInterval(intervalId);
  }, [followed]);

  // 取消关注处理函数
  const handleUnfollow = async (id: string) => {
    try {
      await unfollowStock(id);
      // 更新关注列表
      setFollowed(followed.filter(item => item.id !== id));
    } catch (error: unknown) {
      console.error("取消关注失败:", error);
      alert("取消关注失败: " + ((error as any).response?.data?.detail || "请稍后再试"));
    }
  };

  if (loading) {
    return <div className="flex justify-center p-6"><div className="animate-spin h-8 w-8 border-4 border-blue-500 rounded-full border-t-transparent"></div></div>;
  }

  if (followed.length === 0) {
    return <div className="text-center py-8 text-gray-500">您还没有关注任何股票。使用上方搜索添加关注。</div>;
  }

  return (
    <div>
      <h2 className="text-lg font-semibold mb-4">我的关注</h2>
      <div className="overflow-x-auto">
        <table className="w-full text-sm text-left">
          <thead className="text-xs text-gray-700 uppercase bg-gray-100 dark:bg-gray-700 dark:text-gray-300">
            <tr>
              <th className="px-4 py-2">代码</th>
              <th className="px-4 py-2">名称</th>
              <th className="px-4 py-2">最新价格</th>
              <th className="px-4 py-2">涨跌幅</th>
              <th className="px-4 py-2">操作</th>
            </tr>
          </thead>
          <tbody>
            {followed.map((item) => {
              const stockData = stocksData[item.symbol] || {};
              const priceChangePercent = stockData.change_percent || 0;
              
              return (
                <tr key={item.id} className="border-b dark:border-gray-700">
                  <td className="px-4 py-3 font-medium">{item.symbol}</td>
                  <td className="px-4 py-3">{item.name}</td>
                  <td className="px-4 py-3">
                    ${stockData.price ? stockData.price.toFixed(2) : "加载中..."}
                  </td>
                  <td className={`px-4 py-3 ${priceChangePercent >= 0 ? 'text-green-600' : 'text-red-500'}`}>
                    {priceChangePercent >= 0 ? "+" : ""}
                    {priceChangePercent ? priceChangePercent.toFixed(2) : "0.00"}%
                  </td>
                  <td className="px-4 py-3">
                    <button
                      onClick={() => handleUnfollow(item.id)}
                      className="text-red-500 hover:text-red-700"
                    >
                      取消关注
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}