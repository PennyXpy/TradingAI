"use client";
import { useEffect, useState } from "react";
import api from "@/lib/api";
import MiniSparkline from "@/app/dashboard/components/MiniSparklines";

interface Coin {
  ticker: string;
  price: number;
  change_percent: number;
  spark: number[];
}

export default function CryptoList() {
  const [coins, setCoins] = useState<Coin[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .get("/api/cryptos/top")
      .then((res) => setCoins(Array.isArray(res.data) ? res.data : []))
      .catch((err) => {
        console.error(err);
        setError("加密货币数据获取失败");
      });
  }, []);

  if (error) return <p className="text-red-500">{error}</p>;
  if (!coins.length) return <p>Loading...</p>;

  return (
    <table className="w-full text-sm">
      <tbody>
        {coins.map((c) => (
          <tr
            key={c.ticker}
            className="border-b last:border-none"
          >
            <td className="pr-2">
              <MiniSparkline
                data={c.spark}
                positive={c.change_percent >= 0}
                width={60}
              />
            </td>
            <td>{c.ticker}</td>
            <td className="text-right">${c.price.toFixed(2)}</td>
            <td
              className={`text-right ${
                c.change_percent >= 0 ? "text-green-600" : "text-red-500"
              }`}
            >
              {c.change_percent.toFixed(2)}%
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}