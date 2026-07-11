"""
API routes for managing Repair Executions and their statuses
"""

from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from database import get_db
from models import RepairExecution, RepairExecutionStatus
from utils import build_template_context

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/admin/repair-executions")
def list_repair_executions(request: Request, db: Session = Depends(get_db)):
    """List all repair executions with their statuses"""
    
    executions = db.query(RepairExecution).all()
    
    # Build data with statuses
    execution_data = []
    for execution in executions:
        statuses = db.query(RepairExecutionStatus).filter(
            RepairExecutionStatus.repair_execution_id == execution.id
        ).order_by(RepairExecutionStatus.order).all()
        
        execution_data.append({
            "id": execution.id,
            "name": execution.name,
            "description": execution.description,
            "status_count": len(statuses),
            "statuses": statuses,
            "created_at": execution.created_at
        })
    
    context = build_template_context(request, {
        "executions": execution_data,
        "page_title": "Repair Executions"
    })
    
    return templates.TemplateResponse("admin/repair_executions.html", context)


@router.post("/admin/repair-executions")
async def create_repair_execution(
    name: str,
    description: str = "",
    db: Session = Depends(get_db)
):
    """Create a new repair execution"""
    
    try:
        # Check if name already exists
        existing = db.query(RepairExecution).filter(
            RepairExecution.name == name
        ).first()
        
        if existing:
            return JSONResponse(
                {"error": "Repair execution with this name already exists"},
                status_code=400
            )
        
        repair_execution = RepairExecution(
            name=name,
            description=description
        )
        db.add(repair_execution)
        db.commit()
        db.refresh(repair_execution)
        
        return {
            "id": repair_execution.id,
            "name": repair_execution.name,
            "description": repair_execution.description,
            "message": "Repair execution created successfully"
        }
    except Exception as e:
        db.rollback()
        return JSONResponse(
            {"error": str(e)},
            status_code=500
        )


@router.post("/admin/repair-executions/{execution_id}/statuses")
async def add_status_to_execution(
    execution_id: int,
    status: str,
    description: str = "",
    order: int = 0,
    db: Session = Depends(get_db)
):
    """Add a status to a repair execution"""
    
    try:
        # Verify execution exists
        execution = db.query(RepairExecution).filter(
            RepairExecution.id == execution_id
        ).first()
        
        if not execution:
            raise HTTPException(status_code=404, detail="Repair execution not found")
        
        # Check if status already exists for this execution
        existing = db.query(RepairExecutionStatus).filter(
            RepairExecutionStatus.repair_execution_id == execution_id,
            RepairExecutionStatus.status == status
        ).first()
        
        if existing:
            return JSONResponse(
                {"error": f"Status '{status}' already exists for this execution"},
                status_code=400
            )
        
        # If order is 0, set it to max order + 1
        if order == 0:
            max_order = db.query(RepairExecutionStatus).filter(
                RepairExecutionStatus.repair_execution_id == execution_id
            ).count()
            order = max_order + 1
        
        exec_status = RepairExecutionStatus(
            repair_execution_id=execution_id,
            status=status,
            description=description,
            order=order
        )
        db.add(exec_status)
        db.commit()
        db.refresh(exec_status)
        
        return {
            "id": exec_status.id,
            "status": exec_status.status,
            "description": exec_status.description,
            "order": exec_status.order,
            "message": "Status added successfully"
        }
    except Exception as e:
        db.rollback()
        return JSONResponse(
            {"error": str(e)},
            status_code=500
        )


@router.get("/admin/repair-executions/{execution_id}/statuses")
def get_execution_statuses(
    execution_id: int,
    db: Session = Depends(get_db)
):
    """Get all statuses for a specific repair execution"""
    
    try:
        execution = db.query(RepairExecution).filter(
            RepairExecution.id == execution_id
        ).first()
        
        if not execution:
            raise HTTPException(status_code=404, detail="Repair execution not found")
        
        statuses = db.query(RepairExecutionStatus).filter(
            RepairExecutionStatus.repair_execution_id == execution_id
        ).order_by(RepairExecutionStatus.order).all()
        
        return {
            "id": execution.id,
            "name": execution.name,
            "description": execution.description,
            "statuses": [
                {
                    "id": s.id,
                    "status": s.status,
                    "description": s.description,
                    "order": s.order
                } for s in statuses
            ]
        }
    except Exception as e:
        return JSONResponse(
            {"error": str(e)},
            status_code=500
        )


@router.delete("/admin/repair-executions/{execution_id}")
async def delete_repair_execution(
    execution_id: int,
    db: Session = Depends(get_db)
):
    """Delete a repair execution and its statuses"""
    
    try:
        execution = db.query(RepairExecution).filter(
            RepairExecution.id == execution_id
        ).first()
        
        if not execution:
            raise HTTPException(status_code=404, detail="Repair execution not found")
        
        # Statuses will be deleted cascade
        db.delete(execution)
        db.commit()
        
        return {"message": "Repair execution deleted successfully"}
    except Exception as e:
        db.rollback()
        return JSONResponse(
            {"error": str(e)},
            status_code=500
        )


@router.delete("/admin/repair-execution-statuses/{status_id}")
async def delete_execution_status(
    status_id: int,
    db: Session = Depends(get_db)
):
    """Delete a specific status"""
    
    try:
        exec_status = db.query(RepairExecutionStatus).filter(
            RepairExecutionStatus.id == status_id
        ).first()
        
        if not exec_status:
            raise HTTPException(status_code=404, detail="Status not found")
        
        db.delete(exec_status)
        db.commit()
        
        return {"message": "Status deleted successfully"}
    except Exception as e:
        db.rollback()
        return JSONResponse(
            {"error": str(e)},
            status_code=500
        )
