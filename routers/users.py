from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import models, schemas, auth, database
from typing import List, Optional

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/me")
def get_me(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    profile = None
    if current_user.role == models.UserRole.SEEKER:
        profile = db.query(models.SeekerProfile).filter(
            models.SeekerProfile.user_id == current_user.id
        ).first()
    elif current_user.role == models.UserRole.EMPLOYER:
        profile = db.query(models.EmployerProfile).filter(
            models.EmployerProfile.user_id == current_user.id
        ).first()
    
    return {
        "id": current_user.id,
        "email": current_user.email,
        "role": current_user.role,
        "is_active": current_user.is_active,
        "profile": profile
    }

@router.put("/profile/seeker")
def update_seeker_profile(
    profile_data: schemas.SeekerProfileCreate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    if current_user.role != models.UserRole.SEEKER:
        raise HTTPException(status_code=403, detail="Not a seeker account")
    
    profile = db.query(models.SeekerProfile).filter(
        models.SeekerProfile.user_id == current_user.id
    ).first()
    
    if not profile:
        profile = models.SeekerProfile(user_id=current_user.id)
        db.add(profile)
    
    for field, value in profile_data.model_dump().items():
        setattr(profile, field, value)
    
    db.commit()
    db.refresh(profile)
    return profile

@router.put("/profile/employer")
def update_employer_profile(
    profile_data: schemas.EmployerProfileCreate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    if current_user.role != models.UserRole.EMPLOYER:
        raise HTTPException(status_code=403, detail="Not an employer account")
    
    profile = db.query(models.EmployerProfile).filter(
        models.EmployerProfile.user_id == current_user.id
    ).first()
    
    if not profile:
        profile = models.EmployerProfile(user_id=current_user.id)
        db.add(profile)
    
    if profile.inn != profile_data.inn and profile.inn is not None:
        profile.is_verified = False
    
    for field, value in profile_data.model_dump().items():
        setattr(profile, field, value)
    
    db.commit()
    db.refresh(profile)
    return profile

@router.post("/contacts/{target_user_id}")
def add_contact(
    target_user_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    if current_user.role != models.UserRole.SEEKER:
        raise HTTPException(status_code=403, detail="Only seekers can use networking")
    
    if target_user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot add yourself")
    
    target = db.query(models.User).filter(models.User.id == target_user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    
    existing = db.query(models.contacts).filter(
        ((models.contacts.c.user_id_1 == current_user.id) & 
         (models.contacts.c.user_id_2 == target_user_id)) |
        ((models.contacts.c.user_id_1 == target_user_id) & 
         (models.contacts.c.user_id_2 == current_user.id))
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Contact already exists")
    
    db.execute(
        models.contacts.insert().values(
            user_id_1=current_user.id,
            user_id_2=target_user_id,
            status="pending"
        )
    )
    db.commit()
    return {"status": "contact request sent", "target_user_id": target_user_id}

@router.get("/contacts")
def get_contacts(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    if current_user.role != models.UserRole.SEEKER:
        raise HTTPException(status_code=403, detail="Only seekers can use networking")
    
    # Получаем все связи текущего пользователя
    contacts_query = db.query(models.User).join(
        models.contacts,
        ((models.contacts.c.user_id_2 == models.User.id) & 
         (models.contacts.c.user_id_1 == current_user.id)) |
        ((models.contacts.c.user_id_1 == models.User.id) & 
         (models.contacts.c.user_id_2 == current_user.id))
    ).filter(models.User.role == models.UserRole.SEEKER).all()
    
    return [
        {
            "id": c.id,
            "email": c.email,
            "profile": c.seeker_profile
        } for c in contacts_query
    ]