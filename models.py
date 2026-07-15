import json
from datetime import datetime
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship
from passlib.context import CryptContext

# CryptContext for password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class User(SQLModel, table=True):
    __tablename__ = 'users'
    
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True, nullable=False)
    password_hash: str = Field(nullable=False)
    role: str = Field(default='candidate')  # 'candidate' or 'admin'
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    profile: Optional["Profile"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"uselist": False, "cascade": "all, delete-orphan"}
    )
    saved_internships: List["SavedInternship"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    recommendations: List["RecommendationHistory"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    applications: List["ApplicationHistory"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    
    def set_password(self, password: str):
        self.password_hash = pwd_context.hash(password)
        
    def check_password(self, password: str) -> bool:
        return pwd_context.verify(password, self.password_hash)

class Profile(SQLModel, table=True):
    __tablename__ = 'profiles'
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key='users.id', unique=True, nullable=False)
    full_name: str = Field(nullable=False)
    phone: Optional[str] = Field(default=None, nullable=True)
    college: Optional[str] = Field(default=None, nullable=True)
    education_level: Optional[str] = Field(default=None, nullable=True)
    degree: Optional[str] = Field(default=None, nullable=True)
    branch: Optional[str] = Field(default=None, nullable=True)
    graduation_year: Optional[int] = Field(default=None, nullable=True)
    cgpa: Optional[float] = Field(default=None, nullable=True)
    
    # Stored as JSON strings (avoiding leading underscores for Pydantic)
    skills_raw: str = Field(default='[]')
    interests_raw: str = Field(default='[]')
    
    preferred_industry: Optional[str] = Field(default=None, nullable=True)
    preferred_job_role: Optional[str] = Field(default=None, nullable=True)
    preferred_location: Optional[str] = Field(default=None, nullable=True)
    resume_filename: Optional[str] = Field(default=None, nullable=True)
    
    # Relationships
    user: Optional[User] = Relationship(back_populates="profile")
    
    def __init__(self, **data):
        skills = data.pop("skills", None)
        interests = data.pop("interests", None)
        super().__init__(**data)
        if skills is not None:
            self.skills = skills
        if interests is not None:
            self.interests = interests
    
    @property
    def skills(self) -> list:
        try:
            return json.loads(self.skills_raw) if self.skills_raw else []
        except:
            return []
            
    @skills.setter
    def skills(self, value):
        self.skills_raw = json.dumps(value if isinstance(value, list) else [])
        
    @property
    def interests(self) -> list:
        try:
            return json.loads(self.interests_raw) if self.interests_raw else []
        except:
            return []
            
    @interests.setter
    def interests(self, value):
        self.interests_raw = json.dumps(value if isinstance(value, list) else [])

class Internship(SQLModel, table=True):
    __tablename__ = 'internships'
    
    id: Optional[int] = Field(default=None, primary_key=True)
    company_name: str = Field(nullable=False)
    company_logo: Optional[str] = Field(default=None, nullable=True)
    title: str = Field(nullable=False)
    description: str = Field(nullable=False)
    responsibilities: Optional[str] = Field(default=None, nullable=True)
    
    # Stored as JSON strings
    required_skills_raw: str = Field(default='[]')
    
    eligibility_criteria: Optional[str] = Field(default=None, nullable=True)
    degree_requirement: Optional[str] = Field(default=None, nullable=True)
    
    # Stored as JSON strings
    branch_requirement_raw: str = Field(default='[]')
    
    location: str = Field(nullable=False)
    mode: str = Field(nullable=False)  # 'Remote', 'Hybrid', 'Onsite'
    duration: int = Field(nullable=False)  # in months
    stipend: int = Field(nullable=False)  # per month in INR
    industry: Optional[str] = Field(default=None, nullable=True)
    category: Optional[str] = Field(default=None, nullable=True)
    application_deadline: Optional[str] = Field(default=None, nullable=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    def __init__(self, **data):
        required_skills = data.pop("required_skills", None)
        branch_requirement = data.pop("branch_requirement", None)
        super().__init__(**data)
        if required_skills is not None:
            self.required_skills = required_skills
        if branch_requirement is not None:
            self.branch_requirement = branch_requirement
            
    @property
    def required_skills(self) -> list:
        try:
            return json.loads(self.required_skills_raw) if self.required_skills_raw else []
        except:
            return []
            
    @required_skills.setter
    def required_skills(self, value):
        self.required_skills_raw = json.dumps(value if isinstance(value, list) else [])
        
    @property
    def branch_requirement(self) -> list:
        try:
            return json.loads(self.branch_requirement_raw) if self.branch_requirement_raw else []
        except:
            return []
            
    @branch_requirement.setter
    def branch_requirement(self, value):
        self.branch_requirement_raw = json.dumps(value if isinstance(value, list) else [])

class SavedInternship(SQLModel, table=True):
    __tablename__ = 'saved_internships'
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key='users.id', nullable=False)
    internship_id: int = Field(foreign_key='internships.id', nullable=False)
    status: str = Field(default='saved')  # 'saved' or 'applied'
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    user: Optional[User] = Relationship(back_populates="saved_internships")
    internship: Optional[Internship] = Relationship()

class RecommendationHistory(SQLModel, table=True):
    __tablename__ = 'recommendation_histories'
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key='users.id', nullable=False)
    internship_id: int = Field(foreign_key='internships.id', nullable=False)
    score: float = Field(nullable=False)
    
    # Stored details for explainable AI
    reasons_raw: str = Field(default='[]')
    missing_skills_raw: str = Field(default='[]')
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    user: Optional[User] = Relationship(back_populates="recommendations")
    internship: Optional[Internship] = Relationship()
    
    def __init__(self, **data):
        reasons = data.pop("reasons", None)
        missing_skills = data.pop("missing_skills", None)
        super().__init__(**data)
        if reasons is not None:
            self.reasons = reasons
        if missing_skills is not None:
            self.missing_skills = missing_skills
            
    @property
    def reasons(self) -> list:
        try:
            return json.loads(self.reasons_raw) if self.reasons_raw else []
        except:
            return []
            
    @reasons.setter
    def reasons(self, value):
        self.reasons_raw = json.dumps(value if isinstance(value, list) else [])
        
    @property
    def missing_skills(self) -> list:
        try:
            return json.loads(self.missing_skills_raw) if self.missing_skills_raw else []
        except:
            return []
            
    @missing_skills.setter
    def missing_skills(self, value):
        self.missing_skills_raw = json.dumps(value if isinstance(value, list) else [])

class ApplicationHistory(SQLModel, table=True):
    __tablename__ = 'application_histories'
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key='users.id', nullable=False)
    internship_id: int = Field(foreign_key='internships.id', nullable=False)
    applied_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    user: Optional[User] = Relationship(back_populates="applications")
    internship: Optional[Internship] = Relationship()
