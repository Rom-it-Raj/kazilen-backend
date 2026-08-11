from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class ReviewSubmission(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    description: str = Field(..., min_length=1, max_length=2000)


class ReviewStatus(BaseModel):
    participant_review_submitted: bool
    platform_feedback_submitted: bool


class ReviewResponse(BaseModel):
    status: str
    review_type: str
    id: int
    created_at: Optional[datetime] = None


class ReviewHistoryItem(BaseModel):
    id: int
    booking_id: int
    service_id: str
    booking_date: str
    reviewee_name: str
    rating: int
    description: str
    created_at: Optional[datetime] = None
    editable: bool
    editable_until: Optional[datetime] = None


class PlatformFeedbackHistoryItem(BaseModel):
    id: int
    booking_id: int
    service_id: str
    booking_date: str
    rating: int
    description: str
    created_at: Optional[datetime] = None
    editable: bool
    editable_until: Optional[datetime] = None


class ReceivedReviewItem(BaseModel):
    id: int
    booking_id: int
    service_id: str
    booking_date: str
    reviewer_name: str
    rating: int
    description: str
    created_at: Optional[datetime] = None


class ReviewHistoryResponse(BaseModel):
    reviews: List[ReviewHistoryItem]
    received_reviews: Optional[List[ReceivedReviewItem]] = []
    platform_feedback: List[PlatformFeedbackHistoryItem]
    average_rating: Optional[float] = None
    total_reviews_count: int = 0
