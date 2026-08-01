from pydantic import BaseModel
from typing import Optional, List

class WorkerResponseSchema(BaseModel):
    id: int
    full_name: str
    phone_number: str
    rating: float = 4.9
    locality: str = "Dharampeth, Nagpur"
    eta: str = "Arrives in 30 mins"
    jobs_completed: str = "150+"

class WorkerListResponseSchema(BaseModel):
    status: str
    workers: List[WorkerResponseSchema]
