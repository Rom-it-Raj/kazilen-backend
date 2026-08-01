from pydantic import BaseModel
from typing import Optional, List, Union

class UserUpdateSchema(BaseModel):
    full_name: Optional[str] = None
    dob: Optional[str] = None
    gender: Optional[str] = None

class WorkerServicesUpdateSchema(BaseModel):
    offered_services: Union[List[str], str]

class UserResponseSchema(BaseModel):
    id: int
    phone_number: str
    full_name: Optional[str] = None
    role: str
    dob: Optional[str] = None
    gender: Optional[str] = None
    offered_services: List[str] = []
    created_at: Optional[str] = None
