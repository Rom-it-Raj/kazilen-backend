from datetime import datetime
from pydantic import BaseModel
from typing import Optional, Union

class AddressCreateSchema(BaseModel):
    tag: Optional[str] = "Home"
    flat_no: Optional[str] = None
    street: Optional[str] = None
    area: Optional[str] = ""
    landmark: Optional[str] = None
    city: Optional[str] = "Nagpur"
    pincode: Optional[str] = None
    full_address: str
    latitude: Optional[str] = None
    longitude: Optional[str] = None
    is_default: Optional[bool] = False

class AddressUpdateSchema(BaseModel):
    tag: Optional[str] = None
    flat_no: Optional[str] = None
    street: Optional[str] = None
    area: Optional[str] = None
    landmark: Optional[str] = None
    city: Optional[str] = None
    pincode: Optional[str] = None
    full_address: Optional[str] = None
    latitude: Optional[str] = None
    longitude: Optional[str] = None
    is_default: Optional[bool] = None

class AddressResponseSchema(BaseModel):
    id: int
    user_id: int
    tag: str
    flat_no: Optional[str] = None
    street: Optional[str] = None
    area: str
    landmark: Optional[str] = None
    city: str
    pincode: Optional[str] = None
    full_address: str
    latitude: Optional[str] = None
    longitude: Optional[str] = None
    is_default: bool
    created_at: Optional[Union[datetime, str]] = None
    updated_at: Optional[Union[datetime, str]] = None

    class Config:
        from_attributes = True
