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
        
        # Seed default knowledge documents
        from models.knowledge import KnowledgeDocument
        existing_docs = db.query(KnowledgeDocument).count()
        if existing_docs == 0:
            print("🔄 Seeding default knowledge documents...")
            import os
            os.makedirs("static/uploads", exist_ok=True)
            
            default_docs = [
                ("manual", "MAN-LM-001", "v1.0", "2024-01-15", "LM Alpha Operator Flight Manual", "Please refer to the attached document.", []),
                ("manual", "MAN-GCS-002", "v2.1", "2024-03-20", "GCS Ground Station User Manual", "Please refer to the attached document.", []),
                ("service_bulletin", "SB-PROP-102", "Rev A", "2024-02-10", "Propulsion System Lubrication Interval Bulletin", "Please refer to the attached document.", []),
                ("operator_bulletin", "OB-AV-204", "v1.1", "2024-04-05", "Avionics Calibration Procedures Operator Bulletin", "Please refer to the attached document.", []),
                ("amendments_leaflet", "AL-WH-301", "v3.0", "2024-05-18", "Warhead Payload Attachment leaf amendment leaflet", "Please refer to the attached document.", []),
                ("incoming_letter", "LET-INC-901", "N/A", "2024-05-22", "Customer Letter: Operational Acceptance approval", "Please refer to the attached document.", []),
                ("incoming_letter", "LET-INC-902", "N/A", "2024-06-01", "Customs Clearance Authorization Letter", "Please refer to the attached document.", []),
                ("outgoing_letter", "LET-OUT-801", "N/A", "2024-05-30", "Outgoing Dispatch Slip: Spare Parts shipment", "Please refer to the attached document.", [])
            ]
            
            for doc_type, file_ref, version, date_of_issue, subject, description, attachments in default_docs:
                try:
                    doc = KnowledgeDocument(
                        doc_type=doc_type,
                        file_reference_number=file_ref,
                        version=version,
                        date_of_issue=date_of_issue,
                        subject_line=subject,
                        description=description,
                        attachments=attachments,
                    )
                    db.add(doc)
                    print(f"  ✓ {file_ref}")
                except Exception as e:
                    print(f"  ✗ {file_ref}: {e}")
            db.commit()
            print("✓ Knowledge document seeding completed")
        else:
            print(f"✓ Database already has {existing_docs} knowledge document(s)")
            
        # Seed default knowledge articles
        from models.knowledge import KnowledgeArticle
        from datetime import datetime
        existing_articles = db.query(KnowledgeArticle).count()
        if existing_articles == 0:
            print("🔄 Seeding default knowledge articles...")
            default_articles = [
                ("KM001", "Vajra Knowledge Management User Guide", "Guide to creating, viewing, and managing text-based knowledge articles and uploaded service bulletins in Vajra Service Management.", ["guide", "general"]),
                ("KM002", "Avionics Troubleshooting Playbook", "Steps for debugging avionics connectivity issues on Loitering Munitions:\n1. Check battery voltages.\n2. Ensure telemetry is active.\n3. Validate GPS lock.", ["avionics", "playbook"])
            ]
            for ref, title, content, tags in default_articles:
                try:
                    art = KnowledgeArticle(
                        reference_number=ref,
                        title=title,
                        content=content,
                        tags=tags,
                        created_at=datetime.utcnow()
                    )
                    db.add(art)
                    print(f"  ✓ {ref}")
                except Exception as e:
                    print(f"  ✗ {ref}: {e}")
            db.commit()
            print("✓ Knowledge articles seeding completed")
        else:
            print(f"✓ Database already has {existing_articles} knowledge article(s)")
            
        db.close()
    except Exception as e:
        print(f"✗ Error during user seeding: {e}")
        import traceback
        traceback.print_exc()
