from sqlmodel import SQLModel, Field, create_engine
from backend.models.users import User
  # 引入你定义的模型
from backend.models.token import UserToken

# 数据库文件路径（保存在 models 目录下）
sqlite_file_name = "backend/models/tradingai.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

# 创建 SQLite 引擎
engine = create_engine(sqlite_url, echo=True)

# 创建所有表
def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

if __name__ == "__main__":
    create_db_and_tables()
