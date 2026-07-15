from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import List, Optional, Dict, Any

class RegisterRequest(BaseModel):
    email: str
    password: str
    role: str = "candidate"

class LoginRequest(BaseModel):
    email: str
    password: str

class ProfileUpdateRequest(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    college: Optional[str] = None
    education_level: Optional[str] = None
    degree: Optional[str] = None
    branch: Optional[str] = None
    graduation_year: Optional[int] = None
    cgpa: Optional[float] = None
    skills: Optional[List[str]] = None
    interests: Optional[List[str]] = None
    preferred_industry: Optional[str] = None
    preferred_job_role: Optional[str] = None
    preferred_location: Optional[str] = None

    @field_validator('graduation_year', mode='before')
    @classmethod
    def empty_str_to_none_int(cls, v):
        if v == "":
            return None
        return v

    @field_validator('cgpa', mode='before')
    @classmethod
    def empty_str_to_none_float(cls, v):
        if v == "":
            return None
        return v

class InternshipCreateRequest(BaseModel):
    company_name: str
    company_logo: Optional[str] = None
    title: str
    description: str
    responsibilities: Optional[str] = None
    required_skills: Optional[List[str]] = None
    eligibility_criteria: Optional[str] = None
    degree_requirement: Optional[str] = None
    branch_requirement: Optional[List[str]] = None
    location: str
    mode: str
    duration: int
    stipend: int
    industry: Optional[str] = None
    category: Optional[str] = None
    application_deadline: Optional[str] = None
