from fastapi import APIRouter, Depends, Form, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from database import get_db
from models.incident import Incident
from models.entities import Customer, Contract
from utils import build_template_context, redirect_with_flash

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/incidents")
def incidents_page(request: Request, db: Session = Depends(get_db)):
    try:
        incidents = db.query(Incident).order_by(Incident.created_at.desc()).all()
        
        # Add generated incident numbers to incidents
        for incident in incidents:
            incident.generated_number = _generate_incident_number(incident.caller, db)
        
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
    
    context = build_template_context(
        request, 
        issue_types=issue_types, 
        statuses=statuses, 
        priorities=priorities,
        customers=customer_list,
        contracts=contract_list
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
    db: Session = Depends(get_db),
):
    try:
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
        )
        
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
    
    # Generate incident number
    generated_incident_number = _generate_incident_number(incident.caller, db)
    
    context = build_template_context(
        request,
        incident=incident,
        incident_number=generated_incident_number,
        issue_types=issue_types,
        statuses=statuses,
        priorities=priorities,
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
    db: Session = Depends(get_db),
):
    """Update incident - accepts all form fields"""
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        return redirect_with_flash("/incidents", request, "Incident not found.", "error")
    
    try:
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


def _generate_incident_number(customer_name: str, db: Session):
    """
    Generate automated incident number based on:
    1. Customer name (short code)
    2. Incident Number Format from customer
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
        
        # Find the customer and get incident_number_format from customer data
        customer = db.query(Customer).filter(Customer.name == customer_name).first()
        incident_number_format = "INCIDENT"  # default
        
        if customer and customer.data and isinstance(customer.data, dict):
            # Get incident_number_format from customer's data
            incident_number_format = customer.data.get('incident_number_format', 'INCIDENT')
        
        # Get current year
        current_year = datetime.now().year
        
        # Count incidents for this customer in the current year to get sequence
        existing_incidents = db.query(Incident).filter(Incident.caller == customer_name).all()
        
        # Filter for current year only
        current_year_count = 0
        for inc in existing_incidents:
            if inc.created_at and inc.created_at.year == current_year:
                current_year_count += 1
        
        sequence_number = current_year_count + 1
        
        # Generate incident number
        incident_number = f"TASL-{customer_code}-{incident_number_format}-{current_year}-{sequence_number:04d}"
        
        return incident_number
    
    except Exception as e:
        print(f"Error generating incident number: {str(e)}")
        return None
