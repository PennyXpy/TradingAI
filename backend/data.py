from sqlmodel import SQLModel, Field, create_engine
from models.core_models import User, UserFollowing as Followed, UserSession as UserToken
import os

# 确保数据库目录存在
db_dir = "models"
os.makedirs(db_dir, exist_ok=True)

# 数据库文件路径
sqlite_file_name = os.path.join(db_dir, "tradingai.db")
sqlite_url = f"sqlite:///{sqlite_file_name}"

# 创建 SQLite 引擎
engine = create_engine(sqlite_url, echo=True)

# 创建所有表
def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
    print("📍 Absolute path:", os.path.abspath(sqlite_file_name))

# 数据库会话管理
from sqlmodel import Session

def get_session():
    """获取数据库会话"""
    with Session(engine) as session:
        yield session



if __name__ == "__main__":
    create_db_and_tables()
