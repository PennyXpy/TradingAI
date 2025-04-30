"use client";
import { useEffect, useState } from "react";
import api from "@/lib/api";
import MiniSparkline from "@/app/dashboard/components/MiniSparklines";

interface Index {
  symbol: string;
  name: string;
  value: number;
  change_abs: number;
  change_pct: number;
  spark: number[];
}

export default function IndexGrid() {
  const [items, setItems] = useState<Index[]>([]);

  useEffect(() => {
    api.get("/api/market/indexes").then((res) => setItems(res.data));
  }, []);

  if (!items.length) return null;

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 gap-px bg-gray-700 rounded-lg overflow-hidden">
      {items.map((i) => {
        const pos = i.change_pct >= 0;
        return (
          <div
            key={i.symbol}
            className="bg-white/5 dark:bg-slate-800 p-3 flex flex-col gap-1"
          >
            <span className="text-xs text-blue-300 underline">{i.name}</span>
            <span className="text-sm font-semibold">{i.value.toLocaleString()}</span>

            <MiniSparkline data={i.spark} positive={pos} />

            <span className={pos ? "text-green-400 text-xs" : "text-red-400 text-xs"}>
              {i.change_abs > 0 ? "+" : ""}
              {i.change_abs.toFixed(2)}&nbsp;({i.change_pct.toFixed(2)}%)
            </span>
          </div>
        );
      })}
    </div>
  );
}
