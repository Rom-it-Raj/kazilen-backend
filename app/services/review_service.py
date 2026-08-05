from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.db.models import Booking, BookingReview, PlatformFeedback, User

EDIT_WINDOW = timedelta(minutes=15)


def _get_completed_booking(db: Session, booking_id: int, user_id: int) -> Booking:
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if user_id not in (booking.customer_id, booking.worker_id):
        raise HTTPException(status_code=403, detail="Access denied")
    if booking.status != "completed":
        raise HTTPException(status_code=400, detail="Reviews can be submitted after the job is completed")
    return booking


def _edit_details(created_at):
    if not created_at:
        return False, None
    created_utc = created_at.replace(tzinfo=timezone.utc) if created_at.tzinfo is None else created_at.astimezone(timezone.utc)
    editable_until = created_utc + EDIT_WINDOW
    return datetime.now(timezone.utc) < editable_until, editable_until


def get_review_history(user_id: int, db: Session) -> dict:
    participant_rows = (
        db.query(BookingReview, Booking, User)
        .join(Booking, Booking.id == BookingReview.booking_id)
        .join(User, User.id == BookingReview.reviewee_id)
        .filter(BookingReview.reviewer_id == user_id)
        .order_by(BookingReview.created_at.desc())
        .all()
    )
    platform_rows = (
        db.query(PlatformFeedback, Booking)
        .join(Booking, Booking.id == PlatformFeedback.booking_id)
        .filter(PlatformFeedback.user_id == user_id)
        .order_by(PlatformFeedback.created_at.desc())
        .all()
    )

    reviews = []
    for review, booking, reviewee in participant_rows:
        editable, editable_until = _edit_details(review.created_at)
        reviews.append({
            "id": review.id,
            "booking_id": booking.id,
            "service_id": booking.service_id,
            "booking_date": booking.date,
            "reviewee_name": reviewee.full_name or "Kazilen participant",
            "rating": review.rating,
            "description": review.description,
            "created_at": review.created_at,
            "editable": editable,
            "editable_until": editable_until,
        })

    platform_feedback = []
    for feedback, booking in platform_rows:
        editable, editable_until = _edit_details(feedback.created_at)
        platform_feedback.append({
            "id": feedback.id,
            "booking_id": booking.id,
            "service_id": booking.service_id,
            "booking_date": booking.date,
            "rating": feedback.rating,
            "description": feedback.description,
            "created_at": feedback.created_at,
            "editable": editable,
            "editable_until": editable_until,
        })

    return {"reviews": reviews, "platform_feedback": platform_feedback}


def _ensure_editable(created_at):
    editable, _ = _edit_details(created_at)
    if not editable:
        raise HTTPException(status_code=403, detail="Reviews can only be edited for 15 minutes after submission")


def get_review_status(booking_id: int, user_id: int, db: Session) -> dict:
    _get_completed_booking(db, booking_id, user_id)
    participant_review = (
        db.query(BookingReview)
        .filter(BookingReview.booking_id == booking_id, BookingReview.reviewer_id == user_id)
        .first()
    )
    platform_feedback = (
        db.query(PlatformFeedback)
        .filter(PlatformFeedback.booking_id == booking_id, PlatformFeedback.user_id == user_id)
        .first()
    )
    return {
        "participant_review_submitted": participant_review is not None,
        "platform_feedback_submitted": platform_feedback is not None,
    }


def submit_participant_review(booking_id: int, user_id: int, rating: int, description: str, db: Session) -> dict:
    booking = _get_completed_booking(db, booking_id, user_id)
    reviewee_id = booking.worker_id if user_id == booking.customer_id else booking.customer_id
    existing = (
        db.query(BookingReview)
        .filter(BookingReview.booking_id == booking_id, BookingReview.reviewer_id == user_id)
        .first()
    )
    if existing:
        raise HTTPException(status_code=409, detail="You have already reviewed this job")

    clean_description = description.strip()
    if not clean_description:
        raise HTTPException(status_code=422, detail="Description cannot be empty")

    review = BookingReview(
        booking_id=booking_id,
        reviewer_id=user_id,
        reviewee_id=reviewee_id,
        rating=rating,
        description=clean_description,
    )
    db.add(review)
    db.commit()
    db.refresh(review)
    return {
        "status": "success",
        "review_type": "participant",
        "id": review.id,
        "created_at": review.created_at,
    }


def submit_platform_feedback(booking_id: int, user_id: int, rating: int, description: str, db: Session) -> dict:
    _get_completed_booking(db, booking_id, user_id)
    existing = (
        db.query(PlatformFeedback)
        .filter(PlatformFeedback.booking_id == booking_id, PlatformFeedback.user_id == user_id)
        .first()
    )
    if existing:
        raise HTTPException(status_code=409, detail="You have already submitted feedback for this job")

    clean_description = description.strip()
    if not clean_description:
        raise HTTPException(status_code=422, detail="Description cannot be empty")

    feedback = PlatformFeedback(
        booking_id=booking_id,
        user_id=user_id,
        rating=rating,
        description=clean_description,
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    return {
        "status": "success",
        "review_type": "platform",
        "id": feedback.id,
        "created_at": feedback.created_at,
    }


def update_participant_review(review_id: int, user_id: int, rating: int, description: str, db: Session) -> dict:
    review = db.query(BookingReview).filter(
        BookingReview.id == review_id,
        BookingReview.reviewer_id == user_id,
    ).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    booking = _get_completed_booking(db, review.booking_id, user_id)
    _ensure_editable(review.created_at)
    clean_description = description.strip()
    if not clean_description:
        raise HTTPException(status_code=422, detail="Description cannot be empty")

    review.rating = rating
    review.description = clean_description
    db.commit()
    db.refresh(review)
    return {
        "status": "success",
        "review_type": "participant",
        "id": review.id,
        "created_at": review.created_at,
    }


def update_platform_feedback(feedback_id: int, user_id: int, rating: int, description: str, db: Session) -> dict:
    feedback = db.query(PlatformFeedback).filter(
        PlatformFeedback.id == feedback_id,
        PlatformFeedback.user_id == user_id,
    ).first()
    if not feedback:
        raise HTTPException(status_code=404, detail="Platform feedback not found")
    _get_completed_booking(db, feedback.booking_id, user_id)
    _ensure_editable(feedback.created_at)
    clean_description = description.strip()
    if not clean_description:
        raise HTTPException(status_code=422, detail="Description cannot be empty")

    feedback.rating = rating
    feedback.description = clean_description
    db.commit()
    db.refresh(feedback)
    return {
        "status": "success",
        "review_type": "platform",
        "id": feedback.id,
        "created_at": feedback.created_at,
    }
