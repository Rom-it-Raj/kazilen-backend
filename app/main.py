from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

from app.api.routes import auth
from app.db.database import engine, Base, get_db
from app.db.models import User
from app.core.config import settings
from app.core.security import decode_access_token

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Kazilen API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this to the specific domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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

@app.get("/api/users/me")
def read_users_me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "phone_number": current_user.phone_number,
        "full_name": current_user.full_name,
        "role": current_user.role
    }

@app.get("/")
def root():
    return {"message": "Kazilen API is running"}
