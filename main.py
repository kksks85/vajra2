from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from config import settings
from database import Base, engine
from routers.auth import router as auth_router
from routers.admin import router as admin_router
from routers.incidents import router as incidents_router
from routers.knowledge import router as knowledge_router
from routers.builder import router as builder_router
from routers.dashboard import router as dashboard_router

app = FastAPI(title=settings.APP_NAME)
app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(dashboard_router)
app.include_router(auth_router)
app.include_router(incidents_router)
app.include_router(knowledge_router)
app.include_router(builder_router)
app.include_router(admin_router)


@app.on_event("startup")
def on_startup():
    print("🔄 Starting up Vajra Service Management...")
    try:
        Base.metadata.create_all(bind=engine)
        print("✓ Database schema initialized")
    except Exception as e:
        print(f"✗ Error creating tables: {e}")
    
    # Seed default users on startup
    try:
        from database import SessionLocal
        from models.admin import User
        from services.auth import hash_password
        
        db = SessionLocal()
        
        # Check if any user exists
        existing_users = db.query(User).count()
        if existing_users == 0:
            print("🔄 Seeding default users...")
            
            default_users = [
                ("admin", "admin@vajra.com", "Administrator", "admin123", "admin"),
                ("supervisor", "supervisor@vajra.com", "Sarah Supervisor", "super123", "supervisor"),
                ("technician", "technician@vajra.com", "John Technician", "tech123", "technician"),
                ("agent", "agent@vajra.com", "Alex Agent", "agent123", "agent"),
                ("demo", "demo@vajra.com", "Demo User", "demo123", "agent"),
            ]
            
            for username, email, full_name, password, role in default_users:
                try:
                    user = User(
                        username=username,
                        email=email,
                        full_name=full_name,
                        password_hash=hash_password(password),
                        role=role,
                        is_active=True,
                        department="Operations",
                        status="Active",
                    )
                    db.add(user)
                    print(f"  ✓ {username}")
                except Exception as e:
                    print(f"  ✗ {username}: {e}")
            
            db.commit()
            print("✓ User seeding completed")
        else:
            print(f"✓ Database already has {existing_users} user(s)")
        
        db.close()
    except Exception as e:
        print(f"✗ Error during user seeding: {e}")
        import traceback
        traceback.print_exc()
