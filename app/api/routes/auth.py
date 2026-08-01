from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.auth import SendOTPRequest, VerifyOTPRequest, RegisterRequest
from app.services.auth_service import AuthService

router = APIRouter()

@router.post("/send-otp")
def send_otp(request: SendOTPRequest):
    """Sends OTP to user's phone number via SMS (Logs dev OTP in local environment)."""
    return AuthService.send_otp(request)

@router.post("/verify-otp")
def verify_otp(request: VerifyOTPRequest, db: Session = Depends(get_db)):
    """Verifies OTP and returns access token or indicates registration needed."""
    return AuthService.verify_otp(request, db)

@router.post("/register")
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """Registers a new user (customer or worker) and returns an access token."""
    return AuthService.register(request, db)
