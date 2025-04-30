// ⚠️ 这是 *Client Component*（需要 hooks，所以 "use client"）
"use client";

import Header from "./components/Header";
import IndexGrid from "./components/IndexGrid";
import StockList from "./components/StockList";
import CryptoList from "./components/CryptoList";
import NewsList from "./components/NewsList";

export default function DashboardPage() {
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
