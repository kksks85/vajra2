from fastapi import APIRouter, Depends, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
import json
from datetime import datetime

from database import get_db
from utils import build_template_context, redirect_with_flash

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# Email configuration storage (using a simple in-memory store for now)
email_config = {
    "smtp": {
        "host": "",
        "port": 587,
        "username": "",
        "password": "",
        "from_email": "",
        "use_tls": True
    },
    "pop3": {
        "host": "",
        "port": 995,
        "username": "",
        "password": "",
        "use_ssl": True
    },
    "rules": []
}


@router.get("/admin/email-config")
def email_config_page(request: Request, db: Session = Depends(get_db)):
    context = build_template_context(
        request,
        current_section="Email Configuration",
        smtp_config=email_config["smtp"],
        pop3_config=email_config["pop3"],
        rules=email_config["rules"]
    )
    return templates.TemplateResponse(request, "admin/email_config.html", context)


@router.post("/admin/email-config/smtp")
def update_smtp_config(
    request: Request,
    smtp_host: str = Form(...),
    smtp_port: int = Form(...),
    smtp_username: str = Form(...),
    smtp_password: str = Form(...),
    from_email: str = Form(...),
    use_tls: bool = Form(False),
    db: Session = Depends(get_db)
):
    global email_config
    email_config["smtp"] = {
        "host": smtp_host,
        "port": smtp_port,
        "username": smtp_username,
        "password": smtp_password,
        "from_email": from_email,
        "use_tls": use_tls
    }
    return redirect_with_flash(request, "/admin/email-config", "SMTP configuration updated successfully")


@router.post("/admin/email-config/pop3")
def update_pop3_config(
    request: Request,
    pop3_host: str = Form(...),
    pop3_port: int = Form(...),
    pop3_username: str = Form(...),
    pop3_password: str = Form(...),
    use_ssl: bool = Form(False),
    db: Session = Depends(get_db)
):
    global email_config
    email_config["pop3"] = {
        "host": pop3_host,
        "port": pop3_port,
        "username": pop3_username,
        "password": pop3_password,
        "use_ssl": use_ssl
    }
    return redirect_with_flash(request, "/admin/email-config", "POP3 configuration updated successfully")


@router.get("/admin/email-config/rule-wizard")
def rule_wizard_page(request: Request, db: Session = Depends(get_db)):
    context = build_template_context(
        request,
        current_section="Email Notification Rule Wizard"
    )
    return templates.TemplateResponse(request, "admin/email_rule_wizard.html", context)


@router.post("/admin/email-config/rule")
def create_email_rule(request: Request, db: Session = Depends(get_db)):
    return JSONResponse({"status": "success", "message": "Rule created successfully"})


@router.get("/admin/email-config/rules")
def list_rules(request: Request, db: Session = Depends(get_db)):
    context = build_template_context(
        request,
        rules=email_config["rules"]
    )
    return templates.TemplateResponse(request, "admin/email_rules_list.html", context)


@router.delete("/admin/email-config/rule/{rule_id}")
def delete_rule(rule_id: int, request: Request, db: Session = Depends(get_db)):
    global email_config
    email_config["rules"] = [r for r in email_config["rules"] if r.get("id") != rule_id]
    return JSONResponse({"status": "success", "message": "Rule deleted successfully"})
