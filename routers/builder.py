from fastapi import APIRouter, Depends, Form, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from database import get_db
from models.lowcode import Stage, TaskDefinition, Workflow
from utils import build_template_context, redirect_with_flash

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/builder")
def builder_page(request: Request, db: Session = Depends(get_db)):
    workflows = db.query(Workflow).order_by(Workflow.created_at.desc()).all()
    stages = db.query(Stage).order_by(Stage.order.asc()).all()
    tasks = db.query(TaskDefinition).order_by(TaskDefinition.created_at.desc()).all()
    context = build_template_context(request, workflows=workflows, stages=stages, tasks=tasks)
    return templates.TemplateResponse(request, "builder.html", context)


@router.post("/builder/workflows")
def create_workflow(
    request: Request,
    name: str = Form(...),
    description: str = Form(""),
    db: Session = Depends(get_db),
):
    workflow = Workflow(name=name, description=description)
    db.add(workflow)
    db.commit()
    return redirect_with_flash("/builder", request, "Workflow created.", "success")


@router.post("/builder/stages")
def create_stage(
    request: Request,
    workflow_id: int = Form(...),
    name: str = Form(...),
    order: int = Form(1),
    db: Session = Depends(get_db),
):
    stage = Stage(workflow_id=workflow_id, name=name, order=order)
    db.add(stage)
    db.commit()
    return redirect_with_flash("/builder", request, "Stage created.", "success")


@router.post("/builder/tasks")
def create_task(
    request: Request,
    stage_id: int = Form(...),
    name: str = Form(...),
    task_type: str = Form("manual"),
    config: str = Form("{}"),
    db: Session = Depends(get_db),
):
    task = TaskDefinition(stage_id=stage_id, name=name, task_type=task_type, config={"raw": config})
    db.add(task)
    db.commit()
    return redirect_with_flash("/builder", request, "Task created.", "success")
