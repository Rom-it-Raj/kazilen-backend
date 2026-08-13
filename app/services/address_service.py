from typing import List
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.db.models import Address
from app.schemas.address import AddressCreateSchema, AddressUpdateSchema

class AddressService:
    @staticmethod
    def _format_address(addr: Address) -> dict:
        return {
            "id": addr.id,
            "user_id": addr.user_id,
            "tag": addr.tag or "Home",
            "flat_no": addr.flat_no,
            "street": addr.street,
            "area": addr.area or "",
            "landmark": addr.landmark,
            "city": addr.city or "Nagpur",
            "pincode": addr.pincode,
            "full_address": addr.full_address,
            "latitude": addr.latitude,
            "longitude": addr.longitude,
            "is_default": bool(addr.is_default),
            "created_at": str(addr.created_at) if addr.created_at else None,
            "updated_at": str(addr.updated_at) if addr.updated_at else None,
        }

    @classmethod
    def get_user_addresses(cls, user_id: int, db: Session) -> List[dict]:
        addresses = (
            db.query(Address)
            .filter(Address.user_id == user_id)
            .order_by(desc(Address.is_default), desc(Address.id))
            .all()
        )
        return [cls._format_address(a) for a in addresses]

    @classmethod
    def create_address(cls, user_id: int, data: AddressCreateSchema, db: Session) -> dict:
        # Check if user already has addresses
        existing_count = db.query(Address).filter(Address.user_id == user_id).count()
        
        # If it's the user's first address or explicitly marked default, make it default
        make_default = 1 if (existing_count == 0 or data.is_default) else 0

        if make_default == 1:
            # Unset any current default
            db.query(Address).filter(Address.user_id == user_id).update({"is_default": 0})

        # Ensure area is non-empty fallback
        area_val = (data.area or "").strip()
        if not area_val and data.city:
            area_val = data.city.strip()
        elif not area_val:
            area_val = "Nagpur"

        new_addr = Address(
            user_id=user_id,
            tag=data.tag or "Home",
            flat_no=data.flat_no,
            street=data.street,
            area=area_val,
            landmark=data.landmark,
            city=data.city or "Nagpur",
            pincode=data.pincode,
            full_address=data.full_address.strip(),
            latitude=str(data.latitude) if data.latitude is not None else None,
            longitude=str(data.longitude) if data.longitude is not None else None,
            is_default=make_default,
        )

        db.add(new_addr)
        db.commit()
        db.refresh(new_addr)

        return {
            "status": "success",
            "message": "Address saved successfully",
            "address": cls._format_address(new_addr)
        }

    @classmethod
    def update_address(cls, address_id: int, user_id: int, data: AddressUpdateSchema, db: Session) -> dict:
        addr = db.query(Address).filter(Address.id == address_id, Address.user_id == user_id).first()
        if not addr:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Address not found")

        if data.is_default is True:
            db.query(Address).filter(Address.user_id == user_id).update({"is_default": 0})
            addr.is_default = 1
        elif data.is_default is False:
            addr.is_default = 0

        if data.tag is not None:
            addr.tag = data.tag
        if data.flat_no is not None:
            addr.flat_no = data.flat_no
        if data.street is not None:
            addr.street = data.street
        if data.area is not None:
            addr.area = data.area
        if data.landmark is not None:
            addr.landmark = data.landmark
        if data.city is not None:
            addr.city = data.city
        if data.pincode is not None:
            addr.pincode = data.pincode
        if data.full_address is not None:
            addr.full_address = data.full_address.strip()
        if data.latitude is not None:
            addr.latitude = str(data.latitude)
        if data.longitude is not None:
            addr.longitude = str(data.longitude)

        db.commit()
        db.refresh(addr)

        return {
            "status": "success",
            "message": "Address updated successfully",
            "address": cls._format_address(addr)
        }

    @classmethod
    def delete_address(cls, address_id: int, user_id: int, db: Session) -> dict:
        addr = db.query(Address).filter(Address.id == address_id, Address.user_id == user_id).first()
        if not addr:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Address not found")

        was_default = bool(addr.is_default)
        db.delete(addr)
        db.commit()

        # If deleted address was default, set the latest remaining address as default
        if was_default:
            next_addr = (
                db.query(Address)
                .filter(Address.user_id == user_id)
                .order_by(desc(Address.id))
                .first()
            )
            if next_addr:
                next_addr.is_default = 1
                db.commit()

        return {
            "status": "success",
            "message": "Address deleted successfully"
        }

    @classmethod
    def set_default_address(cls, address_id: int, user_id: int, db: Session) -> dict:
        addr = db.query(Address).filter(Address.id == address_id, Address.user_id == user_id).first()
        if not addr:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Address not found")

        db.query(Address).filter(Address.user_id == user_id).update({"is_default": 0})
        addr.is_default = 1
        db.commit()
        db.refresh(addr)

        return {
            "status": "success",
            "message": "Default address updated",
            "address": cls._format_address(addr)
        }
