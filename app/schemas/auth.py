from pydantic import BaseModel
from typing import Optional

class SendOTPRequest(BaseModel):
    phone_number: str

class VerifyOTPRequest(BaseModel):
    phone_number: str
    otp: str
    role: str = "customer"  # "customer" or "worker"

class RegisterRequest(BaseModel):
    phone_number: str
    full_name: str
    role: str = "customer"
    dob: Optional[str] = None
    gender: Optional[str] = None

class TokenResponse(BaseModel):
    status: str
    access_token: Optional[str] = None
    token_type: Optional[str] = "bearer"
    phone_number: Optional[str] = None
    role: Optional[str] = None
