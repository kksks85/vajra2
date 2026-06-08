from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from starlette.responses import RedirectResponse
from sqlalchemy.orm import Session

from database import get_db
from models.incident import Incident
from models.knowledge import KnowledgeArticle
from models.lowcode import TaskDefinition, Workflow
from utils import build_template_context

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/")
def dashboard(request: Request, db: Session = Depends(get_db)):
    # Redirect to login if not authenticated
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/login", status_code=302)
    
    metrics = {
        "incidents": db.query(Incident).count(),
        "knowledge": db.query(KnowledgeArticle).count(),
        "workflows": db.query(Workflow).count(),
        "tasks": db.query(TaskDefinition).count(),
    }
    context = build_template_context(request, metrics=metrics)
    return templates.TemplateResponse(request, "dashboard.html", context)
