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

@router.post("/send-otp")
def send_otp(request: SendOTPRequest):
    otp = str(random.randint(100000, 999999))
    # In a real app, send OTP via SMS here
    print(f"--- DEV ONLY: OTP for {request.phone_number} is {otp} ---")
    
    hashed_otp = hash_otp(otp)
    redis_key = f"otp:{request.phone_number}"
    
    try:
        redis_client.setex(redis_key, 300, hashed_otp) # 5 minutes expiry
    except redis.ConnectionError:
        raise HTTPException(status_code=500, detail="Could not connect to Redis. Ensure it is running.")
        
    return {"message": "OTP sent successfully"}

@router.post("/verify-otp")
def verify_otp(request: VerifyOTPRequest, db: Session = Depends(get_db)):
    redis_key = f"otp:{request.phone_number}"
    
    try:
        stored_hashed_otp = redis_client.get(redis_key)
    except redis.ConnectionError:
        raise HTTPException(status_code=500, detail="Could not connect to Redis.")
        
    if not stored_hashed_otp:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OTP expired or not requested")
        
    if hash_otp(request.otp) != stored_hashed_otp:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid OTP")
        
    # OTP is valid, remove it
    redis_client.delete(redis_key)
    
    # Check if user exists
    user = db.query(User).filter(User.phone_number == request.phone_number, User.role == request.role).first()
    
    if not user:
        # User doesn't exist, tell frontend to redirect to register page
        # In a real app, you might return a short-lived token just for registration
        return {"status": "needs_registration", "phone_number": request.phone_number, "role": request.role}
        
    # User exists, issue JWT
    access_token = create_access_token(subject=user.id)
    return {"status": "success", "access_token": access_token, "token_type": "bearer"}


@router.post("/register")
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    # Simple registration without re-verifying OTP for simplicity in this demo.
    # In production, require a valid registration token.
    existing_user = db.query(User).filter(User.phone_number == request.phone_number, User.role == request.role).first()
    
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already registered")
        
    new_user = User(
        phone_number=request.phone_number,
        full_name=request.full_name,
        role=request.role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    access_token = create_access_token(subject=new_user.id)
    return {"status": "success", "access_token": access_token, "token_type": "bearer"}
