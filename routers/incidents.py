from fastapi import APIRouter, Depends, Form, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from datetime import datetime
import json

from database import get_db
from models.incident import Incident
from models.entities import Customer, Contract, KittingItem
from models import RepairExecution, RepairExecutionStatus
from utils import build_template_context, redirect_with_flash

router = APIRouter()
templates = Jinja2Templates(directory="templates")


def parse_audit_log(incident: Incident):
    """Parse existing audit log entries"""
    entries = []
    if incident.audit_log:
        try:
            # Try to parse as JSON lines
            for line in incident.audit_log.strip().split('\n'):
                if line.strip():
                    entries.append(json.loads(line))
        except (json.JSONDecodeError, ValueError):
            # If not JSON format, skip parsing
            pass
    return entries


def add_audit_log_entry(incident: Incident, changes: dict, work_notes: str = ""):
    """Add a single combined entry to the incident's audit log with all changes batched together
    
    Args:
        incident: The incident object
        changes: Dict of {field_name: (old_value, new_value)} for all changed fields
        work_notes: Optional work notes to include in this entry
    """
    if not changes:
        return
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Create a single entry combining all changes
    entry = {
        "date_time": timestamp,
        "updated_by": "System",
        "changes": {
            field: {
                "previous_value": str(old_val) if old_val else "",
                "new_value": str(new_val) if new_val else ""
            }
            for field, (old_val, new_val) in changes.items()
        },
        "work_note": work_notes
    }
    
    # Parse existing audit log
    entries = parse_audit_log(incident)
    entries.append(entry)
    
    # Store as JSON lines (one JSON object per line)
    incident.audit_log = '\n'.join(json.dumps(e, ensure_ascii=False) for e in entries)


@router.get("/incidents")
def incidents_page(request: Request, db: Session = Depends(get_db)):
    try:
        incidents = db.query(Incident).order_by(Incident.created_at.desc()).all()
        
        # Add generated incident numbers to incidents
        for incident in incidents:
            incident.generated_number = _generate_incident_number(incident.caller, db, incident.id, incident.customer_contract)
        
        context = build_template_context(request, incidents=incidents)
        return templates.TemplateResponse(request, "incidents.html", context)
    except Exception as e:
        print(f"Error loading incidents: {str(e)}")
        # Fallback - return empty list if there's an error
        context = build_template_context(request, incidents=[])
        return templates.TemplateResponse(request, "incidents.html", context)


@router.get("/incidents/new")
def incidents_new_page(request: Request, db: Session = Depends(get_db)):
    issue_types = _get_issue_types()
    statuses = _get_incident_statuses()
    priorities = _get_incident_priorities()
    
    # Fetch customers from database with full data
    customers = db.query(Customer).all()
    customer_list = []
    for c in customers:
        customer_data = {
            "id": c.id, 
            "name": c.name,
            "contacts": []  # Include all contacts - no auto-population
        }
        # Extract all contacts from customer data JSON
        if c.data and isinstance(c.data, dict):
            # Get all contacts from contacts array
            contacts = c.data.get("contacts", [])
            for contact in contacts:
                customer_data["contacts"].append({
                    "name": contact.get("name", ""),
                    "phone": contact.get("phone", ""),
                    "email": contact.get("email", ""),
                    "designation": contact.get("designation", "")
                })
        customer_list.append(customer_data)
    
    # Fetch contracts from database
    contracts = db.query(Contract).all()
    contract_list = [
        {
            "id": c.id, 
            "number": c.number,
            "customer_id": c.customer_id,
            "customer_name": customers[0].name if customers else "Unknown"  # Default fallback
        } 
        for c in contracts
    ]
    
    # Build correct customer name for each contract
    for contract in contract_list:
        customer = next((cust for cust in customers if cust.id == contract["customer_id"]), None)
        if customer:
            contract["customer_name"] = customer.name
    
    # Get repair executions (grouped by repair_execution name)
    all_repairs = db.query(RepairExecution).order_by(RepairExecution.repair_execution, RepairExecution.order).all()
    repair_execution_data = {}
    
    for repair in all_repairs:
        if repair.repair_execution not in repair_execution_data:
            repair_execution_data[repair.repair_execution] = []
        repair_execution_data[repair.repair_execution].append({
            "id": repair.id,
            "status": repair.status,
            "order": repair.order
        })
    
    # Convert to list format for template
    repair_executions_list = []
    for name, statuses in repair_execution_data.items():
        repair_executions_list.append({
            "name": name,
            "statuses": statuses
        })
    
    context = build_template_context(
        request, 
        issue_types=issue_types, 
        statuses=statuses, 
        priorities=priorities,
        customers=customer_list,
        contracts=contract_list,
        repair_executions=repair_executions_list,
    )
    return templates.TemplateResponse(request, "incidents_new.html", context)


@router.post("/incidents")
def create_incident(
    request: Request,
    title: str = Form(...),
    description: str = Form(""),
    priority: str = Form("medium"),
    status: str = Form("new"),
    issue_type: str = Form(""),
    stage: str = Form("triage"),
    caller: str = Form(""),
    requestor_name: str = Form(""),
    customer_contract: str = Form(""),
    requestor_contact: str = Form(""),
    srlm_system: str = Form(""),
    platform_variant: str = Form(""),
    line_replaceable_unit: str = Form(""),
    sub_system: str = Form(""),
    assignment_group: str = Form(""),
    assigned_to: str = Form(""),
    sla: str = Form(""),
    warranty_status: str = Form(""),
    last_serviced_date: str = Form(""),
    repair_execution: str = Form(""),
    repair_status: str = Form(""),
    db: Session = Depends(get_db),
):
    try:
        print(f"DEBUG: repair_execution={repair_execution}, repair_status={repair_status}")
        
        # If repair_execution is selected but repair_status is not, set it to the first status
        if repair_execution and not repair_status:
            from models.admin import RepairExecution
            first_status = db.query(RepairExecution).filter(
                RepairExecution.repair_execution == repair_execution
            ).order_by(RepairExecution.order).first()
            
            print(f"DEBUG: first_status={first_status}")
            if first_status:
                repair_status = first_status.status
                print(f"DEBUG: Setting repair_status to {repair_status}")
        
        incident = Incident(
            title=title,
            description=description,
            priority=priority,
            status=status,
            issue_type=issue_type,
            stage=stage,
            caller=caller,
            requestor_name=requestor_name,
            customer_contract=customer_contract,
            requestor_contact=requestor_contact,
            srlm_system=srlm_system,
            platform_variant=platform_variant,
            line_replaceable_unit=line_replaceable_unit,
            sub_system=sub_system,
            assignment_group=assignment_group,
            assigned_to=assigned_to,
            sla=sla,
            warranty_status=warranty_status,
            last_serviced_date=last_serviced_date,
            repair_execution=repair_execution,
            repair_status=repair_status,
            work_notes="",
        )
        
        # Initialize audit log with JSON format
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        initial_entry = {
            "date_time": timestamp,
            "updated_by": "System",
            "field": "Status",
            "previous_value": "",
            "new_value": "Created",
            "work_note": ""
        }
        incident.audit_log = json.dumps(initial_entry, ensure_ascii=False)
        
        db.add(incident)
        db.commit()
        db.refresh(incident)
        # Redirect to the detail view with all form fields
        return redirect_with_flash(f"/incidents/{incident.id}", request, "Incident created successfully.", "success")
    except Exception as e:
        db.rollback()
        return redirect_with_flash("/incidents/new", request, f"Error creating incident: {str(e)}", "error")


@router.get("/incidents/{incident_id}")
def incident_detail(request: Request, incident_id: int, db: Session = Depends(get_db)):
    """View and edit incident detail with all form fields"""
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        return redirect_with_flash("/incidents", request, "Incident not found.", "error")
    
    issue_types = _get_issue_types()
    statuses = _get_incident_statuses()
    priorities = _get_incident_priorities()
    
    # Get repair executions (grouped by repair_execution name)
    all_repairs = db.query(RepairExecution).order_by(RepairExecution.repair_execution, RepairExecution.order).all()
    repair_execution_data = {}
    
    for repair in all_repairs:
        if repair.repair_execution not in repair_execution_data:
            repair_execution_data[repair.repair_execution] = []
        repair_execution_data[repair.repair_execution].append({
            "id": repair.id,
            "status": repair.status,
            "order": repair.order
        })
    
    # Convert to list format for template
    repair_executions_list = []
    for name, statuses in repair_execution_data.items():
        repair_executions_list.append({
            "name": name,
            "statuses": statuses
        })
    
    # Generate incident number for this specific incident
    generated_incident_number = _generate_incident_number(incident.caller, db, incident.id, incident.customer_contract)
    
    from routers.admin import LM_ROUTE_CARDS
    kitting_items = []
    if incident.line_replaceable_unit:
        kitting_items = db.query(KittingItem).filter(
            KittingItem.product_serial_no == incident.line_replaceable_unit,
            KittingItem.product_category == "LM"
        ).all()
    else:
        kitting_items = db.query(KittingItem).filter(
            KittingItem.product_category == "LM"
        ).all()
        
    context = build_template_context(
        request,
        incident=incident,
        incident_number=generated_incident_number,
        issue_types=issue_types,
        statuses=statuses,
        priorities=priorities,
        repair_executions=repair_executions_list,
        route_cards=LM_ROUTE_CARDS,
        kitting_items=kitting_items,
    )
    return templates.TemplateResponse(request, "incident_detail_form.html", context)


@router.post("/incidents/{incident_id}")
def update_incident(
    request: Request,
    incident_id: int,
    title: str = Form(...),
    description: str = Form(""),
    priority: str = Form("medium"),
    status: str = Form("new"),
    issue_type: str = Form(""),
    stage: str = Form("triage"),
    caller: str = Form(""),
    requestor_name: str = Form(""),
    customer_contract: str = Form(""),
    requestor_contact: str = Form(""),
    srlm_system: str = Form(""),
    platform_variant: str = Form(""),
    line_replaceable_unit: str = Form(""),
    sub_system: str = Form(""),
    assignment_group: str = Form(""),
    assigned_to: str = Form(""),
    sla: str = Form(""),
    warranty_status: str = Form(""),
    last_serviced_date: str = Form(""),
    repair_execution: str = Form(""),
    repair_status: str = Form(""),
    work_notes: str = Form(""),
    resolved_by: str = Form(""),
    resolved_date_time: str = Form(""),
    resolution_notes: str = Form(""),
    db: Session = Depends(get_db),
):
    """Update incident - accepts all form fields"""
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        return redirect_with_flash("/incidents", request, "Incident not found.", "error")
    
    try:
        # Check if repair_status changed from Query Registered to something else
        status_changed_beyond_query = (
            incident.repair_status == "Query Registered" and 
            repair_status and 
            repair_status != "Query Registered"
        )
        
        # Validate Work Notes if status moved beyond Query Registered
        if status_changed_beyond_query and not work_notes.strip():
            return redirect_with_flash(
                f"/incidents/{incident_id}", 
                request, 
                "Work Notes are mandatory when the incident moves beyond Query Registered status.", 
                "error"
            )
        
        # Track all field changes (excluding work_notes for now)
        fields_to_track = [
            ('title', title),
            ('description', description),
            ('priority', priority),
            ('status', status),
            ('issue_type', issue_type),
            ('stage', stage),
            ('caller', caller),
            ('requestor_name', requestor_name),
            ('customer_contract', customer_contract),
            ('requestor_contact', requestor_contact),
            ('srlm_system', srlm_system),
            ('platform_variant', platform_variant),
            ('line_replaceable_unit', line_replaceable_unit),
            ('sub_system', sub_system),
            ('assignment_group', assignment_group),
            ('assigned_to', assigned_to),
            ('sla', sla),
            ('warranty_status', warranty_status),
            ('last_serviced_date', last_serviced_date),
            ('repair_execution', repair_execution),
            ('repair_status', repair_status),
            ('resolved_by', resolved_by),
            ('resolved_date_time', resolved_date_time),
            ('resolution_notes', resolution_notes),
        ]
        
        # Collect all changes (batch them into one entry)
        batch_changes = {}
        old_work_notes = incident.work_notes or ""
        
        for field_name, new_value in fields_to_track:
            old_value = getattr(incident, field_name, "")
            if old_value != new_value:
                batch_changes[field_name] = (old_value, new_value)
        
        # Create ONE audit entry combining ALL field changes (if any)
        # Work notes are logged separately, not as a field change
        if batch_changes or (old_work_notes != work_notes):
            # Only include work_notes in audit if it actually changed
            work_notes_to_log = work_notes if old_work_notes != work_notes else ""
            add_audit_log_entry(incident, batch_changes, work_notes_to_log)
        
        # Update all fields
        incident.title = title
        incident.description = description
        incident.priority = priority
        incident.status = status
        incident.issue_type = issue_type
        incident.stage = stage
        incident.caller = caller
        incident.requestor_name = requestor_name
        incident.customer_contract = customer_contract
        incident.requestor_contact = requestor_contact
        incident.srlm_system = srlm_system
        incident.platform_variant = platform_variant
        incident.line_replaceable_unit = line_replaceable_unit
        incident.sub_system = sub_system
        incident.assignment_group = assignment_group
        incident.assigned_to = assigned_to
        incident.sla = sla
        incident.warranty_status = warranty_status
        incident.last_serviced_date = last_serviced_date
        incident.repair_execution = repair_execution
        incident.repair_status = repair_status
        incident.work_notes = work_notes
        incident.resolved_by = resolved_by
        incident.resolved_date_time = resolved_date_time
        incident.resolution_notes = resolution_notes
        
        db.commit()
        return redirect_with_flash(f"/incidents/{incident_id}", request, "Incident updated successfully.", "success")
    except Exception as e:
        db.rollback()
        return redirect_with_flash(f"/incidents/{incident_id}", request, f"Error updating incident: {str(e)}", "error")


def _get_issue_types():
    """Returns hierarchical issue types"""
    return [
        {
            "id": "electrical",
            "name": "Electrical",
            "subcategories": []
        },
        {
            "id": "mechanical",
            "name": "Mechanical",
            "subcategories": []
        },
        {
            "id": "electronics",
            "name": "Electronics",
            "subcategories": []
        },
        {
            "id": "software",
            "name": "Software",
            "subcategories": []
        },
        {
            "id": "communication",
            "name": "Communication",
            "subcategories": []
        },
        {
            "id": "sensors",
            "name": "Sensors",
            "subcategories": []
        },
        {
            "id": "camera_imaging",
            "name": "Camera & Imaging",
            "subcategories": []
        },
        {
            "id": "payload",
            "name": "Payload",
            "subcategories": []
        },
        {
            "id": "maintenance",
            "name": "Maintenance",
            "subcategories": []
        },
        {
            "id": "physical_damage",
            "name": "Physical Damage",
            "subcategories": []
        },
        {
            "id": "general_enquiry",
            "name": "General Enquiry",
            "subcategories": []
        },
        {
            "id": "other",
            "name": "Other",
            "subcategories": []
        },
    ]


def _get_incident_statuses():
    """Returns incident status values"""
    return [
        {"id": "new", "name": "New", "label": "New"},
        {"id": "diagnosis", "name": "Diagnosis", "label": "Diagnosis"},
        {"id": "in_progress", "name": "Work in Progress", "label": "Work in Progress"},
        {"id": "on_hold", "name": "On Hold", "label": "On Hold"},
        {"id": "repair_completed", "name": "Repair Completed", "label": "Repair Completed"},
        {"id": "quality_check", "name": "Quality Check", "label": "Quality Check"},
        {"id": "closure", "name": "Closure", "label": "Closure"},
    ]


def _get_incident_priorities():
    """Returns incident priority values"""
    return [
        {"id": "critical", "name": "1 - Critical (AOG)", "label": "Critical (AOG)", "level": 1},
        {"id": "high", "name": "2 - High", "label": "High", "level": 2},
        {"id": "medium", "name": "3 - Medium", "label": "Medium", "level": 3},
        {"id": "low", "name": "4 - Low", "label": "Low", "level": 4},
    ]


def _generate_incident_number(customer_name: str, db: Session, incident_id: int = None, contract_number: str = None):
    """
    Generate automated incident number based on:
    1. Customer name (short code)
    2. Incident Number Format from contract
    3. Current year (YYYY)
    4. Sequential counter (0001, 0002, etc.)
    
    Format: TASL-{CUSTOMER_CODE}-{INCIDENT_FORMAT}-{YYYY}-{SEQUENCE}
    Example: TASL-IAF-ERLM-2026-0001
    """
    from datetime import datetime
    
    if not customer_name:
        return None
    
    try:
        # Get customer short code (first 3 letters of customer name, uppercase)
        customer_code = ''.join(word[0].upper() for word in customer_name.split() if word)[:3]
        if not customer_code:
            customer_code = "UNK"
        
        # Find the contract and get incident_number_format from contract data
        incident_number_format = "INCIDENT"  # default
        
        if contract_number:
            # Look up by contract number if provided
            contract = db.query(Contract).filter(Contract.number == contract_number).first()
            if contract and contract.data and isinstance(contract.data, dict):
                incident_number_format = contract.data.get('incident_number_format', 'INCIDENT')
        else:
            # Fallback: Get the most recent contract for this customer
            customer = db.query(Customer).filter(Customer.name == customer_name).first()
            if customer:
                contract = db.query(Contract).filter(Contract.customer_id == customer.id).order_by(Contract.created_at.desc()).first()
                if contract and contract.data and isinstance(contract.data, dict):
                    incident_number_format = contract.data.get('incident_number_format', 'INCIDENT')
        
        # Get current year
        current_year = datetime.now().year
        
        # Count incidents for this customer in the current year created BEFORE this incident
        existing_incidents = db.query(Incident).filter(Incident.caller == customer_name).all()
        
        # Filter for current year only, and incidents with ID less than current (created before)
        current_year_count = 0
        for inc in existing_incidents:
            if inc.created_at and inc.created_at.year == current_year:
                # If incident_id is provided, only count incidents with lower IDs (created before)
                if incident_id is None or inc.id < incident_id:
                    current_year_count += 1
        
        sequence_number = current_year_count + 1
        
        # Generate incident number
        incident_number = f"TASL-{customer_code}-{incident_number_format}-{current_year}-{sequence_number:04d}"
        
        return incident_number
    
    except Exception as e:
        print(f"Error generating incident number: {str(e)}")
        return None
