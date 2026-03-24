from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base, SessionLocal
import models
import auth
from config import settings
from routers import auth as auth_router, users, opportunities, admin

Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    db = SessionLocal()
    try:
        admin_email = "admin@trampoline.ru"
        existing_admin = db.query(models.User).filter(
            models.User.email == admin_email
        ).first()
        
        if not existing_admin:
            hashed_pw = auth.get_password_hash("admin123")
            admin_user = models.User(
                email=admin_email,
                hashed_password=hashed_pw,
                role=models.UserRole.CURATOR,
                is_active=True
            )
            db.add(admin_user)
            db.commit()
            print(f"Default admin created: {admin_email} / admin123")
    except Exception as e:
        print(f"Admin initialization error: {e}")
        db.rollback()
    finally:
        db.close()
    
    yield 
    
    print("Application shutting down...")



app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Platform for students, graduates, employers and career centers",
    version="1.0.0",
    lifespan=lifespan 
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth_router.router)
app.include_router(users.router)
app.include_router(opportunities.router)
app.include_router(admin.router)


@app.get("/", tags=["Root"])
def read_root():
    return {
        "message": "Welcome to Trampoline API",
        "docs": "/docs",
        "health": "ok"
    }


@app.get("/health", tags=["System"])
def health_check():
    return {"status": "healthy"}