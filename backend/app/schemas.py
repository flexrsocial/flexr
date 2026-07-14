from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    name: str = Field(min_length=1, max_length=100)
    age: int = Field(ge=18, le=99)
    city: str
    gender: Literal["mann", "frau"]
    interest: Literal["mann", "frau"]
    gym: str
    height_cm: Optional[int] = Field(default=None, ge=120, le=230)
    weight_kg: Optional[int] = Field(default=None, ge=30, le=250)
    bio: Optional[str] = Field(default=None, max_length=280)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class PhotoOut(BaseModel):
    id: str
    url: str
    position: int

    class Config:
        from_attributes = True


class PresignPhotoRequest(BaseModel):
    content_type: Literal["image/jpeg", "image/png", "image/webp"]


class PresignPhotoResponse(BaseModel):
    upload_url: str
    object_key: str


class AddPhotoRequest(BaseModel):
    object_key: str


class ProfileOut(BaseModel):
    id: str
    name: str
    age: int
    city: str
    gender: str
    gym: str
    height_cm: Optional[int]
    weight_kg: Optional[int]
    bio: Optional[str]
    photos: list[PhotoOut] = []

    class Config:
        from_attributes = True


class MembershipStatus(BaseModel):
    is_subscribed: bool
    trial_ends_at: datetime
    is_active: bool


class SwipeRequest(BaseModel):
    to_user_id: str
    action: Literal["like", "pass"]


class SwipeResult(BaseModel):
    matched: bool


class ReportRequest(BaseModel):
    reported_user_id: str
    reason: str = Field(min_length=3, max_length=500)


class BlockRequest(BaseModel):
    user_id: str
