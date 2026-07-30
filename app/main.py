from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional
import traceback

from app.api.routes import auth
from app.db.database import engine, Base, get_db
from app.db.models import User
from app.core.config import settings
from app.core.security import decode_access_token

# Create database tables
Base.metadata.create_all(bind=engine)

def auto_migrate():
    with engine.begin() as conn:
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN dob VARCHAR"))
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN gender VARCHAR"))
        except Exception:
            pass

auto_migrate()

app = FastAPI(title="Kazilen API")

ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:4000",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:4000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print(f"[ERROR] Uncaught exception: {exc}")
    traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc) or "Internal Server Error"},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*",
        }
    )

app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])

security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    token = credentials.credentials
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_id: str = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=401, detail="Could not validate credentials")
    
    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user

class UserUpdateSchema(BaseModel):
    full_name: Optional[str] = None
    dob: Optional[str] = None
    gender: Optional[str] = None

@app.get("/api/users/me")
def read_users_me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "phone_number": current_user.phone_number,
        "full_name": current_user.full_name,
        "role": current_user.role,
        "dob": current_user.dob,
        "gender": current_user.gender,
        "created_at": str(current_user.created_at) if current_user.created_at else None
    }

@app.put("/api/users/me")
def update_user_me(data: UserUpdateSchema, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if data.full_name is not None:
        current_user.full_name = data.full_name
    if data.dob is not None:
        current_user.dob = data.dob
    if data.gender is not None:
        current_user.gender = data.gender
        
    db.commit()
    db.refresh(current_user)
    
    return {
        "status": "success",
        "user": {
            "id": current_user.id,
            "phone_number": current_user.phone_number,
            "full_name": current_user.full_name,
            "role": current_user.role,
            "dob": current_user.dob,
            "gender": current_user.gender
        }
    }

@app.get("/")
def root():
    return {"message": "Kazilen API is running"}
