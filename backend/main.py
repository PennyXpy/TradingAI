from fastapi import FastAPI
from backend.service.auth import auth_router

app = FastAPI()

@app.get("/")
def read_root():
    return {"msg": "Welcome to TradingAI API"}

app.include_router(auth_router)
