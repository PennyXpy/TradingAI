// src/app/[investing]/RelatedNews.tsx
"use client";

import { useState, useEffect } from "react";
import { getStockRelatedNews } from "@/lib/api";

// 添加类型定义
interface NewsItem {
  title: string;
  description: string;
  url: string;
  source: string;
  publishedAt: string;
  thumbnail?: string;
  relatedSymbol?: string;
  isFollowed?: boolean;
  isInvested?: boolean;
}

interface RelatedNewsProps {
  followedSymbols: string[];
  investedSymbols: string[];
}

export default function RelatedNews({ followedSymbols, investedSymbols }: RelatedNewsProps) {
  const [news, setNews] = useState<NewsItem[]>([]);
  const [loading, setLoading] = useState(true);

  // 加载相关新闻
  useEffect(() => {
    const allSymbols = [...new Set([...followedSymbols, ...investedSymbols])];
    if (allSymbols.length === 0) {
      setLoading(false);
      return;
    }

    const fetchNews = async () => {
      try {
        // 为每个股票获取相关新闻
        const promises = allSymbols.map(symbol => 
          getStockRelatedNews(symbol)
            .catch(err => {
              console.error(`获取${symbol}相关新闻失败:`, err);
              return [];
            })
        );

        const results = await Promise.all(promises);
        
        // 处理结果，为每条新闻添加关联的股票标记
        let allNews: NewsItem[] = [];
        
        results.forEach((result, index) => {
          const symbol = allSymbols[index];
          const isFollowed = followedSymbols.includes(symbol);
          const isInvested = investedSymbols.includes(symbol);
          
          const symbolNews = result.map((item: NewsItem) => ({
            ...item,
            relatedSymbol: symbol,
            isFollowed,
            isInvested
          }));
          
          allNews = [...allNews, ...symbolNews];
        });
        
        // 按时间排序
        allNews.sort((a, b) => new Date(b.publishedAt).getTime() - new Date(a.publishedAt).getTime());
        
        // 去重
        const uniqueNews = allNews.filter((item, index, self) => 
          index === self.findIndex(t => t.title === item.title)
        );
        
        setNews(uniqueNews.slice(0, 10)); // 最多显示10条
        setLoading(false);
      } catch (error) {
        console.error("获取相关新闻失败:", error);
        setLoading(false);
      }
    };

    fetchNews();
  }, [followedSymbols, investedSymbols]);

  if (loading) {
    return <div className="flex justify-center p-6"><div className="animate-spin h-8 w-8 border-4 border-blue-500 rounded-full border-t-transparent"></div></div>;
  }

  if (news.length === 0) {
    return <div className="text-center py-8 text-gray-500">暂无相关新闻。添加更多股票到关注或投资列表以查看相关新闻。</div>;
  }

  return (
    <div>
      <ul className="space-y-4">
        {news.map((item, index) => (
          <li key={index} className="border-b dark:border-gray-700 pb-4 last:border-0">
            <div className="flex gap-2 text-xs text-gray-600 dark:text-gray-400 mb-1">
              <span>{new Date(item.publishedAt).toLocaleDateString()}</span>
              {item.source && <span>· {item.source}</span>}
            </div>
            
            <h3 className="font-medium mb-1">
              <a href={item.url} target="_blank" rel="noopener noreferrer" className="hover:text-blue-600">
                {item.title}
              </a>
            </h3>
            
            <div className="text-sm text-gray-600 dark:text-gray-300 mb-2 line-clamp-2">
              {item.description}
            </div>
            
            <div className="flex gap-2">
              <span className="text-xs bg-gray-200 dark:bg-gray-700 px-2 py-0.5 rounded">
                {item.relatedSymbol}
              </span>
              
              {item.isFollowed && (
                <span className="text-xs bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200 px-2 py-0.5 rounded">
                  已关注
                </span>
              )}
              
              {item.isInvested && (
                <span className="text-xs bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200 px-2 py-0.5 rounded">
                  已投资
                </span>
              )}
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}