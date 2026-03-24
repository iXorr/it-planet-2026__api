from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import datetime
from models import UserRole, OpportunityType, WorkFormat, ApplicationStatus
from typing import List, Optional


class Token(BaseModel):
    access_token: str
    token_type: str

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    role: UserRole

class UserLogin(BaseModel):
    email: EmailStr
    password: str

# --- Profiles ---
class SeekerProfileCreate(BaseModel):
    full_name: str
    university: str
    graduation_year: int
    resume_json: Optional[str] = None
    is_public: bool = False

class EmployerProfileCreate(BaseModel):
    company_name: str
    inn: str
    description: Optional[str] = None
    website: Optional[str] = None
    verification_docs: Optional[str] = None

class EmployerProfileVerify(BaseModel):
    is_verified: bool


class OpportunityCreate(BaseModel):
    title: str
    description: str
    op_type: OpportunityType
    work_format: WorkFormat
    city: str
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    deadline: Optional[datetime] = None
    tag_names: List[str] = []

class OpportunityResponse(OpportunityCreate):
    id: int
    owner_id: int
    published_at: datetime
    is_active: bool
    company_name: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)

class CuratorCreate(BaseModel):
    email: EmailStr
    password: str