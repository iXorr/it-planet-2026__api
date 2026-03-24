# routers/opportunities.py
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
import models, schemas, auth, database
from typing import List, Optional

router = APIRouter(prefix="/opportunities", tags=["Opportunities"])

@router.post("/", response_model=schemas.OpportunityResponse)
def create_opportunity(
    opportunity: schemas.OpportunityCreate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    if current_user.role != models.UserRole.EMPLOYER:
        raise HTTPException(status_code=403, detail="Only employers can create opportunities")
    
    emp_profile = db.query(models.EmployerProfile).filter(
        models.EmployerProfile.user_id == current_user.id
    ).first()
    
    if not emp_profile or not emp_profile.is_verified:
        raise HTTPException(
            status_code=403, 
            detail="Employer profile must be verified by curator first"
        )
    
    opp_data = opportunity.model_dump(exclude={'tag_names'})
    db_opportunity = models.Opportunity(owner_id=current_user.id, **opp_data)
    
    # Обработка тегов
    for tag_name in opportunity.tag_names:
        tag = db.query(models.Tag).filter(
            models.Tag.name.ilike(tag_name.strip())
        ).first()
        if not tag:
            tag = models.Tag(name=tag_name.strip(), category="tech")
            db.add(tag)
        db_opportunity.tags.append(tag)
    
    db.add(db_opportunity)
    db.commit()
    db.refresh(db_opportunity)
    
    db_opportunity.company_name = emp_profile.company_name
    return db_opportunity

@router.get("/", response_model=List[schemas.OpportunityResponse])
def get_opportunities(
    city: Optional[str] = Query(None),
    work_format: Optional[models.WorkFormat] = Query(None),
    tags: Optional[str] = Query(None),  # comma-separated: "Python,SQL,Junior"
    op_type: Optional[models.OpportunityType] = Query(None),
    min_salary: Optional[int] = Query(None),
    only_active: bool = True,
    db: Session = Depends(database.get_db)
):
    query = db.query(models.Opportunity).join(
        models.EmployerProfile,
        models.Opportunity.owner_id == models.EmployerProfile.user_id
    )
    
    if only_active:
        query = query.filter(
            models.Opportunity.is_active == True,
            models.EmployerProfile.is_verified == True
        )
    
    if city:
        query = query.filter(models.Opportunity.city.ilike(f"%{city}%"))
    if work_format:
        query = query.filter(models.Opportunity.work_format == work_format)
    if op_type:
        query = query.filter(models.Opportunity.op_type == op_type)
    if min_salary:
        query = query.filter(
            or_(
                models.Opportunity.salary_max >= min_salary,
                models.Opportunity.salary_min >= min_salary
            )
        )
    
    if tags:
        tag_list = [t.strip() for t in tags.split(",") if t.strip()]
        query = query.filter(
            models.Opportunity.tags.any(
                models.Tag.name.in_(tag_list)
            )
        )
    
    results = query.all()
    
    for opp in results:
        emp = db.query(models.EmployerProfile).filter(
            models.EmployerProfile.user_id == opp.owner_id
        ).first()
        opp.company_name = emp.company_name if emp else "Unknown"
    
    return results

@router.get("/{opp_id:int}", response_model=schemas.OpportunityResponse)
def get_opportunity(
    opp_id: int,
    db: Session = Depends(database.get_db)
):
    opp = db.query(models.Opportunity).filter(
        models.Opportunity.id == opp_id,
        models.Opportunity.is_active == True
    ).first()
    
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    
    emp = db.query(models.EmployerProfile).filter(
        models.EmployerProfile.user_id == opp.owner_id
    ).first()
    opp.company_name = emp.company_name if emp else "Unknown"
    return opp

@router.post("/{opp_id:int}/apply")
def apply_to_opportunity(
    opp_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    if current_user.role != models.UserRole.SEEKER:
        raise HTTPException(status_code=403, detail="Only seekers can apply")
    
    opp = db.query(models.Opportunity).filter(
        models.Opportunity.id == opp_id,
        models.Opportunity.is_active == True
    ).first()
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    
    existing = db.query(models.Application).filter(
        and_(
            models.Application.opportunity_id == opp_id,
            models.Application.seeker_id == current_user.id
        )
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="You already applied to this opportunity")
    
    new_application = models.Application(
        opportunity_id=opp_id,
        seeker_id=current_user.id,
        status=models.ApplicationStatus.PENDING
    )
    db.add(new_application)
    db.commit()
    
    return {"status": "applied", "application_id": new_application.id}

@router.get("/my")
def get_my_opportunities(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    if current_user.role != models.UserRole.EMPLOYER:
        raise HTTPException(status_code=403, detail="Only employers can view their opportunities")
    
    opportunities = db.query(models.Opportunity).filter(
        models.Opportunity.owner_id == current_user.id
    ).all()
    
    return opportunities

@router.get("/my/applications")
def get_my_applications(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    if current_user.role != models.UserRole.EMPLOYER:
        raise HTTPException(status_code=403, detail="Only employers can view applications")
    
    my_opps = db.query(models.Opportunity.id).filter(
        models.Opportunity.owner_id == current_user.id
    ).subquery()
    
    applications = db.query(models.Application).join(
        models.User, models.Application.seeker_id == models.User.id
    ).join(
        models.SeekerProfile,
        models.SeekerProfile.user_id == models.User.id,
        isouter=True
    ).filter(
        models.Application.opportunity_id.in_(my_opps)
    ).all()
    
    return [
        {
            "application_id": app.id,
            "opportunity_id": app.opportunity_id,
            "seeker": {
                "id": app.seeker.id,
                "email": app.seeker.email,
                "profile": app.seeker.seeker_profile
            },
            "status": app.status,
            "applied_at": app.created_at
        } for app in applications
    ]

@router.patch("/applications/{app_id}/status")
def update_application_status(
    app_id: int,
    new_status: models.ApplicationStatus,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    if current_user.role != models.UserRole.EMPLOYER:
        raise HTTPException(status_code=403, detail="Only employers can update application status")
    
    application = db.query(models.Application).join(
        models.Opportunity,
        models.Application.opportunity_id == models.Opportunity.id
    ).filter(
        models.Application.id == app_id,
        models.Opportunity.owner_id == current_user.id
    ).first()
    
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    application.status = new_status
    db.commit()
    
    return {"status": "updated", "application_id": app_id, "new_status": new_status.value}