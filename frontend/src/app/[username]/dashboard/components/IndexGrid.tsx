"use client";

import { useEffect, useState } from "react";
import api from "@/lib/api";
import MiniSparklines from "./MiniSparklines";

interface MarketIndex {
  symbol: string;
  name: string;
  price: number;
  change: number;
  change_percent: number;
  data?: number[];
  fallback?: boolean;
}

export default function IndexGrid() {
  const [indexes, setIndexes] = useState<MarketIndex[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        
        const response = await api.get("/market/indexes");
        
        if (isMounted) {
          setIndexes(response.data);
          setLoading(false);
        }
      } catch (err) {
        console.error("无法获取市场指数", err);
        if (isMounted) {
          setError("无法获取市场指数数据");
          setLoading(false);
        }
      }
    };

    fetchData();
    
    // 清理函数
    return () => {
      isMounted = false;
    };
  }, []); // 空依赖数组，只在组件挂载时执行一次

  if (loading) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4 h-40 flex items-center justify-center">
        <div className="animate-spin h-8 w-8 border-4 border-blue-500 rounded-full border-t-transparent"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4 h-40 flex items-center justify-center">
        <p className="text-red-500">{error}</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-3 gap-4 mb-4">
      {indexes.map((index) => (
        <div
          key={index.symbol}
          className="bg-white dark:bg-gray-800 rounded-lg shadow p-3 text-center relative"
        >
          {index.fallback && (
            <div className="absolute top-0 right-0 bg-yellow-500 text-xs text-white px-1 rounded-bl">
              缓存
            </div>
          )}
          <div className="font-semibold text-sm mb-1">{index.name}</div>
          <div className="text-lg font-bold mb-1">{index.price.toLocaleString()}</div>
          <div
            className={`text-sm flex items-center justify-center ${
              index.change >= 0 ? "text-green-500" : "text-red-500"
            }`}
          >
            <span>
              {index.change >= 0 ? "+" : ""}
              {index.change.toFixed(2)} ({index.change_percent.toFixed(2)}%)
            </span>
          </div>
          {index.data && <MiniSparklines data={index.data} positive={index.change_percent >= 0} />}
        </div>
      ))}
    </div>
  );
}