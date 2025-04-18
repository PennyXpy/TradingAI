import os
from dotenv import load_dotenv

# 加载 .env 文件中的变量
load_dotenv()

# JWT 配置
SECRET_KEY = os.getenv("SECRET_KEY", "super-secret-key")  # 默认值可自定义
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
