// src/lib/api.ts
import axios from "axios"

const api = axios.create({
  baseURL: "http://localhost:8000", // 你的 FastAPI 地址
  headers: {
    "Content-Type": "application/json",
  },
})

// 请求拦截器 - 处理表单数据
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("token")
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    
    // 如果数据是 FormData，确保正确设置 Content-Type
    if (config.data instanceof FormData) {
      config.headers["Content-Type"] = "application/x-www-form-urlencoded"
    }
    
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器 - 处理常见错误
api.interceptors.response.use(
  (response) => {
    return response
  },
  (error) => {
    // 处理 401 未授权错误
    if (error.response && error.response.status === 401) {
      // 清除本地存储的令牌
      localStorage.removeItem("token")
      
      // 如果不在登录页，可以重定向到登录页
      if (typeof window !== "undefined" && !window.location.pathname.includes("/login")) {
        window.location.href = "/"
      }
    }
    
    return Promise.reject(error)
  }
)

// 定义类型接口
interface FollowedStock {
  id: string;
  user_id: string;
  symbol: string;
  asset_type: string;
  name?: string;
  notes?: string;
  added_at: string;
}

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
  sector?: string;
  industry?: string;
  market_cap?: number;
  pe_ratio?: number;
  dividend_yield?: number;
  volume?: number;
  fallback?: boolean;
}

interface NewsItem {
  title: string;
  description: string;
  url: string;
  source: string;
  publishedAt: string;
  thumbnail?: string;
  relatedSymbol?: string;
}

interface InvestmentParams {
  asset_type?: string;
  symbol?: string;
  transaction_type?: string;
}

export async function getUserProfile() {
  const response = await api.get("/auth/me");
  return response.data;
}

// ====================== Dashboard API ======================
// 获取热门股票
export async function fetchTopStocks(limit = 5) {
  const res = await api.get(`/stocks/top?limit=${limit}`);
  return res.data;
}

// 获取热门加密货币
export async function fetchTopCryptos(limit = 5) {
  const res = await api.get(`/cryptos/top?limit=${limit}`);
  return res.data;
}

// 获取最新金融新闻
export async function fetchLatestNews(limit = 5) {
  const res = await api.get(`/news/latest?limit=${limit}`);
  return res.data;
}

// 获取市场指数
export async function fetchMarketIndexes() {
  const res = await api.get("/market/indexes");
  return res.data;
}

// ====================== 股票和加密货币搜索 API ======================
// 搜索股票
export async function searchStocks(query: string, limit: number = 10): Promise<StockData[]> {
  const res = await api.get(`/stocks/search?query=${encodeURIComponent(query)}&limit=${limit}`);
  return res.data;
}


// 获取股票详细信息
export async function getStockDetails(symbol: string): Promise<StockData> {
  const res = await api.get(`/stocks/details?symbol=${encodeURIComponent(symbol)}`);
  return res.data;
}

// 获取股票历史数据
export async function getStockHistory(symbol: string, period: string = "1mo", interval: string = "1d"): Promise<any[]> {
  const res = await api.get(
    `/stocks/history?symbol=${encodeURIComponent(symbol)}&period=${period}&interval=${interval}`
  );
  return res.data;
}

// 搜索加密货币
export async function searchCryptos(query: string, limit: number = 10): Promise<StockData[]> {
  const res = await api.get(`/cryptos/search?query=${encodeURIComponent(query)}&limit=${limit}`);
  return res.data;
}

// 获取加密货币详细信息
export async function getCryptoDetails(symbol: string): Promise<StockData> {
  const res = await api.get(`/cryptos/details?symbol=${encodeURIComponent(symbol)}`);
  return res.data;
}

// ====================== 新闻 API ======================
// 获取与特定股票相关的新闻
export async function getStockRelatedNews(symbol: string, limit: number = 5, tab: string = "news"): Promise<NewsItem[]> {
  const res = await api.get(`/news/related?symbol=${encodeURIComponent(symbol)}&limit=${limit}`);
  return res.data;
}

// 获取投资组合相关新闻
export async function getPortfolioNews(symbols: string[] | string, limit: number = 10): Promise<NewsItem[]> {
  const symbolsStr = Array.isArray(symbols) ? symbols.join(',') : symbols;
  const res = await api.get(`/news/portfolio?symbols=${encodeURIComponent(symbolsStr)}&limit=${limit}`);
  return res.data;
}


// ====================== 投资组合管理 API ======================
// 获取关注列表
export async function fetchFollowedStocks(assetType?: string): Promise<FollowedStock[]> {
  let url = "/portfolio/followed";
  if (assetType) {
    url += `?asset_type=${assetType}`;
  }
  const res = await api.get(url);
  return res.data;
}

// 添加关注
export async function followStock(data: {
  symbol: string;
  asset_type: string;
  name?: string;
  notes?: string;
}): Promise<FollowedStock> {
  const res = await api.post("/portfolio/followed", data);
  return res.data;
}

// 取消关注
export async function unfollowStock(id: string): Promise<{message: string}> {
  const res = await api.delete(`/portfolio/followed/${id}`);
  return res.data;
}

// 获取投资记录
export async function fetchInvestments(params?: InvestmentParams): Promise<Investment[]> {
  let url = "/portfolio/investments";
  
  if (params) {
    const queryParams = new URLSearchParams();
    if (params.asset_type) queryParams.append("asset_type", params.asset_type);
    if (params.symbol) queryParams.append("symbol", params.symbol);
    if (params.transaction_type) queryParams.append("transaction_type", params.transaction_type);
    
    const queryString = queryParams.toString();
    if (queryString) {
      url += `?${queryString}`;
    }
  }
  
  const res = await api.get(url);
  return res.data;
}

// 添加投资记录
export async function addInvestment(data: {
  symbol: string;
  asset_type: string;
  quantity: number;
  price_per_unit: number;
  transaction_date: string;
  transaction_type: string;
  fees?: number;
  notes?: string;
}): Promise<Investment> {
  const res = await api.post("/portfolio/investments", data);
  return res.data;
}

// 删除投资记录
export async function deleteInvestment(id: string): Promise<{message: string}> {
  const res = await api.delete(`/portfolio/investments/${id}`);
  return res.data;
}

export default api
