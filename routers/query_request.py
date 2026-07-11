from fastapi import APIRouter, Depends, Form, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from datetime import datetime
import json

from database import get_db
from models.query_request import QueryRequest
from models.entities import Customer, Contract
from utils import build_template_context, redirect_with_flash

router = APIRouter()
templates = Jinja2Templates(directory="templates")


def parse_audit_log(query_request: QueryRequest):
    """Parse existing audit log entries"""
    entries = []
    if query_request.audit_log:
        try:
            # Try to parse as JSON lines
            for line in query_request.audit_log.strip().split('\n'):
                if line.strip():
                    entries.append(json.loads(line))
        except (json.JSONDecodeError, ValueError):
            # If not JSON format, skip parsing
            pass
    return entries


def get_customer_initials(customer_name: str) -> str:
    """Extract initials from customer name"""
    if not customer_name:
        return "UNKN"
    
    customer_lower = customer_name.lower()
    if "air force" in customer_lower:
        return "IAF"
    elif "army" in customer_lower:
        return "IA"
    elif "navy" in customer_lower:
        return "IN"
    else:
        # Fallback: get first letter of each word
        words = customer_name.split()
        return ''.join(w[0].upper() for w in words if w)


def generate_query_number(customer_name: str, db: Session) -> str:
    """Generate unique query number with format QRY-{Initials}-{Sequential}"""
    initials = get_customer_initials(customer_name)
    
    # Count existing queries with this customer prefix
    count = db.query(QueryRequest).filter(
        QueryRequest.caller == customer_name
    ).count()
    
    # Generate sequential number (starting from 0001)
    seq_number = str(count + 1).zfill(4)
    
    return f"QRY-{initials}-{seq_number}"


def add_audit_log_entry(query_request: QueryRequest, changes: dict, notes: str = ""):
    """Add a single combined entry to the query request's audit log with all changes batched together
    
    Args:
        query_request: The query request object
        changes: Dict of {field_name: (old_value, new_value)} for all changed fields
        notes: Optional notes to include in this entry
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
        "note": notes
    }
    
    # Parse existing audit log
    entries = parse_audit_log(query_request)
    entries.append(entry)
    
    # Store as JSON lines (one JSON object per line)
    query_request.audit_log = '\n'.join(json.dumps(e, ensure_ascii=False) for e in entries)


@router.get("/queries")
def queries_list_page(request: Request, db: Session = Depends(get_db)):
    """Display list of all query requests"""
    try:
        queries = db.query(QueryRequest).order_by(QueryRequest.created_at.desc()).all()
        
        context = build_template_context(request, queries=queries)
        return templates.TemplateResponse(request, "queries_list.html", context)
    except Exception as e:
        print(f"Error loading queries: {str(e)}")
        context = build_template_context(request, queries=[])
        return templates.TemplateResponse(request, "queries_list.html", context)


@router.get("/queries/new")
def queries_new_page(request: Request, db: Session = Depends(get_db)):
    """Display form to create new query request"""
    query_types = ["Technical Query", "Operational Query", "Budgetry Quotation", "Contract Related", "Quality Claims", "Training", "General"]
    priorities = ["Low", "Medium", "High", "Urgent"]
    statuses = ["Open", "In Progress", "Pending", "Resolved", "Closed"]
    
    # Fetch customers from database with full data
    customers = db.query(Customer).all()
    customer_list = []
    for c in customers:
        customer_data = {
            "id": c.id, 
            "name": c.name,
            "contacts": []  # Include all contacts
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
            "customer_name": customers[0].name if customers else "Unknown"
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
        query_types=query_types,
        priorities=priorities,
        statuses=statuses,
        customers=customer_list,
        contracts=contract_list
    )
    return templates.TemplateResponse(request, "queries_new.html", context)


@router.post("/queries")
def create_query(
    request: Request,
    title: str = Form(...),
    description: str = Form(default=""),
    query_type: str = Form(...),
    priority: str = Form("Medium"),
    status: str = Form("Open"),
    subject: str = Form(default=""),
    assignment_group: str = Form(default=""),
    assigned_to: str = Form(default=""),
    caller: str = Form(default=""),
    requestor_name: str = Form(default=""),
    requestor_contact: str = Form(default=""),
    requestor_email: str = Form(default=""),
    db: Session = Depends(get_db)
):
    """Create new query request"""
    try:
        # Generate unique query number
        query_number = generate_query_number(caller, db)
        
        # Create new query request
        query = QueryRequest(
            query_number=query_number,
            title=title,
            description=description,
            query_type=query_type,
            priority=priority,
            status=status,
            subject=subject,
            assignment_group=assignment_group,
            assigned_to=assigned_to,
            caller=caller,
            requestor_name=requestor_name,
            requestor_contact=requestor_contact,
            requestor_email=requestor_email
        )
        
        # Add creation entry to audit log
        changes = {
            "status": ("", "Open"),
            "priority": ("", priority),
            "query_type": ("", query_type),
        }
        add_audit_log_entry(query, changes)
        
        db.add(query)
        db.commit()
        db.refresh(query)
        
        return redirect_with_flash(
            f"/queries/{query.id}",
            request,
            f"Query Request {query_number} created successfully"
        )
    except Exception as e:
        print(f"Error creating query: {str(e)}")
        return redirect_with_flash(
            "/queries/new",
            request,
            f"Error creating query: {str(e)}",
            category="error"
        )


@router.get("/queries/{query_id}")
def query_detail_page(query_id: int, request: Request, db: Session = Depends(get_db)):
    """Display query request details"""
    try:
        query = db.query(QueryRequest).filter(QueryRequest.id == query_id).first()
        
        if not query:
            return redirect_with_flash(
                "/queries",
                request,
                "Query request not found",
                category="error"
            )
        
        query_number = query.query_number or f"QRY{query.id:07d}"
        query_types = ["Technical Query", "Operational Query", "Budgetry Quotation", "Contract Related", "Quality Claims", "Training", "General"]
        priorities = ["Low", "Medium", "High", "Urgent"]
        statuses = ["Open", "In Progress", "Pending", "Resolved", "Closed"]
        
        # Fetch customers from database with full data
        customers = db.query(Customer).all()
        customer_list = []
        for c in customers:
            customer_data = {
                "id": c.id, 
                "name": c.name,
                "contacts": []
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
                "customer_name": customers[0].name if customers else "Unknown"
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
            query=query,
            query_number=query_number,
            query_types=query_types,
            priorities=priorities,
            statuses=statuses,
            customers=customer_list,
            contracts=contract_list
        )
        return templates.TemplateResponse(request, "query_detail.html", context)
    except Exception as e:
        print(f"Error loading query: {str(e)}")
        return redirect_with_flash(
            "/queries",
            request,
            f"Error loading query: {str(e)}",
            category="error"
        )


@router.post("/queries/{query_id}")
def update_query(
    query_id: int,
    request: Request,
    title: str = Form(...),
    description: str = Form(default=""),
    query_type: str = Form(...),
    priority: str = Form("Medium"),
    status: str = Form("Open"),
    subject: str = Form(default=""),
    assignment_group: str = Form(default=""),
    assigned_to: str = Form(default=""),
    caller: str = Form(default=""),
    requestor_name: str = Form(default=""),
    requestor_contact: str = Form(default=""),
    requestor_email: str = Form(default=""),
    notes: str = Form(default=""),
    db: Session = Depends(get_db)
):
    """Update query request"""
    try:
        query = db.query(QueryRequest).filter(QueryRequest.id == query_id).first()
        
        if not query:
            return redirect_with_flash(
                "/queries",
                request,
                "Query request not found",
                category="error"
            )
        
        # Track changes
        changes = {}
        
        if query.title != title:
            changes["title"] = (query.title, title)
            query.title = title
        
        if query.description != description:
            changes["description"] = (query.description, description)
            query.description = description
        
        if query.query_type != query_type:
            changes["query_type"] = (query.query_type, query_type)
            query.query_type = query_type
        
        if query.priority != priority:
            changes["priority"] = (query.priority, priority)
            query.priority = priority
        
        if query.status != status:
            changes["status"] = (query.status, status)
            query.status = status
        
        if query.subject != subject:
            changes["subject"] = (query.subject, subject)
            query.subject = subject
        
        if query.assignment_group != assignment_group:
            changes["assignment_group"] = (query.assignment_group, assignment_group)
            query.assignment_group = assignment_group
        
        if query.assigned_to != assigned_to:
            changes["assigned_to"] = (query.assigned_to, assigned_to)
            query.assigned_to = assigned_to
        
        if query.caller != caller:
            changes["caller"] = (query.caller, caller)
            query.caller = caller
        
        if query.requestor_name != requestor_name:
            changes["requestor_name"] = (query.requestor_name, requestor_name)
            query.requestor_name = requestor_name
        
        if query.requestor_contact != requestor_contact:
            changes["requestor_contact"] = (query.requestor_contact, requestor_contact)
            query.requestor_contact = requestor_contact
        
        if query.requestor_email != requestor_email:
            changes["requestor_email"] = (query.requestor_email, requestor_email)
            query.requestor_email = requestor_email
        
        # Add audit log entry if there are changes
        if changes or notes:
            add_audit_log_entry(query, changes, notes)
        
        db.commit()
        db.refresh(query)
        
        query_number = query.query_number or f"QRY{query.id:07d}"
        return redirect_with_flash(
            f"/queries/{query.id}",
            request,
            f"Query Request {query_number} updated successfully"
        )
    except Exception as e:
        print(f"Error updating query: {str(e)}")
        return redirect_with_flash(
            f"/queries/{query_id}",
            request,
            f"Error updating query: {str(e)}",
            category="error"
        )
