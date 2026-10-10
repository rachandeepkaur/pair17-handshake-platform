from pydantic import BaseModel, EmailStr, Field


class CompanySignupRequest(BaseModel):
    company_name: str = Field(min_length=2, max_length=190)
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    location: str = Field(min_length=2, max_length=190)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
