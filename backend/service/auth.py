from fastapi import APIRouter, Depends, HTTPException, status, Request  # 添加Request导入
from sqlmodel import Session, select
from jose import jwt, JWTError
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import datetime, timezone, timedelta
from passlib.context import CryptContext
from typing import Optional
import logging  # 添加调试代码: 导入logging

from models.users import User
from models.token import UserToken
from config.settings import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from data import engine

from pydantic import BaseModel

# 添加调试代码: 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LoginRequest(BaseModel):
    email: str
    password: str

class UserCreate(BaseModel):
    email: str
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

# ------------------ FastAPI setup ------------------ #
auth_router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# ------------------ DB Dependency ------------------ #
def get_db():
    with Session(engine) as session:
        yield session

# ------------------ Password Utils ------------------ #
def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def hash_password(pw: str) -> str:
    return pwd_context.hash(pw)

# ------------------ JWT Utils ------------------ #
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=60)
    to_encode.update({"exp": expire})
    
    # 添加调试代码: 记录令牌创建信息
    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    logger.info(f"创建令牌 (前10位): {token[:10]}...")
    return token

# ------------------ Get Current User ------------------ #
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    try:
        # 添加调试代码: 记录收到的令牌
        logger.info(f"收到令牌 (前10位): {token[:10]}...")
        logger.info(f"使用密钥 (前10位): {SECRET_KEY[:10]}...")
        logger.info(f"使用算法: {ALGORITHM}")
        
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # 添加调试代码: 记录解码后的内容
        logger.info(f"解码成功，Payload: {payload}")
        
        email = payload.get("sub")
        if email is None:
            logger.error("令牌中无sub字段")  # 添加调试代码
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError as e:
        # 添加调试代码: 记录详细错误信息
        logger.error(f"JWT解码错误: {str(e)}")
        raise HTTPException(status_code=401, detail=f"Token decoding failed: {str(e)}")

    user = db.exec(select(User).where(User.email == email)).first()
    if not user:
        logger.error(f"未找到用户: {email}")  # 添加调试代码
        raise HTTPException(status_code=404, detail="User not found")

    # 修复字段名: 从access_token改为token
    stored_token = db.exec(
        select(UserToken).where(UserToken.user_id == user.id, UserToken.token == token)
    ).first()
    if not stored_token:
        logger.error(f"数据库中未找到令牌")  # 添加调试代码
        raise HTTPException(status_code=403, detail="Token revoked or expired")
    
    logger.info(f"用户验证成功: {user.username}")  # 添加调试代码
    return user

# ------------------ Register ------------------ #
@auth_router.post("/register", response_model=dict)
def register_user(user_data: UserCreate):
    existing_user = get_user(user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    hashed_password = hash_password(user_data.password)
    new_user = User(email=user_data.email, username= user_data.username, hashed_password=hashed_password)
    
    with Session(engine) as session:
        session.add(new_user)
        session.commit()
        session.refresh(new_user)
    
    return {"message": "User created successfully"}

# ------------------ Login ------------------ #
@auth_router.post("/login", response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    # 添加调试代码: 记录登录信息
    logger.info(f"用户 {user.username} 登录成功")
    
    with Session(engine) as session:
        user_token = UserToken(
            user_id=user.id,
            token=access_token,
            expires_at=datetime.now(timezone.utc) + access_token_expires
        )
        session.add(user_token)
        session.commit()
    
    return {"access_token": access_token, "token_type": "bearer"}

# ------------------ Logout ------------------ #
@auth_router.post("/logout")
def logout(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    # 修复字段名: 从access_token改为token
    db.exec(select(UserToken).where(UserToken.token == token)).delete()
    db.commit()
    return {"msg": "Logged out"}

# ------------------ Profile Info ------------------ #
@auth_router.get("/me")
def get_profile(user: User = Depends(get_current_user)):
    return {
        "id": user.id,
        "email": user.email,
        "username": user.username
    }

# 添加调试端点: 检查Authorization头
@auth_router.get("/debug-headers")
async def debug_headers(request: Request):
    headers = dict(request.headers)
    auth_header = headers.get("authorization", "无authorization头")
    return {"auth_header": auth_header}

@auth_router.get("/user-by-email")
def user_by_email(email: str):
    user = get_user(email)
    if not user:
        raise HTTPException(404, "User not found")
    return user

def get_user(email: str):
    with Session(engine) as session:
        statement = select(User).where(User.email == email)
        user = session.exec(statement).first()
        return user

def authenticate_user(email: str, password: str):
    user = get_user(email)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user