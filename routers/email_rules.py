from fastapi import APIRouter, Depends, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from database import get_db
from utils import build_template_context

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/admin/email-rules")
def email_rules_page(request: Request, db: Session = Depends(get_db), rule_type: str = "inbound"):
    """Display email rules management page with Inbound and Outbound tabs"""
    
    # Mock data for demonstration
    inbound_rules = [
        {
            "id": 1,
            "name": "Auto-response for New Incidents",
            "trigger": "Incident Created",
            "conditions": "Priority = Critical",
            "recipients": "support-team@company.com",
            "status": "Active"
        },
        {
            "id": 2,
            "name": "Escalation Alert",
            "trigger": "Incident Updated",
            "conditions": "Status Changed to On Hold",
            "recipients": "manager@company.com",
            "status": "Active"
        }
    ]
    
    outbound_rules = [
        {
            "id": 1,
            "name": "Customer Notification",
            "trigger": "Incident Resolved",
            "conditions": "Priority = Medium",
            "recipients": "customer@example.com",
            "status": "Active"
        }
    ]
    
    context = build_template_context(
        request,
        rule_type=rule_type,
        inbound_rules=inbound_rules,
        outbound_rules=outbound_rules
    )
    return templates.TemplateResponse(request, "email_rules.html", context)


@router.get("/admin/email-rules/wizard")
def email_rules_wizard_page(request: Request, db: Session = Depends(get_db), rule_type: str = "inbound"):
    """Display email rule creation wizard"""
    
    context = build_template_context(request, rule_type=rule_type)
    return templates.TemplateResponse(request, "email_rules_wizard.html", context)


@router.post("/admin/email-rules/save")
def save_email_rule(
    request: Request,
    db: Session = Depends(get_db),
    rule_name: str = Form(...),
    rule_type: str = Form(...),
    trigger_event: str = Form(...),
    conditions: str = Form(...),
    recipients: str = Form(...),
    email_subject: str = Form(...),
    email_body: str = Form(...)
):
    """Save new email rule"""
    # In a real implementation, save to database
    return RedirectResponse(url=f"/admin/email-rules?rule_type={rule_type}", status_code=302)
