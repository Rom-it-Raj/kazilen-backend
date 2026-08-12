from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.database import get_db
from app.schemas.review import (
    ReviewHistoryResponse,
    ReviewResponse,
    ReviewStatus,
    ReviewSubmission,
    PlatformFeedbackMeResponse,
)
from app.services.review_service import (
    get_review_status,
    get_review_history,
    submit_participant_review,
    submit_platform_feedback,
    get_user_platform_feedback,
    submit_user_platform_feedback,
    update_participant_review,
    update_platform_feedback,
)

router = APIRouter()


@router.get("/platform/me", response_model=PlatformFeedbackMeResponse)
def get_my_platform_feedback_endpoint(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_user_platform_feedback(current_user.id, db)


@router.post("/platform", response_model=ReviewResponse)
def submit_my_platform_feedback_endpoint(
    submission: ReviewSubmission,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return submit_user_platform_feedback(
        current_user.id,
        submission.rating,
        submission.description,
        db,
    )


@router.get("/my", response_model=ReviewHistoryResponse)
def get_my_review_history_endpoint(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_review_history(current_user.id, db)


@router.get("/bookings/{booking_id}/status", response_model=ReviewStatus)
def get_review_status_endpoint(
    booking_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_review_status(booking_id, current_user.id, db)


@router.post("/bookings/{booking_id}/participant", response_model=ReviewResponse)
def submit_participant_review_endpoint(
    booking_id: int,
    submission: ReviewSubmission,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return submit_participant_review(
        booking_id,
        current_user.id,
        submission.rating,
        submission.description,
        db,
    )


@router.post("/bookings/{booking_id}/platform", response_model=ReviewResponse)
def submit_platform_feedback_endpoint(
    booking_id: int,
    submission: ReviewSubmission,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return submit_platform_feedback(
        booking_id,
        current_user.id,
        submission.rating,
        submission.description,
        db,
    )


@router.put("/participant/{review_id}", response_model=ReviewResponse)
def update_participant_review_endpoint(
    review_id: int,
    submission: ReviewSubmission,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return update_participant_review(
        review_id,
        current_user.id,
        submission.rating,
        submission.description,
        db,
    )


@router.put("/platform/{feedback_id}", response_model=ReviewResponse)
def update_platform_feedback_endpoint(
    feedback_id: int,
    submission: ReviewSubmission,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return update_platform_feedback(
        feedback_id,
        current_user.id,
        submission.rating,
        submission.description,
        db,
    )
