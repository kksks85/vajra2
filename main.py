import sys
# Set output encoding to UTF-8 to prevent console issues on Windows
if sys.platform.startswith('win'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

# Apply compatibility monkey-patch for Starlette/FastAPI Jinja2Templates.TemplateResponse
import inspect
from fastapi.templating import Jinja2Templates

original_template_response = Jinja2Templates.TemplateResponse
sig = inspect.signature(original_template_response)
params = list(sig.parameters.keys())
expects_request_first = len(params) > 1 and params[1] == 'request'

def patched_template_response(self, *args, **kwargs):
    request_val = None
    name_val = None
    context_val = None
    
    if len(args) == 3:
        request_val, name_val, context_val = args
    elif len(args) == 2:
        if isinstance(args[0], str):
            name_val, context_val = args
        else:
            request_val, name_val = args
            context_val = kwargs.pop('context', None)
    elif len(args) == 1:
        if isinstance(args[0], str):
            name_val = args[0]
        else:
            request_val = args[0]
            name_val = kwargs.pop('name', None)
            context_val = kwargs.pop('context', None)
            
    request_val = kwargs.pop('request', request_val)
    name_val = kwargs.pop('name', name_val)
    context_val = kwargs.pop('context', context_val)
    
    if context_val is None:
        context_val = {}
    elif not isinstance(context_val, dict):
        try:
            context_val = dict(context_val)
        except Exception:
            context_val = {}
            
    if 'request' not in context_val and request_val is not None:
        context_val['request'] = request_val

    if expects_request_first:
        return original_template_response(self, request_val, name_val, context_val, **kwargs)
    else:
        return original_template_response(self, name_val, context_val, **kwargs)

Jinja2Templates.TemplateResponse = patched_template_response


from config import settings
from database import Base, engine
import models.entities  # Ensure all entity models are loaded into metadata
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
    print("[STARTUP] Starting up Vajra Service Management...")
    try:
        Base.metadata.create_all(bind=engine)
        print("[OK] Database schema initialized")
    except Exception as e:
        print(f"[ERROR] Error creating tables: {e}")
    
    # Seed default users on startup
    try:
        from database import SessionLocal
        from models.admin import User
        from services.auth import hash_password
        
        db = SessionLocal()
        
        # Check if any user exists
        existing_users = db.query(User).count()
        if existing_users == 0:
            print("[SEED] Seeding default users...")
            
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
                    print(f"  [OK] {username}")
                except Exception as e:
                    print(f"  [ERROR] {username}: {e}")
            
            db.commit()
            print("[OK] User seeding completed")
        else:
            print(f"[OK] Database already has {existing_users} user(s)")
        
        # Seed managers if they do not exist
        manager1 = db.query(User).filter(User.username == "manager1").first()
        if not manager1:
            print("[SEED] Seeding manager1...")
            manager1 = User(
                username="manager1",
                email="manager1@vajra.com",
                full_name="Manager One",
                password_hash=hash_password("manager123"),
                role="supervisor",
                is_active=True,
                department="Operations",
                status="Active",
            )
            db.add(manager1)
            db.commit()
            db.refresh(manager1)
            
        manager2 = db.query(User).filter(User.username == "manager2").first()
        if not manager2:
            print("[SEED] Seeding manager2...")
            manager2 = User(
                username="manager2",
                email="manager2@vajra.com",
                full_name="Manager Two",
                password_hash=hash_password("manager234"),
                role="supervisor",
                is_active=True,
                department="Operations",
                status="Active",
            )
            db.add(manager2)
            db.commit()
            db.refresh(manager2)
            
        # Seed Groups
        from models.admin import Group
        
        # Remove legacy group knowledge_approval if it exists
        legacy_group = db.query(Group).filter(Group.name == "knowledge_approval").first()
        if legacy_group:
            print("[SEED] Removing legacy group knowledge_approval...")
            db.delete(legacy_group)
            db.commit()

        # Seed Group knowledge_management_approver
        km_group = db.query(Group).filter(Group.name == "knowledge_management_approver").first()
        if not km_group:
            print("[SEED] Creating group knowledge_management_approver...")
            km_group = Group(
                name="knowledge_management_approver",
                description="Knowledge Management Approver Group",
                user_ids=[manager1.id, manager2.id],
                member_count=2,
            )
            db.add(km_group)
            db.commit()
        else:
            # Ensure managers are in user_ids
            updated = False
            user_ids = list(km_group.user_ids) if km_group.user_ids else []
            for m in [manager1, manager2]:
                if m.id not in user_ids:
                    user_ids.append(m.id)
                    updated = True
            if updated:
                km_group.user_ids = user_ids
                km_group.member_count = len(user_ids)
                db.commit()

        # Update empty statuses to published for existing articles and documents
        from sqlalchemy import text
        db.execute(text("UPDATE knowledge_articles SET status = 'published' WHERE status = '' OR status IS NULL"))
        db.execute(text("UPDATE knowledge_documents SET status = 'published' WHERE status = '' OR status IS NULL"))
        db.commit()
        
        # Seed default knowledge documents
        from models.knowledge import KnowledgeDocument
        existing_docs = db.query(KnowledgeDocument).count()

        if existing_docs == 0:
            print("[SEED] Seeding default knowledge documents...")
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
                    print(f"  [OK] {file_ref}")
                except Exception as e:
                    print(f"  [ERROR] {file_ref}: {e}")
            db.commit()
            print("[OK] Knowledge document seeding completed")
        else:
            print(f"[OK] Database already has {existing_docs} knowledge document(s)")
            
        # Seed default knowledge articles
        from models.knowledge import KnowledgeArticle
        from datetime import datetime
        existing_articles = db.query(KnowledgeArticle).count()
        if existing_articles == 0:
            print("[SEED] Seeding default knowledge articles...")
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
                    print(f"  [OK] {ref}")
                except Exception as e:
                    print(f"  [ERROR] {ref}: {e}")
            db.commit()
            print("[OK] Knowledge articles seeding completed")
        else:
            print(f"[OK] Database already has {existing_articles} knowledge article(s)")
            
        db.close()
    except Exception as e:
        print(f"[ERROR] Error during user seeding: {e}")
        import traceback
        traceback.print_exc()
