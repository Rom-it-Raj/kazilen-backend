"""
Booking business logic layer.

OTP flow:
 1. Customer books → status=pending (no OTP yet)
 2. Worker accepts → status=accepted
 3. Worker at site: generates start_otp → shown on worker screen → worker verifies it → status=in_progress
 4. Job done: Worker generates end_otp → shown on worker screen → worker verifies it → status=completed
"""

import random
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import Booking, User


def _generate_otp() -> str:
    """Returns a random 6-digit OTP string."""
    return str(random.randint(100000, 999999))


def _get_db_session() -> Session:
    return next(get_db())


# ---------------------------------------------------------------------------
# Customer: create booking
# ---------------------------------------------------------------------------

def create_booking(booking_data, customer_id: int) -> Booking:
    db = _get_db_session()
    new_slot = booking_data.time_slot

    # Fetch all active bookings for this worker on this date
    existing = (
        db.query(Booking)
        .filter(
            Booking.worker_id == booking_data.worker_id,
            Booking.date == booking_data.date,
            Booking.status.in_(["pending", "accepted", "in_progress"]),
        )
        .all()
    )

    is_asap = "ASAP" in new_slot.upper() or "INSTANT" in new_slot.upper()
    if is_asap:
        for b in existing:
            if b.customer_id == customer_id and ("ASAP" in b.time_slot.upper() or "INSTANT" in b.time_slot.upper()):
                raise HTTPException(
                    status_code=409,
                    detail="You already have an active Instant ASAP booking with this worker.",
                )
    else:
        for b in existing:
            if _slots_overlap(new_slot, b.time_slot):
                # Distinguish: is it the same customer re-booking?
                if b.customer_id == customer_id:
                    raise HTTPException(
                        status_code=409,
                        detail="You already have an active booking for this worker at this time.",
                    )
                raise HTTPException(
                    status_code=409,
                    detail="This worker is already booked during that time. Please choose a different slot.",
                )

    booking = Booking(
        customer_id=customer_id,
        worker_id=booking_data.worker_id,
        service_id=booking_data.service_id,
        date=booking_data.date,
        time_slot=booking_data.time_slot,
        address=booking_data.address,
        amount=booking_data.amount,
        status="pending",
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)
    print(f"[BOOKING] New booking #{booking.id} created for customer {customer_id}, worker {booking_data.worker_id}")
    return booking



# ---------------------------------------------------------------------------
# Public: get booked slots for a worker on a date
# ---------------------------------------------------------------------------

def _parse_slot_hours(time_slot: str) -> list[int]:
    """Parse 'HH:MM-HH:MM' → list of occupied start-hours (ints).
    E.g. '09:00-11:00' → [9, 10]."""
    try:
        start_str, end_str = time_slot.split("-", 1)
        start_h = int(start_str.split(":")[0])
        end_h = int(end_str.split(":")[0])
        return list(range(start_h, end_h))
    except Exception:
        return []


def _slots_overlap(a: str, b: str) -> bool:
    """Return True if time slot strings a and b share at least one hour."""
    return bool(set(_parse_slot_hours(a)) & set(_parse_slot_hours(b)))


# ---------------------------------------------------------------------------
# Public: get booked slots for a worker on a date
# ---------------------------------------------------------------------------

def get_booked_slots(worker_id: int, date: str) -> dict:
    """Returns individual booked hour-start strings for the worker on the date.
    E.g. if '09:00-11:00' is booked → returns ['09:00', '10:00'].
    Only active statuses: pending, accepted, in_progress."""
    db = _get_db_session()
    rows = (
        db.query(Booking.time_slot)
        .filter(
            Booking.worker_id == worker_id,
            Booking.date == date,
            Booking.status.in_(["pending", "accepted", "in_progress"]),
        )
        .all()
    )
    occupied = set()
    for (slot,) in rows:
        for h in _parse_slot_hours(slot):
            occupied.add(f"{str(h).zfill(2)}:00")
    return {"booked_hours": sorted(occupied)}



# ---------------------------------------------------------------------------
# Customer: list own bookings
# ---------------------------------------------------------------------------

def get_customer_bookings(customer_id: int) -> dict:
    db = _get_db_session()
    bookings = (
        db.query(Booking)
        .filter(Booking.customer_id == customer_id)
        .order_by(Booking.created_at.desc())
        .all()
    )
    return {"status": "success", "bookings": bookings}


# ---------------------------------------------------------------------------
# Worker: list incoming bookings
# ---------------------------------------------------------------------------

def get_worker_bookings(worker_id: int) -> dict:
    """Returns pending, accepted and in_progress bookings for the worker."""
    db = _get_db_session()
    bookings = (
        db.query(Booking)
        .filter(
            Booking.worker_id == worker_id,
            Booking.status.in_(["pending", "accepted", "in_progress"])
        )
        .order_by(Booking.created_at.desc())
        .all()
    )
    return {"status": "success", "bookings": bookings}


# ---------------------------------------------------------------------------
# Shared: get single booking detail
# ---------------------------------------------------------------------------

def get_booking_detail(booking_id: int, user_id: int) -> Booking:
    db = _get_db_session()
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.customer_id != user_id and booking.worker_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    return booking


# ---------------------------------------------------------------------------
# Worker: accept booking
# ---------------------------------------------------------------------------

def accept_booking(booking_id: int, worker_id: int) -> dict:
    db = _get_db_session()
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.worker_id != worker_id:
        raise HTTPException(status_code=403, detail="This booking is not assigned to you")
    if booking.status != "pending":
        raise HTTPException(status_code=400, detail=f"Booking is already {booking.status}")
    booking.status = "accepted"
    db.commit()
    print(f"[BOOKING] #{booking_id} accepted by worker {worker_id}")
    return {"status": "accepted", "booking_id": booking_id, "message": "Booking accepted"}


# ---------------------------------------------------------------------------
# Worker: generate start OTP (to begin job at customer site)
# ---------------------------------------------------------------------------

def generate_start_otp(booking_id: int, worker_id: int) -> dict:
    db = _get_db_session()
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.worker_id != worker_id:
        raise HTTPException(status_code=403, detail="Access denied")
    if booking.status != "accepted":
        raise HTTPException(status_code=400, detail=f"Cannot generate OTP. Booking status is '{booking.status}'. Must be 'accepted'.")
    otp = _generate_otp()
    booking.start_otp = otp
    db.commit()
    print(f"[BOOKING] Start OTP for #{booking_id}: {otp}")
    return {"status": "success", "otp": otp, "booking_id": booking_id}


# ---------------------------------------------------------------------------
# Worker: verify start OTP → transitions to in_progress
# ---------------------------------------------------------------------------

def verify_start_otp(booking_id: int, worker_id: int, otp: str) -> dict:
    db = _get_db_session()
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.worker_id != worker_id:
        raise HTTPException(status_code=403, detail="Access denied")
    if not booking.start_otp:
        raise HTTPException(status_code=400, detail="Start OTP has not been generated yet")
    if booking.start_otp != otp and otp != "123456":  # dev master bypass
        raise HTTPException(status_code=400, detail="Incorrect OTP. Please try again.")
    booking.status = "in_progress"
    db.commit()
    print(f"[BOOKING] #{booking_id} start OTP verified — job in progress")
    return {"status": "in_progress", "booking_id": booking_id, "message": "Job started successfully"}


# ---------------------------------------------------------------------------
# Worker: generate end OTP (to close job)
# ---------------------------------------------------------------------------

def generate_end_otp(booking_id: int, worker_id: int) -> dict:
    db = _get_db_session()
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.worker_id != worker_id:
        raise HTTPException(status_code=403, detail="Access denied")
    if booking.status != "in_progress":
        raise HTTPException(status_code=400, detail=f"Cannot generate end OTP. Booking status is '{booking.status}'. Must be 'in_progress'.")
    otp = _generate_otp()
    booking.end_otp = otp
    db.commit()
    print(f"[BOOKING] End OTP for #{booking_id}: {otp}")
    return {"status": "success", "otp": otp, "booking_id": booking_id}


# ---------------------------------------------------------------------------
# Worker: verify end OTP → transitions to completed
# ---------------------------------------------------------------------------

def verify_end_otp(booking_id: int, worker_id: int, otp: str) -> dict:
    db = _get_db_session()
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.worker_id != worker_id:
        raise HTTPException(status_code=403, detail="Access denied")
    if not booking.end_otp:
        raise HTTPException(status_code=400, detail="End OTP has not been generated yet")
    if booking.end_otp != otp and otp != "123456":  # dev master bypass
        raise HTTPException(status_code=400, detail="Incorrect OTP. Please try again.")
    booking.status = "completed"
    db.commit()
    print(f"[BOOKING] #{booking_id} end OTP verified — job completed")
    return {"status": "completed", "booking_id": booking_id, "message": "Job completed successfully"}
