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
            
        # Seed default Kitting items
        from models.entities import KittingItem
        existing_kitting = db.query(KittingItem).count()
        if existing_kitting == 0:
            print("[SEED] Seeding default kitting items...")
            default_kitting = [
                # LM-0001 route cards
                ("LM-0001", "LM", "LH Side Wing Integration Assembly", "12345678", "12345678901234", "Propeller", "B-001", "S-201", "150g", "2", "EA", "Check balance", "Propulsion"),
                ("LM-0001", "LM", "LH Side Wing Integration Assembly", "87654321", "43210987654321", "Carbon Wing Skin", "B-002", "S-202", "500g", "1", "EA", "Fragile", "Airframe"),
                ("LM-0001", "LM", "RH Side Wing Integration Assembly", "12345679", "12345678901235", "Propeller Motor", "B-003", "S-203", "350g", "1", "EA", "Calibrated", "Propulsion"),
                ("LM-0001", "LM", "LH Empennage Integration Assembly", "11223344", "10101010101010", "Tail Fin Carbon Fiber", "B-004", "S-204", "800g", "1", "EA", "Verify alignment", "Airframe"),
                ("LM-0001", "LM", "RH Empennage Integration Assembly", "55667788", "20202020202020", "Elevator Servo Motor", "B-005", "S-205", "80g", "1", "EA", "Testing OK", "Flight Control"),
                ("LM-0001", "LM", "VTOL Boom Bracket Integration Assembly LH", "99001122", "30303030303030", "VTOL Boom Carbon tube", "B-006", "S-206", "1200g", "1", "EA", "Structural", "Airframe"),
                ("LM-0001", "LM", "VTOL Boom Bracket Integration Assembly RH", "33445566", "40404040404040", "Boom Bracket Titanium", "B-007", "S-207", "450g", "2", "EA", "Heavy duty", "Airframe"),
                ("LM-0001", "LM", "Centre Wing Integration Assembly", "77889900", "50505050505050", "Central Spar Carbon", "B-008", "S-208", "2500g", "1", "EA", "Main structural element", "Airframe"),
                ("LM-0001", "LM", "Fuselage Integration Assembly", "88990011", "60606060606060", "Autopilot Flight Computer", "B-009", "S-209", "320g", "1", "EA", "Firmware v1.0.4 preloaded", "Avionics"),
                ("LM-0001", "LM", "Aircraft ERLM Assembly", "99001133", "70707070707070", "Main Payload Camera", "B-010", "S-210", "950g", "1", "EA", "Gimbal assembly included", "Payload"),
                
                # GCS-0101 route cards
                ("GCS-0101", "GCS", "GCS Shelter Integration Assembly", "22334455", "80808080808080", "Getac Rugged Laptop", "B-G01", "S-G01", "3200g", "1", "EA", "OS pre-installed", "Computing"),
                ("GCS-0101", "GCS", "GCS Shelter Integration Assembly", "44556677", "90909090909090", "Display Panel 24 inch", "B-G02", "S-G02", "4500g", "2", "EA", "High brightness", "Display"),
                ("GCS-0101", "GCS", "GCS Ground Antenna Integration Assembly", "66778899", "11111111111111", "Omni Antenna Mast", "B-G03", "S-G03", "8500g", "1", "EA", "Deployable", "Communication"),
                ("GCS-0101", "GCS", "GCS Ground Antenna Integration Assembly", "88990022", "22222222222222", "RF Cable Assembly 10m", "B-G04", "S-G04", "1200g", "2", "EA", "Low loss", "Communication")
            ]
            for psn, pcat, rcd, pn, spn, md, bn, msn, wg, rq, uom, rem, subs in default_kitting:
                try:
                    item = KittingItem(
                        product_serial_no=psn,
                        product_category=pcat,
                        route_card_description=rcd,
                        part_number=pn,
                        sap_part_number=spn,
                        material_description=md,
                        batch_no_po_no=bn,
                        material_serial_no=msn,
                        weight_in_grams=wg,
                        required_quantity=rq,
                        uom=uom,
                        remarks=rem,
                        subsystems=subs
                    )
                    db.add(item)
                except Exception as e:
                    print(f"  [ERROR] Seeding kitting: {e}")
            db.commit()
            print("[OK] Kitting item seeding completed")
        else:
            print(f"[OK] Database already has {existing_kitting} kitting item(s)")

        # Seed default Customers
        from models.entities import Customer
        existing_customers = db.query(Customer).count()
        if existing_customers == 0:
            print("[SEED] Seeding default customers...")
            default_customers = [
                (1, "Acme Rail Systems", "Plot 12, Industrial Estate, Pune", "Ravi Kumar", "ravi.kumar@acme.example", "+91 98765 43210", "Active"),
                (2, "MetroLine Services", "47 Transit Park, Mumbai", "Neha Singh", "neha.singh@metroline.example", "+91 91234 56789", "Active"),
                (3, "Urban Transit Corp", "88 City Loop Rd, Delhi", "Arjun Mehta", "arjun.mehta@urban.example", "+91 99887 66554", "Expended")
            ]
            for cid, name, addr, cname, cemail, cphone, status in default_customers:
                cust = Customer(
                    id=cid,
                    name=name,
                    data={
                        "customer_name": name,
                        "primary_address": addr,
                        "contact_name": cname,
                        "contact_email": cemail,
                        "contact_phone": cphone,
                        "status": status
                    }
                )
                db.add(cust)
            db.commit()
            print("[OK] Customer seeding completed")
        else:
            print(f"[OK] Database already has {existing_customers} customer(s)")

        # Seed default Contracts
        from models.entities import Contract
        existing_contracts = db.query(Contract).count()
        if existing_contracts == 0:
            print("[SEED] Seeding default contracts...")
            default_contracts = [
                (101, "CTR-2024-001", 1, "2024-01-15", "2026-12-15", "Active"),
                (102, "CTR-2024-014", 2, "2024-03-02", "2025-03-01", "Expired"),
                (103, "CTR-2023-220", 3, "2023-07-10", "2024-07-09", "Expired")
            ]
            for con_id, number, cust_id, executed_on, valid_till, status in default_contracts:
                con = Contract(
                    id=con_id,
                    number=number,
                    customer_id=cust_id,
                    data={
                        "id": con_id,
                        "contract_number": number,
                        "customer_id": cust_id,
                        "executed_on": executed_on,
                        "valid_till": valid_till,
                        "status": status,
                        "main_deliverables": "LM: 10, GCS: 2, TMV: 4, Simulator: 1, LRU: 15",
                        "main_warranty": True,
                        "main_manuals": "User Manual v1.2 (2024-01-15), Maintenance Manual v1.0 (2024-01-20)",
                        "sub_scheduled_maintenance": True,
                        "sub_unscheduled_maintenance": True,
                        "sub_calibration": True,
                        "sub_software_upgrade": True,
                        "sub_visits_record": "Monthly status reports and support",
                        "sub_refresher_training": True
                    }
                )
                db.add(con)
            db.commit()
            print("[OK] Contract seeding completed")
        else:
            print(f"[OK] Database already has {existing_contracts} contract(s)")

        # Seed default LoiteringMunition units
        from models.entities import LoiteringMunition
        existing_lms = db.query(LoiteringMunition).count()
        if existing_lms == 0:
            print("[SEED] Seeding default loitering munitions...")
            # Acme Rail CTR-2024-001 units: LM-0001 to LM-0010 (LM-0002 excluded)
            for i in range(1, 11):
                if i == 2:
                    continue  # delete/exclude LM002 record
                sn = f"LM-{i:04d}"
                unit = LoiteringMunition(
                    serial_number=sn,
                    unit_name=f"LM Unit {i:02d}",
                    data={
                        "serial_number": sn,
                        "unit_name": f"LM Unit {i:02d}",
                        "customer_id": 1,
                        "customer_name": "Acme Rail Systems",
                        "contract_id": 101,
                        "contract_number": "CTR-2024-001",
                        "warranty_valid_from": "2024-01-15",
                        "warranty_valid_to": "2026-12-15",
                        "sap_part_number": f"1000000000{1000+i:03d}",
                        "customer_part_number": f"8000100{i}",
                        "customer_part_no": f"8000100{i}",
                        "make": "VajraCorp",
                        "model": "VC-LM-V1",
                        "software_version": "1.0.4",
                        "status": "Active",
                        "last_service_on": "2024-06-15",
                        "next_service_due": "2024-12-15",
                        "service_notes": "Initial service completed successfully."
                    }
                )
                db.add(unit)

            # MetroLine CTR-2024-014 units: LM-0011 to LM-0020
            for i in range(11, 21):
                sn = f"LM-{i:04d}"
                unit = LoiteringMunition(
                    serial_number=sn,
                    unit_name=f"LM Unit {i:02d}",
                    data={
                        "serial_number": sn,
                        "unit_name": f"LM Unit {i:02d}",
                        "customer_id": 2,
                        "customer_name": "MetroLine Services",
                        "contract_id": 102,
                        "contract_number": "CTR-2024-014",
                        "warranty_valid_from": "2024-03-02",
                        "warranty_valid_to": "2025-03-01",  # Expired
                        "sap_part_number": f"1000000000{1000+i:03d}",
                        "customer_part_number": f"8000100{i}",
                        "customer_part_no": f"8000100{i}",
                        "make": "VajraCorp",
                        "model": "VC-LM-V2",
                        "software_version": "1.0.4",
                        "status": "Active",
                        "last_service_on": "2024-08-20",
                        "next_service_due": "2025-02-20",
                        "service_notes": "Warranty expired but unit is fully functional."
                    }
                )
                db.add(unit)

            db.commit()
            print("[OK] Loitering Munitions seeding completed")
        else:
            print(f"[OK] Database already has {existing_lms} loitering munition(s)")

        # Seed default GroundControlSystem units
        from models.entities import GroundControlSystem
        existing_gcs = db.query(GroundControlSystem).count()
        if existing_gcs == 0:
            print("[SEED] Seeding default ground control systems...")
            unit = GroundControlSystem(
                serial_number="GCS-0101",
                unit_name="GCS Ground Station",
                data={
                    "serial_number": "GCS-0101",
                    "unit_name": "GCS Ground Station",
                    "customer_id": 1,
                    "customer_name": "Acme Rail Systems",
                    "contract_id": 101,
                    "contract_number": "CTR-2024-001",
                    "warranty_valid_from": "2024-01-15",
                    "warranty_valid_to": "2026-01-14",
                    "sap_part_number": "20000000002001",
                    "customer_part_number": "90002001",
                    "customer_part_no": "90002001",
                    "make": "VajraCorp",
                    "model": "VC-GCS-V1",
                    "software_version": "2.1.0",
                    "status": "Active"
                }
            )
            db.add(unit)
            db.commit()
            print("[OK] Ground Control Systems seeding completed")
        else:
            print(f"[OK] Database already has {existing_gcs} ground control system(s)")

        # Seed default Incidents
        from models.incident import Incident
        existing_incidents = db.query(Incident).count()
        if existing_incidents == 0:
            print("[SEED] Seeding default incidents...")
            default_incidents = [
                ("GPS signal lost during takeoff", "The aircraft lost GPS signal momentarily after liftoff, triggering fail-safe return to land. GPS receiver connector reseated.", "resolved", "high", "Hardware", "resolved"),
                ("Telemetry packet drop rate high", "High packet drops observed at ranges beyond 2km. Investigating antenna alignment on GCS Ground Antenna.", "assigned", "medium", "Software", "work_in_progress"),
                ("Battery cell voltage mismatch warning", "Telemetry reported cell voltage difference > 100mV on Battery Pack B-001 during flight check. Battery quarantined for deep cycle testing.", "new", "low", "Hardware", "triage")
            ]
            for title, desc, status, priority, issue_type, stage in default_incidents:
                try:
                    inc = Incident(
                        title=title,
                        description=desc,
                        status=status,
                        priority=priority,
                        issue_type=issue_type,
                        stage=stage
                    )
                    db.add(inc)
                except Exception as e:
                    print(f"  [ERROR] Seeding incident: {e}")
            db.commit()
            print("[OK] Incident seeding completed")
        else:
            print(f"[OK] Database already has {existing_incidents} incident(s)")

        db.close()
    except Exception as e:
        print(f"[ERROR] Error during user seeding: {e}")
        import traceback
        traceback.print_exc()
