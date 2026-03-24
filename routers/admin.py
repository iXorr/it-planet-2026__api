from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import models, schemas, auth, database

router = APIRouter(prefix="/admin", tags=["Curator"])

def get_curator_or_403(
    current_user: models.User = Depends(auth.get_current_user)
):
    if current_user.role != models.UserRole.CURATOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Curator access required"
        )
    return current_user

@router.post("/verify-employer/{employer_user_id}")
def verify_employer(
    employer_user_id: int,
    verification: schemas.EmployerProfileVerify,
    current_user: models.User = Depends(get_curator_or_403),
    db: Session = Depends(database.get_db)
):
    profile = db.query(models.EmployerProfile).filter(
        models.EmployerProfile.user_id == employer_user_id
    ).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Employer not found")
    
    profile.is_verified = verification.is_verified
    db.commit()
    return {"status": "verification updated", "employer_id": employer_user_id}

@router.post("/moderate-opportunity/{opp_id}")
def moderate_opportunity(
    opp_id: int,
    is_active: bool,
    current_user: models.User = Depends(get_curator_or_403),
    db: Session = Depends(database.get_db)
):
    opp = db.query(models.Opportunity).filter(
        models.Opportunity.id == opp_id
    ).first()
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    
    opp.is_active = is_active
    db.commit()
    return {"status": "moderation updated", "opportunity_id": opp_id}

@router.post("/create-curator")
def create_curator(
    data: schemas.CuratorCreate,
    current_user: models.User = Depends(get_curator_or_403),
    db: Session = Depends(database.get_db)
):
    existing = db.query(models.User).filter(
        models.User.email == data.email
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_pw = auth.get_password_hash(data.password)
    new_curator = models.User(
        email=data.email,
        hashed_password=hashed_pw,
        role=models.UserRole.CURATOR
    )
    db.add(new_curator)
    db.commit()
    return {"status": "curator created", "email": data.email}

@router.delete("/delete-user/{user_id}")
def delete_user(
    user_id: int,
    current_user: models.User = Depends(get_curator_or_403),
    db: Session = Depends(database.get_db)
):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.role == models.UserRole.CURATOR and current_user.id != user_id:
        pass
    
    db.delete(user)
    db.commit()
    return {"status": "user deleted"}