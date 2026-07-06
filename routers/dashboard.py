from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from starlette.responses import RedirectResponse
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from collections import defaultdict

from database import get_db
from models.incident import Incident
from models.knowledge import KnowledgeArticle
from models.lowcode import TaskDefinition, Workflow
from models.entities import LoiteringMunition, Contract
from utils import build_template_context

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/")
def dashboard(request: Request, db: Session = Depends(get_db)):
    # Redirect to login if not authenticated
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/login", status_code=302)
    
    # Metrics - Tiles
    total_incidents = db.query(Incident).count()
    open_incidents = db.query(Incident).filter(Incident.status.in_(["new", "open", "assigned"])).count()
    
    # New metrics for Fleet Status
    work_in_progress = db.query(Incident).filter(Incident.status == "in_progress").count()
    resolved = db.query(Incident).filter(Incident.status == "closure").count()
    critical_priority = db.query(Incident).filter(Incident.priority == "critical").count()
    
    # AOG: Critical incidents in progress (not resolved)
    in_progress_statuses = ["new", "open", "assigned", "in_progress", "on_hold", "diagnosis", "investigation", "quality_check"]
    aog = db.query(Incident).filter(Incident.priority == "critical", Incident.status.in_(in_progress_statuses)).count()
    
    # Get incidents by priority with open and resolved breakdown
    all_incidents = db.query(Incident).all()
    incidents_by_priority = {}
    for incident in all_incidents:
        priority = incident.priority if incident.priority else 'Unknown'
        if priority not in incidents_by_priority:
            incidents_by_priority[priority] = {
                'total': 0,
                'open': 0,
                'resolved': 0
            }
        incidents_by_priority[priority]['total'] += 1
        
        # Count open incidents (new, open, assigned, in_progress, on_hold, diagnosis, investigation, quality_check)
        if incident.status in ["new", "open", "assigned", "in_progress", "on_hold", "diagnosis", "investigation", "quality_check"]:
            incidents_by_priority[priority]['open'] += 1
        
        # Count resolved incidents (closure, repair_completed)
        if incident.status in ["closure", "repair_completed"]:
            incidents_by_priority[priority]['resolved'] += 1
    
    # Get incidents by product category (from platform_variant column)
    all_incidents = db.query(Incident).all()
    incidents_by_category = defaultdict(int)
    for incident in all_incidents:
        category = incident.platform_variant if incident.platform_variant else 'Unknown'
        incidents_by_category[category] += 1
    
    # Get LM warranty and service data with contract validation
    today = datetime.now().date()
    month_start = today.replace(day=1)
    month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    next_month_start = (month_end + timedelta(days=1))
    next_month_end = (next_month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    quarter_end = today + timedelta(days=90)
    
    all_lm_units = db.query(LoiteringMunition).all()
    
    service_schedule_next_month = []
    service_schedule_next_quarter = []
    service_schedule_past_due = []
    
    warranty_already_expired = []
    warranty_expired_month = []
    warranty_expiring_next_month = []
    warranty_valid_active = []
    
    for lm in all_lm_units:
        warranty_valid_to_str = None
        last_service_on_str = None
        next_service_due_str = None
        service_notes = None
        customer = 'Unknown'
        contract_number = 'Unknown'
        contract_id = None
        status = 'unknown'
        status_color = '#9ca3af'
        
        if hasattr(lm, 'data') and isinstance(lm.data, dict):
            warranty_valid_to_str = lm.data.get('warranty_valid_to')
            last_service_on_str = lm.data.get('last_service_on')
            next_service_due_str = lm.data.get('next_service_due')
            service_notes = lm.data.get('service_notes')
            customer = lm.data.get('customer', 'Unknown')
            contract_number = lm.data.get('contract', 'Unknown')
            contract_id = lm.data.get('contract_id')
        
        # Validate warranty from contract if available
        contract_warranty_valid_to = None
        if contract_id:
            contract = db.query(Contract).filter(Contract.id == contract_id).first()
            if contract and hasattr(contract, 'data') and isinstance(contract.data, dict):
                main_deliverables = contract.data.get('main_deliverables', [])
                if isinstance(main_deliverables, list):
                    for deliverable in main_deliverables:
                        if isinstance(deliverable, dict) and deliverable.get('name') == 'LM':
                            contract_warranty_valid_to = deliverable.get('warranty_valid_to')
                            break
        
        # Use contract warranty if available, otherwise use LM data
        warranty_date_str = contract_warranty_valid_to or warranty_valid_to_str
        
        # Process WARRANTY information
        if warranty_date_str:
            try:
                warranty_date = datetime.strptime(warranty_date_str, "%Y-%m-%d").date()
                
                item = {
                    'id': lm.id,
                    'serial_number': lm.serial_number or lm.unit_name,
                    'customer': customer,
                    'contract': contract_number,
                    'warranty_date': warranty_date_str,
                }
                
                if warranty_date < today:
                    # Already expired (regardless of when)
                    item['status'] = 'Expired'
                    item['status_color'] = '#dc2626'  # Red
                    warranty_already_expired.append(item)
                elif month_start <= warranty_date <= month_end:
                    # Expiring this month
                    item['status'] = 'Expiring This Month'
                    item['status_color'] = '#ea580c'  # Orange-Red
                    warranty_expired_month.append(item)
                elif next_month_start <= warranty_date <= next_month_end:
                    # Expiring next month
                    item['status'] = 'Expiring Next Month'
                    item['status_color'] = '#f97316'  # Orange
                    warranty_expiring_next_month.append(item)
                elif warranty_date <= quarter_end:
                    # Expiring within next quarter
                    item['status'] = 'Due Soon'
                    item['status_color'] = '#fbbf24'  # Amber
                    warranty_valid_active.append(item)
                else:
                    # Warranty still valid
                    item['status'] = 'Active'
                    item['status_color'] = '#22c55e'  # Green
                    warranty_valid_active.append(item)
            except ValueError:
                pass
        
        # Process SERVICE SCHEDULE information
        if next_service_due_str:
            try:
                next_service_date = datetime.strptime(next_service_due_str, "%d-%m-%Y").date()
                
                service_item = {
                    'id': lm.id,
                    'serial_number': lm.serial_number or lm.unit_name,
                    'customer': customer,
                    'contract': contract_number,
                    'next_service_due': next_service_due_str,
                    'last_service_on': last_service_on_str,
                    'service_notes': service_notes,
                }
                
                if next_service_date < today:
                    # Service is overdue
                    service_item['status'] = 'Past Due'
                    service_item['status_color'] = '#dc2626'  # Red
                    service_schedule_past_due.append(service_item)
                elif month_start <= next_service_date <= month_end:
                    # Service due this month
                    service_item['status'] = 'Due This Month'
                    service_item['status_color'] = '#fbbf24'  # Amber
                    service_schedule_next_month.append(service_item)
                elif next_month_start <= next_service_date <= next_month_end:
                    # Service due next month
                    service_item['status'] = 'Due Next Month'
                    service_item['status_color'] = '#f97316'  # Orange
                    service_schedule_next_month.append(service_item)
                elif next_service_date <= quarter_end:
                    # Service due within next quarter
                    service_item['status'] = 'Due Next Quarter'
                    service_item['status_color'] = '#3b82f6'  # Blue
                    service_schedule_next_quarter.append(service_item)
            except ValueError:
                pass
    
    metrics = {
        "total_incidents": total_incidents,
        "open_incidents": open_incidents,
        "work_in_progress": work_in_progress,
        "resolved": resolved,
        "critical_priority": critical_priority,
        "aog": aog,
        "incidents_by_priority": dict(incidents_by_priority),
        "incidents_by_category": dict(incidents_by_category),
        "service_schedule_next_month": service_schedule_next_month,
        "service_schedule_next_quarter": service_schedule_next_quarter,
        "service_schedule_past_due": service_schedule_past_due,
        "warranty_already_expired": warranty_already_expired,
        "warranty_expired_month": warranty_expired_month,
        "warranty_expiring_next_month": warranty_expiring_next_month,
        "warranty_valid_active": warranty_valid_active,
    }
    context = build_template_context(request, metrics=metrics)
    return templates.TemplateResponse(request, "dashboard.html", context)
