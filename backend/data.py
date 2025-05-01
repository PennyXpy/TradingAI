from sqlmodel import SQLModel, Field, create_engine
from models.users import User, FollowedAsset
from models.token import UserToken
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



if __name__ == "__main__":
    create_db_and_tables()
