// src/app/[investing]/components/Investments.tsx
"use client";

import { useState, useEffect } from "react";
import { getStockDetails, deleteInvestment } from "@/lib/api";

// 添加类型定义
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
  change: number;
  change_percent: number;
  [key: string]: any;
}

interface InvestmentsProps {
  investments: Investment[];
  setInvestments: React.Dispatch<React.SetStateAction<Investment[]>>;
  loading: boolean;
}

export default function Investments({ investments, setInvestments, loading }: InvestmentsProps) {
  const [stocksData, setStocksData] = useState<Record<string, StockData>>({});
  const [totalValue, setTotalValue] = useState(0);
  const [totalCost, setTotalCost] = useState(0);
  const [totalProfit, setTotalProfit] = useState(0);

  // 加载投资股票的最新数据并计算收益
  useEffect(() => {
    if (investments.length === 0) return;

    const fetchStocksData = async () => {
      try {
        // 创建股票数据请求
        const promises = investments.map(item => 
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
            newStocksData[investments[index].symbol] = result;
          }
        });

        setStocksData(newStocksData);

        // 计算总投资价值和收益
        let cost = 0;
        let value = 0;

        investments.forEach(investment => {
          const currentData = newStocksData[investment.symbol];
          if (currentData && investment.transaction_type === "buy") {
            const investmentCost = investment.quantity * investment.price_per_unit;
            const currentValue = investment.quantity * currentData.price;
            
            cost += investmentCost;
            value += currentValue;
          }
        });

        setTotalCost(cost);
        setTotalValue(value);
        setTotalProfit(value - cost);
      } catch (error) {
        console.error("获取股票数据失败:", error);
      }
    };

    fetchStocksData();

    // 设置定时刷新（每分钟更新一次）
    const intervalId = setInterval(fetchStocksData, 60000);
    return () => clearInterval(intervalId);
  }, [investments]);

  // 删除投资记录处理函数
  const handleDelete = async (id: string) => {
    try {
      await deleteInvestment(id);
      // 更新投资列表
      setInvestments(investments.filter(item => item.id !== id));
    } catch (error: unknown) {
      console.error("删除投资记录失败:", error);
      alert("删除投资记录失败: " + ((error as any).response?.data?.detail || "请稍后再试"));
    }
  };

  if (loading) {
    return <div className="flex justify-center p-6"><div className="animate-spin h-8 w-8 border-4 border-blue-500 rounded-full border-t-transparent"></div></div>;
  }

  if (investments.length === 0) {
    return <div className="text-center py-8 text-gray-500">您还没有添加任何投资记录。使用上方表单添加投资记录。</div>;
  }

  // 计算投资组合概览
  const portfolioSummary = (
    <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg mb-4 grid grid-cols-3 gap-4">
      <div className="text-center">
        <div className="text-sm text-gray-600 dark:text-gray-300">总成本</div>
        <div className="text-xl font-bold">${totalCost.toFixed(2)}</div>
      </div>
      <div className="text-center">
        <div className="text-sm text-gray-600 dark:text-gray-300">当前价值</div>
        <div className="text-xl font-bold">${totalValue.toFixed(2)}</div>
      </div>
      <div className="text-center">
        <div className="text-sm text-gray-600 dark:text-gray-300">总收益</div>
        <div className={`text-xl font-bold ${totalProfit >= 0 ? 'text-green-600' : 'text-red-500'}`}>
          {totalProfit >= 0 ? "+" : ""}${totalProfit.toFixed(2)}
          <span className="text-sm">
            ({totalCost > 0 ? ((totalProfit / totalCost) * 100).toFixed(2) : 0}%)
          </span>
        </div>
      </div>
    </div>
  );

  return (
    <div>
      <h2 className="text-lg font-semibold mb-4">我的投资</h2>
      {portfolioSummary}
      
      <div className="overflow-x-auto">
        <table className="w-full text-sm text-left">
          <thead className="text-xs text-gray-700 uppercase bg-gray-100 dark:bg-gray-700 dark:text-gray-300">
            <tr>
              <th className="px-4 py-2">代码</th>
              <th className="px-4 py-2">交易类型</th>
              <th className="px-4 py-2">数量</th>
              <th className="px-4 py-2">价格</th>
              <th className="px-4 py-2">当前价格</th>
              <th className="px-4 py-2">收益</th>
              <th className="px-4 py-2">交易日期</th>
              <th className="px-4 py-2">操作</th>
            </tr>
          </thead>
          <tbody>
            {investments.map((item) => {
              const stockData = stocksData[item.symbol] || {};
              const currentPrice = stockData.price || 0;
              const profit = item.transaction_type === "buy" 
                ? (currentPrice - item.price_per_unit) * item.quantity
                : 0; // 对于卖出交易，不计算收益
              const profitPercent = item.price_per_unit > 0 
                ? (profit / (item.price_per_unit * item.quantity)) * 100
                : 0;
              
              return (
                <tr key={item.id} className="border-b dark:border-gray-700">
                  <td className="px-4 py-3 font-medium">{item.symbol}</td>
                  <td className={`px-4 py-3 ${item.transaction_type === "buy" ? "text-green-600" : "text-red-500"}`}>
                    {item.transaction_type === "buy" ? "买入" : "卖出"}
                  </td>
                  <td className="px-4 py-3">{item.quantity}</td>
                  <td className="px-4 py-3">${item.price_per_unit.toFixed(2)}</td>
                  <td className="px-4 py-3">
                    ${currentPrice ? currentPrice.toFixed(2) : "加载中..."}
                  </td>
                  <td className={`px-4 py-3 ${profit >= 0 ? 'text-green-600' : 'text-red-500'}`}>
                    {profit >= 0 ? "+" : ""}${profit.toFixed(2)}
                    <span className="text-xs block">
                      ({profitPercent.toFixed(2)}%)
                    </span>
                  </td>
                  <td className="px-4 py-3">{new Date(item.transaction_date).toLocaleDateString()}</td>
                  <td className="px-4 py-3">
                    <button
                      onClick={() => handleDelete(item.id)}
                      className="text-red-500 hover:text-red-700"
                    >
                      删除
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