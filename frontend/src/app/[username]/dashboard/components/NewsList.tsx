"use client";

import { useEffect, useState } from "react";
import api from "@/lib/api";

interface News {
  title: string;
  link: string;
  time_ago: string;
  scores?: { polarity?: number };
}

export default function NewsList() {
  const [news, setNews] = useState<News[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .get("/news/latest")
      .then((res) => setNews(Array.isArray(res.data) ? res.data : []))
      .catch((err) => {
        console.error(err);
        setError("新闻数据获取失败");
      });
  }, []);

  if (error) return <p className="text-red-500">{error}</p>;
  if (!news.length) return <p>Loading...</p>;

  return (
    <ul className="space-y-3">
      {news.map((n, idx) => {
        const polarity = n.scores?.polarity ?? 0;
        const pos = polarity >= 0;
        return (
          <li key={idx} className="border-b pb-3 last:border-none">
            {/* ----------- 第一行：标题 ----------- */}
            <a
              href={n.link}
              target="_blank"
              rel="noopener noreferrer"
              className="font-medium hover:underline block"
            >
              {n.title}
            </a>

            {/* ----------- 第二行：Sentiment | 时间 ----------- */}
            <div className="flex items-center justify-between text-xs mt-0.5">
              <span className={pos ? "text-green-500" : "text-red-500"}>
                Sentiment: {polarity.toFixed(2)}
              </span>
              <span className="text-gray-400 whitespace-nowrap">
                {n.time_ago}
              </span>
            </div>
          </li>
        );
      })}
    </ul>
  );
}
