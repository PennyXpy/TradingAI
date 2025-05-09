# backend/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 导入routers
from service.auth import auth_router
from service.pages_routes import router as main_router  # 👈 你的新业务路由
from service.user_portfolio import portfolio_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"msg": "Welcome to TradingAI API"}

# 👇 注册多个模块路由
app.include_router(auth_router, prefix="/auth")  # 登录注册相关接口
app.include_router(main_router) # 股票/新闻/加密币信息接口
app.include_router(portfolio_router, prefix="/portfolio", tags=["portfolio"])