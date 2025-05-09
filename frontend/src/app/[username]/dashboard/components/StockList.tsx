"use client";
import { useEffect, useState } from "react";
import api from "@/lib/api";
import MiniSparkline from "@/app/[username]/dashboard/components/MiniSparklines";

// 更新为与后端匹配的接口
interface Stock {
  symbol: string;
  name: string;
  price: number;
  change: number;
  change_percent: number;
  fallback?: boolean;
}

export default function StockList() {
  const [stocks, setStocks] = useState<Stock[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    
    const fetchData = async () => {
      try {
        setLoading(true);
        
        const response = await api.get("/stocks/top");
        
        if (isMounted) {
          setStocks(response.data);
          setLoading(false);
        }
      } catch (err) {
        console.error("无法获取股票数据", err);
        if (isMounted) {
          setError("股票数据获取失败");
          setLoading(false);
        }
      }
    };

    fetchData();
    
    // 清理函数
    return () => {
      isMounted = false;
    };
  }, []);

  if (loading) {
    return <p className="text-gray-500">加载中...</p>;
  }

  if (error) {
    return <p className="text-red-500">{error}</p>;
  }

  if (!stocks || !stocks.length) {
    return <p className="text-gray-500">暂无数据</p>;
  }

  return (
    <table className="w-full text-sm">
      <tbody>
        {stocks.map((stock) => (
          <tr key={stock.symbol} className="border-b last:border-none">
            <td className="py-2 font-medium" style={{width: "30%"}}>
              {stock.symbol}
              <div className="text-xs text-gray-500">{stock.name}</div>
            </td>
            <td className="text-right" style={{width: "25%"}}>
              ${stock.price.toFixed(2)}
            </td>
            <td
              className={`text-right ${
                stock.change_percent >= 0 ? "text-green-600" : "text-red-500"
              }`}
              style={{width: "25%"}}
            >
              {stock.change_percent.toFixed(2)}%
            </td>
            <td className="text-right" style={{width: "20%"}}>
              <MiniSparkline
                data={[stock.price]}
                positive={stock.change_percent >= 0}
                width={50}
              />
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}