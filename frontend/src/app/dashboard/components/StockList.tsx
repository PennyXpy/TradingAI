"use client";
import { useEffect, useState } from "react";
import api from "@/lib/api";
import MiniSparkline from "@/app/dashboard/components/MiniSparklines";

interface Stock {
  ticker: string;
  price: number;
  change_percent: number;
  spark: number[];
}

export default function StockList() {
  const [data, setData] = useState<Stock[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .get("/api/stocks/top")
      .then((res) => setData(Array.isArray(res.data) ? res.data : []))
      .catch((err) => {
        console.error(err);
        setError("股票数据获取失败");
      });
  }, []);

  if (error) return <p className="text-red-500">{error}</p>;
  if (!data.length) return <p>Loading...</p>;

  return (
    <table className="w-full text-sm">
      <tbody>
        {data.map((s) => (
          <tr key={s.ticker} className="border-b last:border-none">
            <td className="pr-2">
              <MiniSparkline
                data={s.spark}
                positive={s.change_percent >= 0}
                width={60}
              />
            </td>
            <td>{s.ticker}</td>
            <td className="text-right">${s.price.toFixed(2)}</td>
            <td
              className={`text-right ${
                s.change_percent >= 0 ? "text-green-600" : "text-red-500"
              }`}
            >
              {s.change_percent.toFixed(2)}%
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}