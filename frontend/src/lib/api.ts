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
        window.location.href = "/login"
      }
    }
    
    return Promise.reject(error)
  }
)

export async function getUserProfile() {
  const response = await api.get("/users/me");
  return response.data;
}

// 获取热门股票
export async function fetchTopStocks() {
  const res = await api.get("/stocks/top")
  return res.data
}

// 获取热门加密货币
export async function fetchTopCryptos() {
  const res = await api.get("/cryptos/top")
  return res.data
}

// 获取最新金融新闻
export async function fetchLatestNews() {
  const res = await api.get("/news/latest")
  return res.data
}


export default api
