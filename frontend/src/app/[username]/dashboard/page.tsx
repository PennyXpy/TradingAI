// [username]/dashboard/page.tsx
"use client";

import { useEffect, useState } from "react";
import Header from "./components/Header";
import IndexGrid from "./components/IndexGrid";
import StockList from "./components/StockList";
import CryptoList from "./components/CryptoList";
import NewsList from "./components/NewsList";

export default function DashboardPage() {
  // 添加一个状态来防止过多重新渲染导致的API调用
  const [dataInitialized, setDataInitialized] = useState(false);

  useEffect(() => {
    // 仅在组件首次挂载时执行一次初始化
    if (!dataInitialized) {
      setDataInitialized(true);
    }
  }, [dataInitialized]);

  return (
    <div className="flex flex-col h-full">
      <Header />

      <div className="flex flex-1 p-4 gap-6 overflow-hidden">
        {/* 左列 */}
        <div className="w-1/3 flex flex-col gap-4">
          <IndexGrid />
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4 flex-1 overflow-auto">
            <h3 className="font-semibold mb-2">🔥 热门股票</h3>
            <StockList />
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4 flex-1 overflow-auto">
            <h3 className="font-semibold mb-2">💰 热门加密货币</h3>
            <CryptoList />
          </div>
        </div>

        {/* 右列 */}
        <div className="flex-1 bg-white dark:bg-gray-800 rounded-lg shadow p-4 overflow-y-auto">
          <h3 className="font-semibold mb-2">📰 最新财经新闻</h3>
          <NewsList />
        </div>
      </div>
    </div>
  );
}