"""Auth request/response schemas."""

from pydantic import BaseModel


class RegisterRequest(BaseModel):
    name: str
    password: str


class LoginRequest(BaseModel):
    name: str
    password: str


class UserResponse(BaseModel):
    id: int
    name: str


class LoginResponse(BaseModel):
    token: str
    id: int
    name: str
