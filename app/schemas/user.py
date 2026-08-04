from datetime import datetime
from pydantic import BaseModel
from typing import Optional, List, Union, Dict, Any

class UserUpdateSchema(BaseModel):
    full_name: Optional[str] = None
    dob: Optional[str] = None
    gender: Optional[str] = None

class WorkerServicesUpdateSchema(BaseModel):
    offered_services: Union[List[Union[Dict[str, Any], str]], str, Dict[str, Any]]

class UserResponseSchema(BaseModel):
    id: int
    phone_number: str
    full_name: Optional[str] = None
    role: str
    dob: Optional[str] = None
    gender: Optional[str] = None
    offered_services: Union[List[Any], str] = []
    referral_code: Optional[str] = None
    referral_points: int = 0
    created_at: Optional[Union[datetime, str]] = None
