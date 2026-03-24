from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, ForeignKey, Table, Text, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from database import Base

class UserRole(str, enum.Enum):
    SEEKER = "seeker"
    EMPLOYER = "employer"
    CURATOR = "curator"

class OpportunityType(str, enum.Enum):
    INTERNSHIP = "internship"
    VACANCY = "vacancy"
    MENTORSHIP = "mentorship"
    EVENT = "event"

class WorkFormat(str, enum.Enum):
    OFFICE = "office"
    HYBRID = "hybrid"
    REMOTE = "remote"

class ApplicationStatus(str, enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    RESERVE = "reserve"

opportunity_tags = Table('opportunity_tags', Base.metadata,
    Column('opportunity_id', Integer, ForeignKey('opportunities.id')),
    Column('tag_id', Integer, ForeignKey('tags.id'))
)

contacts = Table('contacts', Base.metadata,
    Column('user_id_1', Integer, ForeignKey('users.id')),
    Column('user_id_2', Integer, ForeignKey('users.id')),
    Column('status', String, default='pending') # pending, accepted
)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


    seeker_profile = relationship("SeekerProfile", back_populates="user", uselist=False)
    employer_profile = relationship("EmployerProfile", back_populates="user", uselist=False)
    opportunities = relationship("Opportunity", back_populates="owner")
    applications = relationship("Application", back_populates="seeker")
    favorites = relationship("Favorite", back_populates="user")

class SeekerProfile(Base):
    __tablename__ = "seeker_profiles"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    full_name = Column(String)
    university = Column(String)
    graduation_year = Column(Integer)
    resume_json = Column(Text)
    is_public = Column(Boolean, default=False)
    
    user = relationship("User", back_populates="seeker_profile")

class EmployerProfile(Base):
    __tablename__ = "employer_profiles"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    company_name = Column(String, nullable=False)
    inn = Column(String) 
    description = Column(Text)
    website = Column(String)
    is_verified = Column(Boolean, default=False) 
    verification_docs = Column(Text) 
    
    user = relationship("User", back_populates="employer_profile")

class Tag(Base):
    __tablename__ = "tags"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    category = Column(String)

class Opportunity(Base):
    __tablename__ = "opportunities"
    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String, nullable=False)
    description = Column(Text)
    op_type = Column(Enum(OpportunityType))
    work_format = Column(Enum(WorkFormat))
    city = Column(String)
    address = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    salary_min = Column(Integer)
    salary_max = Column(Integer)
    published_at = Column(DateTime(timezone=True), server_default=func.now())
    deadline = Column(DateTime(timezone=True))
    is_active = Column(Boolean, default=True)
    
    owner = relationship("User", back_populates="opportunities")
    tags = relationship("Tag", secondary=opportunity_tags)
    applications = relationship("Application", back_populates="opportunity")
    favorites = relationship("Favorite", back_populates="opportunity")

class Application(Base):
    __tablename__ = "applications"
    id = Column(Integer, primary_key=True, index=True)
    opportunity_id = Column(Integer, ForeignKey("opportunities.id"))
    seeker_id = Column(Integer, ForeignKey("users.id"))
    status = Column(Enum(ApplicationStatus), default=ApplicationStatus.PENDING)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    opportunity = relationship("Opportunity", back_populates="applications")
    seeker = relationship("User", back_populates="applications")

class Favorite(Base):
    __tablename__ = "favorites"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    opportunity_id = Column(Integer, ForeignKey("opportunities.id"))
    
    user = relationship("User", back_populates="favorites")
    opportunity = relationship("Opportunity", back_populates="favorites")