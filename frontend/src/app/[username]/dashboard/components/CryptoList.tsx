"use client";
import { useEffect, useState } from "react";
import api from "@/lib/api";
import MiniSparkline from "@/app/[username]/dashboard/components/MiniSparklines";

// 更新为与后端匹配的接口
interface Crypto {
  symbol: string;
  name: string;
  price: number;
  change: number;
  change_percent: number;
  fallback?: boolean;
}

export default function CryptoList() {
  const [coins, setCoins] = useState<Crypto[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    
    const fetchData = async () => {
      try {
        setLoading(true);
        
        const response = await api.get("/cryptos/top");
        
        if (isMounted) {
          setCoins(response.data);
          setLoading(false);
        }
      } catch (err) {
        console.error("无法获取加密货币数据", err);
        if (isMounted) {
          setError("加密货币数据获取失败");
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

  if (!coins || !coins.length) {
    return <p className="text-gray-500">暂无数据</p>;
  }

  return (
    <table className="w-full text-sm">
      <tbody>
        {coins.map((coin) => (
          <tr
            key={coin.symbol}
            className="border-b last:border-none"
          >
            <td className="py-2 font-medium" style={{width: "30%"}}>
              {coin.symbol}
              <div className="text-xs text-gray-500">{coin.name}</div>
            </td>
            <td className="text-right" style={{width: "25%"}}>
              ${coin.price.toFixed(2)}
            </td>
            <td
              className={`text-right ${
                coin.change_percent >= 0 ? "text-green-600" : "text-red-500"
              }`}
              style={{width: "25%"}}
            >
              {coin.change_percent.toFixed(2)}%
            </td>
            <td className="text-right" style={{width: "20%"}}>
              <MiniSparkline
                data={[coin.price]}
                positive={coin.change_percent >= 0}
                width={50}
              />
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}