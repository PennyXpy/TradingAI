from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from jose import jwt, JWTError
from fastapi.security import OAuth2PasswordBearer
from datetime import datetime, timedelta
from passlib.context import CryptContext

from backend.models.users import User
from backend.models.token import UserToken
from backend.config.settings import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from backend.data import engine

from pydantic import BaseModel

class LoginRequest(BaseModel):
    email: str
    password: str


# ------------------ FastAPI setup ------------------ #
auth_router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

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
def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# ------------------ Get Current User ------------------ #
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token decoding failed")

    user = db.exec(select(User).where(User.email == email)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    stored_token = db.exec(
        select(UserToken).where(UserToken.user_id == user.id, UserToken.access_token == token)
    ).first()
    if not stored_token:
        raise HTTPException(status_code=403, detail="Token revoked or expired")
    
    return user

# ------------------ Register ------------------ #
@auth_router.post("/register")
def register(user: User, db: Session = Depends(get_db)):
    existing = db.exec(select(User).where(User.email == user.email)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user.hashed_password = hash_password(user.hashed_password)
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"msg": "Registered", "user_id": user.id}

# ------------------ Login ------------------ #
@auth_router.post("/login")
def login(request: LoginRequest, db: Session = Depends(get_db)):
    user = db.exec(select(User).where(User.email == request.email)).first()
    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token(data={"sub": user.email})
    db_token = UserToken(user_id=user.id, access_token=access_token)
    db.add(db_token)
    db.commit()

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


# ------------------ Logout ------------------ #
@auth_router.post("/logout")
def logout(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    db.exec(select(UserToken).where(UserToken.access_token == token)).delete()
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
