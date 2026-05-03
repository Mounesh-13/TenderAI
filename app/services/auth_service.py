from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.config import settings
from sqlalchemy.orm import Session
from app.models.db_models import DBUser
from app.models.auth import UserCreate

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    def verify_password(self, plain_password, hashed_password):
        return pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password):
        return pwd_context.hash(password)

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None):
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt

    def get_user_by_email(self, db: Session, email: str):
        return db.query(DBUser).filter(DBUser.email == email).first()

    def create_user(self, db: Session, user: UserCreate):
        hashed_password = self.get_password_hash(user.password)
        db_user = DBUser(
            email=user.email,
            hashed_password=hashed_password,
            full_name=user.full_name,
            role=user.role
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user

auth_service = AuthService()
