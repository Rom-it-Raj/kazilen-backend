from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional, List, Union
import json
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
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN offered_services VARCHAR"))
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

class WorkerServicesUpdateSchema(BaseModel):
    offered_services: Union[List[str], str]

@app.get("/api/users/me")
def read_users_me(current_user: User = Depends(get_current_user)):
    services_list = []
    if current_user.offered_services:
        try:
            services_list = json.loads(current_user.offered_services)
        except Exception:
            services_list = current_user.offered_services.split(",")

    return {
        "id": current_user.id,
        "phone_number": current_user.phone_number,
        "full_name": current_user.full_name,
        "role": current_user.role,
        "dob": current_user.dob,
        "gender": current_user.gender,
        "offered_services": services_list,
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

@app.put("/api/users/me/services")
def update_worker_services(data: WorkerServicesUpdateSchema, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if isinstance(data.offered_services, list):
        current_user.offered_services = json.dumps(data.offered_services)
    else:
        current_user.offered_services = str(data.offered_services)

    db.commit()
    db.refresh(current_user)

    return {
        "status": "success",
        "message": "Offered services updated in database",
        "offered_services": data.offered_services
    }

@app.get("/api/workers/available")
@app.get("/api/workers")
def get_available_workers(service_id: Optional[str] = None, sub_category: Optional[str] = None, db: Session = Depends(get_db)):
    target_service = service_id or sub_category
    workers = db.query(User).filter(User.role == "worker").all()
    filtered = []

    for w in workers:
        enabled = True
        if target_service and w.offered_services:
            try:
                services_list = json.loads(w.offered_services)
                if isinstance(services_list, list):
                    enabled = target_service in services_list
                else:
                    enabled = target_service in str(services_list).split(",")
            except Exception:
                enabled = target_service in str(w.offered_services).split(",")

        if enabled:
            filtered.append({
                "id": w.id,
                "full_name": w.full_name or "Verified Partner",
                "phone_number": w.phone_number,
                "rating": 4.9,
                "locality": "Dharampeth, Nagpur",
                "eta": "Arrives in 30 mins",
                "jobs_completed": "150+"
            })

    return {"status": "success", "workers": filtered}

@app.get("/")
def root():
    return {"message": "Kazilen API is running"}
