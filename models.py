# models.py
from pydantic import BaseModel
from typing import Optional


class UserRegister(BaseModel):
    fullName: str
    mobile: int
    employeeId: int
    department: str


class AttendanceAction(BaseModel):
    user_id: int
    location: Optional[dict] = None  # Expected: {"latitude": ..., "longitude": ...}


class CheckStatusRequest(BaseModel):
    user_id: int
