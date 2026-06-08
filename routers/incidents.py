from fastapi import APIRouter, Depends, Form, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from database import get_db
from models.incident import Incident
from utils import build_template_context, redirect_with_flash

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/incidents")
def incidents_page(request: Request, db: Session = Depends(get_db)):
    incidents = db.query(Incident).order_by(Incident.created_at.desc()).all()
    context = build_template_context(request, incidents=incidents)
    return templates.TemplateResponse(request, "incidents.html", context)


@router.get("/incidents/new")
def incidents_new_page(request: Request):
    issue_types = _get_issue_types()
    statuses = _get_incident_statuses()
    priorities = _get_incident_priorities()
    context = build_template_context(request, issue_types=issue_types, statuses=statuses, priorities=priorities)
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
    
    context = build_template_context(
        request,
        incident=incident,
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
        db.commit()
        return redirect_with_flash(f"/incidents/{incident_id}", request, "Incident updated successfully.", "success")
    except Exception as e:
        db.rollback()
        return redirect_with_flash(f"/incidents/{incident_id}", request, f"Error updating incident: {str(e)}", "error")


def _get_issue_types():
    """Returns hierarchical issue types"""
    return [
        {
            "id": "mechanical",
            "name": "Mechanical",
            "subcategories": [
                {"id": "propulsion", "name": "Propulsion"},
                {"id": "electrical_power", "name": "Electrical / Power"},
                {"id": "avionics_electronics", "name": "Avionics / Electronics"},
                {"id": "communication", "name": "Communication"},
            ]
        },
        {
            "id": "software",
            "name": "Software",
            "subcategories": []
        },
        {
            "id": "payload_mission",
            "name": "Payload / Mission System",
            "subcategories": []
        },
        {
            "id": "performance",
            "name": "Performance",
            "subcategories": []
        },
        {
            "id": "physical_damage",
            "name": "Physical Damage",
            "subcategories": []
        },
        {
            "id": "maintenance_spare",
            "name": "Maintenance / Spare Request",
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
