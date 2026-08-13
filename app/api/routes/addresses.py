from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from app.db.database import get_db
from app.db.models import User
from app.api.deps import get_current_user
from app.schemas.address import AddressCreateSchema, AddressUpdateSchema, AddressResponseSchema
from app.services.address_service import AddressService

router = APIRouter()

@router.get("", response_model=List[AddressResponseSchema])
def get_user_addresses(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve all saved addresses for the authenticated user."""
    return AddressService.get_user_addresses(current_user.id, db)

@router.post("", status_code=status.HTTP_201_CREATED)
def create_address(
    data: AddressCreateSchema,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Save a new address to the user's address book."""
    return AddressService.create_address(current_user.id, data, db)

@router.put("/{address_id}")
def update_address(
    address_id: int,
    data: AddressUpdateSchema,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update an existing address for the authenticated user."""
    return AddressService.update_address(address_id, current_user.id, data, db)

@router.delete("/{address_id}")
def delete_address(
    address_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a saved address."""
    return AddressService.delete_address(address_id, current_user.id, db)

@router.patch("/{address_id}/default")
def set_default_address(
    address_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Set an address as the default address."""
    return AddressService.set_default_address(address_id, current_user.id, db)
