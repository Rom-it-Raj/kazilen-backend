import random
import redis
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.db.database import get_db
from app.db.models import User
from app.core.config import settings
from app.core.security import hash_otp, create_access_token

router = APIRouter()

redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
memory_otp_store = {}

class SendOTPRequest(BaseModel):
    phone_number: str

class VerifyOTPRequest(BaseModel):
    phone_number: str
    otp: str
    role: str = "customer" # Default role, can be "worker"

class RegisterRequest(BaseModel):
    phone_number: str
    full_name: str
    role: str = "customer"
    dob: Optional[str] = None
    gender: Optional[str] = None

@router.post("/send-otp")
def send_otp(request: SendOTPRequest):
    otp = str(random.randint(100000, 999999))
    print(f"\n=======================================================")
    print(f"--- DEV OTP FOR {request.phone_number}: {otp} ---")
    print(f"=======================================================\n")
    
    hashed_otp = hash_otp(otp)
    redis_key = f"otp:{request.phone_number}"
    
    try:
        redis_client.setex(redis_key, 300, hashed_otp) # 5 minutes expiry
    except Exception as e:
        print(f"[WARN] Redis unavailable ({e}), using in-memory OTP fallback.")
        memory_otp_store[request.phone_number] = hashed_otp
        
    return {"message": "OTP sent successfully", "dev_otp": otp}

@router.post("/verify-otp")
def verify_otp(request: VerifyOTPRequest, db: Session = Depends(get_db)):
    redis_key = f"otp:{request.phone_number}"
    stored_hashed_otp = None
    
    try:
        stored_hashed_otp = redis_client.get(redis_key)
    except Exception:
        stored_hashed_otp = memory_otp_store.get(request.phone_number)

    # Allow 123456 as fallback master dev OTP
    is_master_dev_otp = (request.otp == "123456")
    
    if not stored_hashed_otp and not is_master_dev_otp:
        stored_hashed_otp = memory_otp_store.get(request.phone_number)

    if not stored_hashed_otp and not is_master_dev_otp:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OTP expired or not requested. Try sending OTP again.")
        
    if not is_master_dev_otp and hash_otp(request.otp) != stored_hashed_otp:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid OTP entered")
        
    # Clean up OTP
    try:
        redis_client.delete(redis_key)
    except Exception:
        memory_otp_store.pop(request.phone_number, None)
    
    # Check if user exists
    user = db.query(User).filter(User.phone_number == request.phone_number, User.role == request.role).first()
    
    if not user:
        return {"status": "needs_registration", "phone_number": request.phone_number, "role": request.role}
        
    # User exists, issue JWT
    access_token = create_access_token(subject=user.id)
    return {"status": "success", "access_token": access_token, "token_type": "bearer"}


@router.post("/register")
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.phone_number == request.phone_number, User.role == request.role).first()
    
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already registered")
        
    new_user = User(
        phone_number=request.phone_number,
        full_name=request.full_name,
        role=request.role,
        dob=request.dob,
        gender=request.gender
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    access_token = create_access_token(subject=new_user.id)
    return {"status": "success", "access_token": access_token, "token_type": "bearer"}
