"use client";

import { useState } from "react";
import { searchStocks } from "@/lib/api";

// 添加类型定义
interface StockData {
  symbol: string;
  name: string;
  price: number;
  change?: number;
  change_percent?: number;
  [key: string]: any; // 允许其他属性
}

interface StockSearchProps {
  onFollow: (stock: StockData) => Promise<void>;
  onAddInvestment: (data: any) => Promise<void>;
  mode: string;
}

export default function StockSearch({ onFollow, onAddInvestment, mode }: StockSearchProps) {
  const [searchTerm, setSearchTerm] = useState("");
  const [searchResults, setSearchResults] = useState<StockData[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedStock, setSelectedStock] = useState<StockData | null>(null);
  
  // 添加Robinhood选项
  const [dataSource, setDataSource] = useState("manual"); // "manual" 或 "robinhood"
  
  // 投资表单状态
  const [quantity, setQuantity] = useState<number>(1);
  const [price, setPrice] = useState<number>(0);
  const [transactionType, setTransactionType] = useState("buy");
  const [transactionDate, setTransactionDate] = useState(
    new Date().toISOString().split("T")[0]
  );

  // 搜索股票
  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchTerm.trim()) return;

    setLoading(true);
    try {
      const results = await searchStocks(searchTerm);
      setSearchResults(results);
    } catch (error: unknown) {
      console.error("搜索股票失败:", error);
      alert("搜索失败: " + ((error as any).response?.data?.detail || "请稍后再试"));
    } finally {
      setLoading(false);
    }
  };

  // 选择股票
  const handleSelectStock = async (stock: StockData) => {
    setSelectedStock(stock);
    if (mode === "invested" && stock.price) {
      setPrice(stock.price);
    }
  };

  // 添加到关注列表
  const handleFollow = () => {
    if (!selectedStock) return;
    onFollow(selectedStock);
    resetForm();
  };

  // 添加投资记录
  const handleAddInvestment = (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedStock) return;

    const investmentData = {
      symbol: selectedStock.symbol,
      quantity: parseFloat(quantity.toString()),
      price_per_unit: parseFloat(price.toString()),
      transaction_date: new Date(transactionDate).toISOString(),
      transaction_type: transactionType,
      notes: ""
    };

    onAddInvestment(investmentData);
    resetForm();
  };

  // 重置表单
  const resetForm = () => {
    setSearchTerm("");
    setSearchResults([]);
    setSelectedStock(null);
    setQuantity(1);
    setPrice(0);
    setTransactionDate(new Date().toISOString().split("T")[0]);
    setTransactionType("buy");
  };

  return (
    <div>
      {/* 添加Robinhood选项，只在投资模式下显示 */}
      {mode === "invested" && (
        <div className="mb-4">
          <label className="block text-sm font-medium mb-1">数据来源</label>
          <div className="flex space-x-4">
            <label className="flex items-center">
              <input
                type="radio"
                value="manual"
                checked={dataSource === "manual"}
                onChange={() => setDataSource("manual")}
                className="mr-2"
              />
              手动输入
            </label>
            <label className="flex items-center">
              <input
                type="radio"
                value="robinhood"
                checked={dataSource === "robinhood"}
                onChange={() => setDataSource("robinhood")}
                className="mr-2"
              />
              Robinhood（即将推出）
            </label>
          </div>
        </div>
      )}

      {/* Robinhood提示 */}
      {mode === "invested" && dataSource === "robinhood" && (
        <div className="p-4 mb-4 border rounded-lg bg-gray-50 dark:bg-gray-700">
          <p className="mb-2">Robinhood集成功能正在开发中。目前请使用手动输入方式添加投资记录。</p>
          <button
            onClick={() => setDataSource("manual")}
            className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
          >
            返回手动输入
          </button>
        </div>
      )}

      {/* 搜索表单，只在手动输入模式或关注模式下显示 */}
      {(dataSource === "manual" || mode === "followed") && (
        <form onSubmit={handleSearch} className="flex gap-2 mb-4">
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="输入股票代码或公司名称"
            className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
            required
          />
          <button
            type="submit"
            className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 focus:ring-2 focus:ring-blue-300"
            disabled={loading}
          >
            {loading ? "搜索中..." : "搜索"}
          </button>
        </form>
      )}

      {/* 搜索结果列表 */}
      {searchResults.length > 0 && !selectedStock && (
        <div className="my-4 border rounded-lg overflow-hidden">
          <div className="max-h-60 overflow-y-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-100 dark:bg-gray-700">
                <tr>
                  <th className="px-4 py-2 text-left">代码</th>
                  <th className="px-4 py-2 text-left">名称</th>
                  <th className="px-4 py-2 text-right">价格</th>
                  <th className="px-4 py-2"></th>
                </tr>
              </thead>
              <tbody>
                {searchResults.map((stock) => (
                  <tr 
                    key={stock.symbol} 
                    className="border-t dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800 cursor-pointer"
                    onClick={() => handleSelectStock(stock)}
                  >
                    <td className="px-4 py-3">{stock.symbol}</td>
                    <td className="px-4 py-3">{stock.name}</td>
                    <td className="px-4 py-3 text-right">
                      ${stock.price ? stock.price.toFixed(2) : "N/A"}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <button 
                        className="text-blue-500 hover:text-blue-700"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleSelectStock(stock);
                        }}
                      >
                        选择
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* 选中的股票详情 */}
      {selectedStock && (
        <div className="my-4 p-4 border rounded-lg bg-gray-50 dark:bg-gray-700">
          <div className="flex justify-between items-center mb-4">
            <div>
              <div className="text-lg font-semibold">{selectedStock.symbol}</div>
              <div className="text-sm text-gray-600 dark:text-gray-300">{selectedStock.name}</div>
            </div>
            <div className="text-right">
              <div className="text-lg font-bold">
                ${selectedStock.price ? selectedStock.price.toFixed(2) : "N/A"}
              </div>
              {selectedStock.change_percent !== undefined && (
                <div className={`text-sm ${selectedStock.change_percent >= 0 ? 'text-green-600' : 'text-red-500'}`}>
                  {selectedStock.change_percent >= 0 ? "+" : ""}
                  {selectedStock.change_percent.toFixed(2)}%
                </div>
              )}
            </div>
          </div>

          {/* 关注或投资表单 */}
          {mode === "followed" ? (
            <div className="flex justify-end">
              <button
                onClick={handleFollow}
                className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
              >
                添加到关注列表
              </button>
            </div>
          ) : (
            <form onSubmit={handleAddInvestment} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">交易类型</label>
                  <select
                    value={transactionType}
                    onChange={(e) => setTransactionType(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                  >
                    <option value="buy">买入</option>
                    <option value="sell">卖出</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">交易日期</label>
                  <input
                    type="date"
                    value={transactionDate}
                    onChange={(e) => setTransactionDate(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                    required
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">数量</label>
                  <input
                    type="number"
                    value={quantity}
                    onChange={(e) => setQuantity(parseFloat(e.target.value))}
                    min="0.01"
                    step="0.01"
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">价格</label>
                  <input
                    type="number"
                    value={price}
                    onChange={(e) => setPrice(parseFloat(e.target.value))}
                    min="0.01"
                    step="0.01"
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                    required
                  />
                </div>
              </div>
              
              {/* 总价计算 */}
              <div className="bg-gray-100 dark:bg-gray-600 p-3 rounded-lg">
                <div className="flex justify-between">
                  <span>总计:</span>
                  <span className="font-bold">${(price * quantity).toFixed(2)}</span>
                </div>
              </div>
              
              <div className="flex justify-end gap-2">
                <button
                  type="button"
                  onClick={resetForm}
                  className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
                >
                  取消
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
                >
                  添加投资记录
                </button>
              </div>
            </form>
          )}
        </div>
      )}
    </div>
  );
}