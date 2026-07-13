from fastapi import APIRouter, Depends, Form, Request, File, UploadFile
from fastapi.templating import Jinja2Templates
from pathlib import Path
import re
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

from database import get_db, engine
from models.admin import Role, User, License, Group, RepairExecution, RepairExecutionStatus, Report
from models.entities import (
    Battery,
    BatteryType,
    Contract,
    Customer,
    GroundControlSystem,
    LineReplaceableUnit,
    LoiteringMunition,
    MRLS,
    RapidDeploymentVehicle,
    SAM,
    SMTSTE,
    SimulatorUnit,
    SubSystem,
    TacticalMobilityVehicle,
    Warhead,
    KittingItem,
)
from services.auth import create_user
from utils import build_template_context, redirect_with_flash, paginate

router = APIRouter()
templates = Jinja2Templates(directory="templates")

BATTERY_TYPES = [
    "Lithium-Ion 12S 44.4V",
    "Li-Polymer 6S 22.2V",
    "Li-Fe 4S 12.8V"
]


def parse_form_data(form_data):
    data = {}
    for key, value in form_data.multi_items():
        if hasattr(value, "filename"):
            value = value.filename

        if key.endswith("[]"):
            key = key[:-2]
            data.setdefault(key, []).append(value)
        elif key in data:
            if isinstance(data[key], list):
                data[key].append(value)
            else:
                data[key] = [data[key], value]
        else:
            data[key] = value
    return data


def parse_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def normalize_list(value):
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return value
    return [value]


def model_data(obj, top_level_fields=None):
    result = {}
    if top_level_fields:
        for field in top_level_fields:
            value = getattr(obj, field, None)
            if value is not None:
                result[field] = value
    if getattr(obj, "data", None):
        result.update(obj.data)
    return result


def entity_to_dict(obj, db: Session | None = None, top_level_fields=None):
    result = {"id": obj.id}
    result.update(model_data(obj, top_level_fields=top_level_fields))

    if db is not None:
        customer_id = parse_int(result.get("customer_id"))
        if customer_id:
            customer = db.query(Customer).filter(Customer.id == customer_id).first()
            if customer:
                result.setdefault("customer_name", customer.name)

        contract_id = parse_int(result.get("contract_id"))
        if contract_id:
            contract = db.query(Contract).filter(Contract.id == contract_id).first()
            if contract:
                result.setdefault("contract_number", contract.number)

    # Compatibilities and dynamic mappings for list sub-tables
    # 1. LRU Name/Serial/UnitName mappings
    if "lru_serial_number" in result and "serial_number" not in result:
        result["serial_number"] = result["lru_serial_number"]
    if "lru_name" in result and "name" not in result:
        result["name"] = result["lru_name"]
    if "serial_number" in result and "lru_serial_number" not in result:
        result["lru_serial_number"] = result["serial_number"]
    if "name" in result and "lru_name" not in result:
        result["lru_name"] = result["name"]
    if "unit_name" in result and "name" not in result:
        result["name"] = result["unit_name"]
    if "name" in result and "unit_name" not in result:
        result["unit_name"] = result["name"]

    # 2. LM Components
    if "lm_component" in result:
        components = normalize_list(result.get("lm_component"))
        part_nos = normalize_list(result.get("lm_part_no"))
        qtys = normalize_list(result.get("lm_qty"))
        serial_nos = normalize_list(result.get("lm_serial_no"))
        comps = []
        for i in range(max(len(components), len(part_nos), len(qtys), len(serial_nos))):
            comp = components[i] if i < len(components) else ""
            pn = part_nos[i] if i < len(part_nos) else ""
            qty = qtys[i] if i < len(qtys) else 1
            sn = serial_nos[i] if i < len(serial_nos) else ""
            try:
                qty = int(qty)
            except (TypeError, ValueError):
                qty = 1
            comps.append({"component_lru": comp, "part_no": pn, "qty": qty, "serial_no": sn})
        result["components"] = comps

    # 3. GCS Components
    if "gcs_component" in result:
        components = normalize_list(result.get("gcs_component"))
        part_nos = normalize_list(result.get("gcs_part_no"))
        qtys = normalize_list(result.get("gcs_qty"))
        comps = []
        for i in range(max(len(components), len(part_nos), len(qtys))):
            comp = components[i] if i < len(components) else ""
            pn = part_nos[i] if i < len(part_nos) else ""
            qty = qtys[i] if i < len(qtys) else 1
            try:
                qty = int(qty)
            except (TypeError, ValueError):
                qty = 1
            comps.append({"component_lru": comp, "part_no": pn, "qty": qty})
        result["components"] = comps

    # 4. Simulator Components
    if "sim_component" in result:
        components = normalize_list(result.get("sim_component"))
        part_nos = normalize_list(result.get("sim_part_no"))
        qtys = normalize_list(result.get("sim_qty"))
        comps = []
        for i in range(max(len(components), len(part_nos), len(qtys))):
            comp = components[i] if i < len(components) else ""
            pn = part_nos[i] if i < len(part_nos) else ""
            qty = qtys[i] if i < len(qtys) else 1
            try:
                qty = int(qty)
            except (TypeError, ValueError):
                qty = 1
            comps.append({"component_lru": comp, "part_no": pn, "qty": qty})
        result["components"] = comps

    # 5. LRU Components
    if "lru_component" in result:
        components = normalize_list(result.get("lru_component"))
        part_nos = normalize_list(result.get("lru_part_no"))
        qtys = normalize_list(result.get("lru_qty"))
        serial_nos = normalize_list(result.get("lru_serial_no"))
        comps = []
        for i in range(max(len(components), len(part_nos), len(qtys), len(serial_nos))):
            comp = components[i] if i < len(components) else ""
            pn = part_nos[i] if i < len(part_nos) else ""
            qty = qtys[i] if i < len(qtys) else 1
            sn = serial_nos[i] if i < len(serial_nos) else ""
            try:
                qty = int(qty)
            except (TypeError, ValueError):
                qty = 1
            comps.append({"component_lru": comp, "part_no": pn, "qty": qty, "serial_no": sn})
        result["components"] = comps

    # 6. SMT_STE Tools compatibility
    if "tool_component" in result:
        components = normalize_list(result.get("tool_component"))
        part_nos = normalize_list(result.get("tool_part_no"))
        qtys = normalize_list(result.get("tool_qty"))
        tools = []
        for i in range(max(len(components), len(part_nos), len(qtys))):
            comp = components[i] if i < len(components) else ""
            pn = part_nos[i] if i < len(part_nos) else ""
            qty = qtys[i] if i < len(qtys) else 1
            try:
                qty = int(qty)
            except (TypeError, ValueError):
                qty = 1
            tools.append({"component_lru": comp, "part_no": pn, "qty": qty})
        result["tools"] = tools

    # 7. MRLS Spares compatibility
    if "spare_nomenclature" in result:
        noms = normalize_list(result.get("spare_nomenclature"))
        part_nos = normalize_list(result.get("spare_part_no"))
        qtys_inst = normalize_list(result.get("spare_qty_installed"))
        qtys_prov = normalize_list(result.get("spare_qty_provided"))
        spares = []
        for i in range(max(len(noms), len(part_nos), len(qtys_inst), len(qtys_prov))):
            nom = noms[i] if i < len(noms) else ""
            pn = part_nos[i] if i < len(part_nos) else ""
            qi = qtys_inst[i] if i < len(qtys_inst) else 1
            qp = qtys_prov[i] if i < len(qtys_prov) else 1
            try:
                qi = int(qi)
            except (TypeError, ValueError):
                qi = 1
            try:
                qp = int(qp)
            except (TypeError, ValueError):
                qp = 1
            spares.append({"nomenclature": nom, "part_no": pn, "qty_installed": qi, "qty_provided": qp})
        result["spares"] = spares

    return result


def list_entities(db: Session, model, top_level_fields=None):
    items = db.query(model).order_by(model.id).all()
    return [entity_to_dict(obj, db=db, top_level_fields=top_level_fields) for obj in items]


def load_entity(db: Session, model, unit_type: str, unit_id: int, top_level_fields=None):
    entity = db.query(model).filter(model.id == unit_id).first()
    if entity:
        return entity_to_dict(entity, db=db, top_level_fields=top_level_fields)
    return None


def persist_entity(db: Session, model, data: dict, top_level_fields=None):
    kwargs = {}
    if top_level_fields:
        for field in top_level_fields:
            if field in data:
                value = data.get(field)
                if field.endswith("_id"):
                    kwargs[field] = parse_int(value)
                else:
                    kwargs[field] = value

    entity = model(**kwargs, data=data)
    db.add(entity)
    db.commit()
    db.refresh(entity)
    return entity


def list_or_sample(db: Session, model, unit_type: str, top_level_fields=None):
    items = db.query(model).order_by(model.id).all()
    if items:
        return [entity_to_dict(obj, db=db, top_level_fields=top_level_fields) for obj in items]
    return []


@router.get("/admin")
def admin_page(request: Request, db: Session = Depends(get_db)):
    roles = db.query(Role).all()
    licenses = db.query(License).all()
    groups = db.query(Group).all()
    users = db.query(User).all()
    context = build_template_context(request, roles=roles, licenses=licenses, groups=groups, users=users)
    return templates.TemplateResponse(request, "admin.html", context)


@router.get("/admin/users")
def users_list_page(request: Request, db: Session = Depends(get_db)):
    page = int(request.query_params.get("page", 1))
    db_users = db.query(User).order_by(User.id).all()
    all_users = [
        {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "license_type": user.license_type,
            "department": user.department,
            "location": user.location,
            "employee_id": user.employee_id,
            "specialization": user.specialization,
            "phone": user.phone,
            "status": user.status,
        }
        for user in db_users
    ]
    pagination = paginate(all_users, page=page, per_page=50)
    context = build_template_context(request, users=pagination["items"], pagination=pagination)
    return templates.TemplateResponse(request, "users_list.html", context)


@router.get("/admin/users/new")
def users_new_page(request: Request):
    roles = _get_sample_roles()
    licenses = _get_sample_licenses()
    departments = [
        "Administration",
        "Project Management",
        "Operations",
        "Quality Assurance",
        "Field Operations",
        "Customer Support",
        "Technical Consulting",
        "Engineering",
    ]
    locations = [
        "Pune HQ",
        "Mumbai Branch",
        "Bangalore Branch",
        "Delhi Branch",
        "Hyderabad Branch",
    ]
    specializations = [
        "System Architecture",
        "Database Optimization",
        "Cloud Infrastructure",
        "Security & Compliance",
        "Performance Tuning",
        "Python/Backend",
        "React/Frontend",
        "DevOps/Infrastructure",
        "QA/Testing",
        "Database/SQL",
    ]
    context = build_template_context(
        request,
        roles=roles,
        licenses=licenses,
        departments=departments,
        locations=locations,
        specializations=specializations,
        mode="create",
    )
    return templates.TemplateResponse(request, "user_config.html", context)


@router.get("/admin/users/{user_id}")
def user_view_page(request: Request, user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return redirect_with_flash("/admin/users", request, "User not found.", "error")
    user_dict = {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role,
        "license_type": user.license_type,
        "department": user.department,
        "location": user.location,
        "employee_id": user.employee_id,
        "specialization": user.specialization,
        "phone": user.phone,
        "status": user.status,
    }
    roles = []
    licenses = []
    context = build_template_context(request, user=user_dict, roles=roles, licenses=licenses, mode="view")
    return templates.TemplateResponse(request, "user_config.html", context)


@router.get("/admin/users/{user_id}/edit")
def user_edit_page(request: Request, user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return redirect_with_flash("/admin/users", request, "User not found.", "error")
    user_dict = {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role,
        "license_type": user.license_type,
        "department": user.department,
        "location": user.location,
        "employee_id": user.employee_id,
        "specialization": user.specialization,
        "phone": user.phone,
        "status": user.status,
    }
    roles = []
    licenses = []
    departments = [
        "Administration",
        "Project Management",
        "Operations",
        "Quality Assurance",
        "Field Operations",
        "Customer Support",
        "Technical Consulting",
        "Engineering",
    ]
    locations = [
        "Pune HQ",
        "Mumbai Branch",
        "Bangalore Branch",
        "Delhi Branch",
        "Hyderabad Branch",
    ]
    specializations = [
        "System Architecture",
        "Database Optimization",
        "Cloud Infrastructure",
        "Security & Compliance",
        "Performance Tuning",
        "Python/Backend",
        "React/Frontend",
        "DevOps/Infrastructure",
        "QA/Testing",
        "Database/SQL",
    ]
    context = build_template_context(
        request,
        user=user,
        roles=roles,
        licenses=licenses,
        departments=departments,
        locations=locations,
        specializations=specializations,
        mode="edit",
    )
    return templates.TemplateResponse(request, "user_config.html", context)


@router.get("/admin/licenses")
def licenses_list_page(request: Request, db: Session = Depends(get_db)):
    page = int(request.query_params.get("page", 1))
    db_licenses = db.query(License).order_by(License.id).all()
    all_licenses = [
        {
            "id": license.id,
            "name": license.name,
            "description": license.description,
            "max_users": license.max_users,
            "features": license.features,
        }
        for license in db_licenses
    ]
    pagination = paginate(all_licenses, page=page, per_page=50)
    context = build_template_context(request, licenses=pagination["items"], pagination=pagination)
    return templates.TemplateResponse(request, "licenses_list.html", context)


@router.get("/admin/licenses/{license_id}")
def license_detail_page(request: Request, license_id: int):
    all_licenses = _get_sample_licenses()
    # Find license by index (license_id is 1-based)
    if license_id < 1 or license_id > len(all_licenses):
        return redirect_with_flash("/admin/licenses", request, "License not found.", "error")
    
    license_obj = all_licenses[license_id - 1]
    edit_mode = request.query_params.get("edit", "").lower() == "true"
    
    context = build_template_context(request, license=license_obj, license_id=license_id, mode="edit" if edit_mode else "view", can_edit=True)
    return templates.TemplateResponse(request, "license_detail.html", context)


@router.post("/admin/licenses/{license_id}")
def license_update_page(request: Request, license_id: int):
    # Note: This is a placeholder. Since we're using sample data, actual updates aren't persisted.
    # In a real app, this would update the database.
    return redirect_with_flash(f"/admin/licenses/{license_id}", request, "License updated successfully.", "success")


@router.get("/admin/groups")
def groups_list_page(request: Request, db: Session = Depends(get_db)):
    page = int(request.query_params.get("page", 1))
    db_groups = db.query(Group).order_by(Group.id).all()
    all_groups = [
        {
            "id": group.id,
            "name": group.name,
            "description": group.description,
            "user_ids": group.user_ids,
            "member_count": group.member_count,
        }
        for group in db_groups
    ]
    pagination = paginate(all_groups, page=page, per_page=50)
    context = build_template_context(request, groups=pagination["items"], pagination=pagination)
    return templates.TemplateResponse(request, "groups_list.html", context)


@router.get("/admin/groups/new")
def groups_new_page(request: Request):
    managers = _get_sample_managers()
    context = build_template_context(request, managers=managers)
    return templates.TemplateResponse(request, "group_config.html", context)


@router.get("/admin/groups/{group_id}")
def view_group_page(group_id: int, request: Request, db: Session = Depends(get_db)):
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        # Fallback/create from sample group
        sample_groups = _get_sample_groups()
        sample_g = next((g for g in sample_groups if g["id"] == group_id), None)
        if sample_g:
            group = Group(
                id=group_id,
                name=sample_g["name"],
                description=sample_g["description"],
                user_ids=sample_g["user_ids"],
                member_count=sample_g["member_count"],
                data={},
            )
            db.add(group)
            db.commit()
            db.refresh(group)
        else:
            return redirect_with_flash("/admin/groups", request, "Group not found.", "error")
            
    db_users = db.query(User).all()
    user_map = {u.id: {
        "id": u.id,
        "full_name": u.full_name,
        "role": u.role,
        "department": u.department,
        "email": u.email,
        "status": u.status
    } for u in db_users}
    
    if not user_map:
        for u in _get_sample_users():
            user_map[u["id"]] = u
            
    group_users = [user_map[uid] for uid in (group.user_ids or []) if uid in user_map]
    
    group_dict = {
        "id": group.id,
        "name": group.name,
        "description": group.description,
        "user_ids": group.user_ids or [],
        "member_count": group.member_count or 0,
        **(group.data or {})
    }
    
    context = build_template_context(request, group=group_dict, group_users=group_users, mode="view")
    return templates.TemplateResponse(request, "group_config.html", context)


@router.get("/admin/groups/{group_id}/edit")
def edit_group_page(group_id: int, request: Request, db: Session = Depends(get_db)):
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        # Fallback/create from sample group
        sample_groups = _get_sample_groups()
        sample_g = next((g for g in sample_groups if g["id"] == group_id), None)
        if sample_g:
            group = Group(
                id=group_id,
                name=sample_g["name"],
                description=sample_g["description"],
                user_ids=sample_g["user_ids"],
                member_count=sample_g["member_count"],
                data={},
            )
            db.add(group)
            db.commit()
            db.refresh(group)
        else:
            return redirect_with_flash("/admin/groups", request, "Group not found.", "error")
            
    db_users = db.query(User).all()
    user_map = {u.id: {
        "id": u.id,
        "full_name": u.full_name,
        "role": u.role,
        "department": u.department,
        "email": u.email,
        "status": u.status
    } for u in db_users}
    
    if not user_map:
        for u in _get_sample_users():
            user_map[u["id"]] = u
            
    group_users = [user_map[uid] for uid in (group.user_ids or []) if uid in user_map]
    
    managers = [
        {
            "id": u.id,
            "full_name": u.full_name,
            "department": u.department
        }
        for u in db_users if u.role.lower() in ("supervisor", "manager", "admin", "administrator")
    ]
    if not managers:
        managers = _get_sample_managers()
        
    group_dict = {
        "id": group.id,
        "name": group.name,
        "description": group.description,
        "user_ids": group.user_ids or [],
        "member_count": group.member_count or 0,
        **(group.data or {})
    }
    
    context = build_template_context(request, group=group_dict, group_users=group_users, managers=managers, mode="edit")
    return templates.TemplateResponse(request, "group_config.html", context)


@router.post("/admin/groups")
async def create_group(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    data = parse_form_data(form)
    group = Group(
        name=data.get("name", "Untitled Group"),
        description=data.get("description", ""),
        user_ids=normalize_list(data.get("user_ids") or data.get("member_ids") or []),
        member_count=len(normalize_list(data.get("user_ids") or data.get("member_ids") or [])),
        data=data,
    )
    db.add(group)
    db.commit()
    return redirect_with_flash("/admin/groups", request, "Group saved successfully.", "success")


@router.post("/admin/groups/{group_id}")
async def update_group(group_id: int, request: Request, db: Session = Depends(get_db)):
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        # Fallback/create from sample group
        sample_groups = _get_sample_groups()
        sample_g = next((g for g in sample_groups if g["id"] == group_id), None)
        if sample_g:
            group = Group(
                id=group_id,
                name=sample_g["name"],
                description=sample_g["description"],
                user_ids=sample_g["user_ids"],
                member_count=sample_g["member_count"],
                data={},
            )
            db.add(group)
            db.commit()
            db.refresh(group)
        else:
            return redirect_with_flash("/admin/groups", request, "Group not found.", "error")
            
    form = await request.form()
    data = parse_form_data(form)
    
    group.name = data.get("name", group.name)
    group.description = data.get("description", group.description)
    
    existing_data = dict(group.data) if group.data else {}
    existing_data.update(data)
    group.data = existing_data
    
    db.commit()
    return redirect_with_flash(f"/admin/groups/{group_id}", request, "Group updated successfully.", "success")


@router.get("/admin/groups/{group_id}/manage-members")
def manage_group_members_page(group_id: int, request: Request, db: Session = Depends(get_db)):
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        # Fallback/create from sample group
        sample_groups = _get_sample_groups()
        sample_g = next((g for g in sample_groups if g["id"] == group_id), None)
        if sample_g:
            group = Group(
                id=group_id,
                name=sample_g["name"],
                description=sample_g["description"],
                user_ids=sample_g["user_ids"],
                member_count=sample_g["member_count"],
                data={},
            )
            db.add(group)
            db.commit()
            db.refresh(group)
        else:
            return redirect_with_flash("/admin/groups", request, "Group not found.", "error")
            
    db_users = db.query(User).all()
    all_users = [
        {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "department": user.department,
            "status": user.status,
        }
        for user in db_users
    ]
    
    group_dict = {
        "id": group.id,
        "name": group.name,
        "description": group.description,
        "user_ids": group.user_ids or [],
        "member_count": group.member_count or 0,
        **(group.data or {})
    }
    
    context = build_template_context(request, group=group_dict, all_users=all_users)
    return templates.TemplateResponse(request, "group_members.html", context)


@router.post("/admin/groups/{group_id}/manage-members")
async def update_group_members(group_id: int, request: Request, db: Session = Depends(get_db)):
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        # Fallback/create from sample group
        sample_groups = _get_sample_groups()
        sample_g = next((g for g in sample_groups if g["id"] == group_id), None)
        if sample_g:
            group = Group(
                id=group_id,
                name=sample_g["name"],
                description=sample_g["description"],
                user_ids=sample_g["user_ids"],
                member_count=sample_g["member_count"],
                data={},
            )
            db.add(group)
            db.commit()
            db.refresh(group)
        else:
            return redirect_with_flash("/admin/groups", request, "Group not found.", "error")
            
    form = await request.form()
    user_id_strs = form.getlist("user_ids")
    user_ids = []
    for uid_str in user_id_strs:
        try:
            user_ids.append(int(uid_str))
        except ValueError:
            pass
            
    group.user_ids = user_ids
    group.member_count = len(user_ids)
    db.commit()
    
    return redirect_with_flash(f"/admin/groups/{group_id}/edit", request, "Group members updated successfully.", "success")


@router.get("/admin/customers")
def customer_list_page(request: Request, db: Session = Depends(get_db)):
    page = int(request.query_params.get("page", 1))
    db_customers = db.query(Customer).order_by(Customer.id).all()
    all_customers = [
        {
            "id": customer.id,
            **(customer.data or {}),
        }
        for customer in db_customers
    ]
    pagination = paginate(all_customers, page=page, per_page=50)
    context = build_template_context(request, customers=pagination["items"], pagination=pagination)
    return templates.TemplateResponse(request, "customers_list.html", context)


@router.get("/admin/customers/new")
def customer_configuration_page(request: Request):
    context = build_template_context(request)
    return templates.TemplateResponse(request, "customer_config.html", context)


@router.post("/admin/customers")
async def create_or_update_customer(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    customer_id = form.get("customer_id")
    
    # Build customer data
    customer_name = form.get("customer_name", form.get("name", ""))
    primary_address = form.get("primary_address", "")
    contracts = form.get("contracts", "")
    
    # Build primary contact from form
    primary_contact = {
        "name": form.get("primary_contact_name", ""),
        "email": form.get("primary_contact_email", ""),
        "phone": form.get("primary_contact_phone", ""),
        "designation": form.get("primary_contact_designation", ""),
        "rank": form.get("primary_contact_rank", ""),
        "site": form.get("primary_contact_site", ""),
    }
    
    # Build additional contacts from form
    contact_names = form.getlist("contact_name[]")
    contact_emails = form.getlist("contact_email[]")
    contact_phones = form.getlist("contact_phone[]")
    contact_designations = form.getlist("contact_designation[]")
    contact_ranks = form.getlist("contact_rank[]")
    contact_sites = form.getlist("contact_site[]")
    
    additional_contacts = []
    for i in range(len(contact_names)):
        if contact_names[i]:  # Only add if name is not empty
            additional_contacts.append({
                "name": contact_names[i],
                "email": contact_emails[i] if i < len(contact_emails) else "",
                "phone": contact_phones[i] if i < len(contact_phones) else "",
                "designation": contact_designations[i] if i < len(contact_designations) else "",
                "rank": contact_ranks[i] if i < len(contact_ranks) else "",
                "site": contact_sites[i] if i < len(contact_sites) else "",
            })
    
    # Combine all contacts
    all_contacts = [primary_contact] + additional_contacts if primary_contact.get("name") else additional_contacts
    
    # Create data dictionary
    data = {
        "name": customer_name,
        "primary_address": primary_address,
        "contacts": all_contacts,
        "status": "Active",
        "contracts": contracts,
    }
    
    if customer_id:
        # Update existing customer
        customer = db.query(Customer).filter(Customer.id == int(customer_id)).first()
        if customer:
            customer.name = customer_name
            customer.data = data
            db.commit()
            return redirect_with_flash("/admin/customers", request, "Customer updated.", "success")
    
    # Create new customer
    customer = Customer(name=customer_name, data=data)
    db.add(customer)
    db.commit()
    return redirect_with_flash("/admin/customers", request, "Customer saved.", "success")


@router.get("/admin/customers/{customer_id}/delete")
def delete_customer(customer_id: int, request: Request, db: Session = Depends(get_db)):
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if customer:
        db.delete(customer)
        db.commit()
        return redirect_with_flash("/admin/customers", request, "Customer deleted.", "success")
    return redirect_with_flash("/admin/customers", request, "Customer not found.", "error")


def _get_sample_customers():
    return [
        {
            "id": 1,
            "name": "Acme Rail Systems",
            "primary_address": "Plot 12, Industrial Estate, Pune",
            "contact_name": "Ravi Kumar",
            "contact_email": "ravi.kumar@acme.example",
            "contact_phone": "+91 98765 43210",
            "status": "Active",
        },
        {
            "id": 2,
            "name": "MetroLine Services",
            "primary_address": "47 Transit Park, Mumbai",
            "contact_name": "Neha Singh",
            "contact_email": "neha.singh@metroline.example",
            "contact_phone": "+91 91234 56789",
            "status": "Active",
        },
        {
            "id": 3,
            "name": "Urban Transit Corp",
            "primary_address": "88 City Loop Rd, Delhi",
            "contact_name": "Arjun Mehta",
            "contact_email": "arjun.mehta@urban.example",
            "contact_phone": "+91 99887 66554",
            "status": "Expended",
        },
    ]


def _load_customers_and_contracts(db: Session):
    db_customers = db.query(Customer).order_by(Customer.id).all()
    customers = [{"id": c.id, **(c.data or {})} for c in db_customers]
    if not customers:
        customers = _get_sample_customers()
    db_contracts = db.query(Contract).order_by(Contract.id).all()
    contracts = []
    for c in db_contracts:
        cdata = c.data or {}
        if "customer_name" not in cdata and c.customer_id:
            cust = db.query(Customer).filter(Customer.id == c.customer_id).first()
            if cust:
                cdata["customer_name"] = (cust.data or {}).get("customer_name", cust.name)
        contracts.append({"id": c.id, **cdata})
    if not contracts:
        contracts = _get_sample_contracts()
    return customers, contracts


def _get_sample_contracts():
    items = [
        {
            "id": 101,
            "number": "CTR-2024-001",
            "customer_id": 1,
            "customer_name": "Acme Rail Systems",
            "executed_on": "2024-01-15",
            "valid_till": "2026-01-14",
            "status": "Active",
        },
        {
            "id": 102,
            "number": "CTR-2024-014",
            "customer_id": 2,
            "customer_name": "MetroLine Services",
            "executed_on": "2024-03-02",
            "valid_till": "2025-03-01",
            "status": "Active",
        },
        {
            "id": 103,
            "number": "CTR-2023-220",
            "customer_id": 3,
            "customer_name": "Urban Transit Corp",
            "executed_on": "2023-07-10",
            "valid_till": "2024-07-09",
            "status": "Expired",
        },
    ]
    for item in items:
        item.setdefault("main_deliverables", "LM: 10, GCS: 2, TMV: 4, Simulator: 1, LRU: 15")
        item.setdefault("main_warranty", True)
        item.setdefault("main_manuals", "User Manual v1.2 (2024-01-15), Maintenance Manual v1.0 (2024-01-20)")
        item.setdefault("sub_scheduled_maintenance", True)
        item.setdefault("sub_unscheduled_maintenance", True)
        item.setdefault("sub_calibration", True)
        item.setdefault("sub_software_upgrade", False)
        item.setdefault("sub_visits_record", "Scheduled: 4 visits/yr (2 engineers, 3 days). Unscheduled: As needed.")
        item.setdefault("sub_refresher_training", True)
    return items


def _get_sample_units(unit_type: str):
    base = {
        "LM": [
            {
                "id": 1001,
                "serial_number": "LM-0001",
                "unit_name": "LM Alpha",
                "customer_id": 1,
                "customer_name": "Acme Rail Systems",
                "contract_id": 101,
                "contract_number": "CTR-2024-001",
                "warranty_valid_from": "2024-02-01",
                "warranty_valid_to": "2026-02-01",
                "sap_part_number": "10000000001001",
                "customer_part_number": "80001001",
                "customer_part_no": "80001001",
                "make": "VajraCorp",
                "model": "VC-LM-V1",
                "software_version": "1.0.4",
                "status": "Active",
            },
            {
                "id": 1002,
                "serial_number": "LM-0002",
                "unit_name": "LM Bravo",
                "customer_id": 2,
                "customer_name": "MetroLine Services",
                "contract_id": 102,
                "contract_number": "CTR-2024-014",
                "warranty_valid_from": "2024-04-10",
                "warranty_valid_to": "2026-04-10",
                "sap_part_number": "10000000001002",
                "customer_part_number": "80001002",
                "customer_part_no": "80001002",
                "make": "VajraCorp",
                "model": "VC-LM-V2",
                "software_version": "1.0.4",
                "status": "Active",
            },
        ],
        "GCS": [
            {
                "id": 2001,
                "serial_number": "GCS-0101",
                "unit_name": "GCS North",
                "sap_part_number": "10000000002001",
                "customer_part_number": "80002001",
                "customer_id": 1,
                "customer_name": "Acme Rail Systems",
                "contract_id": 101,
                "contract_number": "CTR-2024-001",
                "warranty_valid_from": "2024-01-20",
                "warranty_valid_to": "2026-01-20",
                "make": "VajraCorp",
                "model": "VC-GCS-V1",
                "software_version": "1.0.4",
                "status": "Active",
            },
        ],
        "TMV": [
            {
                "id": 3001,
                "serial_number": "TMV-2201",
                "unit_name": "TMV Ranger",
                "customer_id": 2,
                "customer_name": "MetroLine Services",
                "contract_id": 102,
                "contract_number": "CTR-2024-014",
                "warranty_valid_from": "2024-05-01",
                "warranty_valid_to": "2026-05-01",
                "status": "Active",
                "sap_part_number": "20000000003001",
                "customer_part_number": "80003001",
                "make": "TMVCorp",
                "model": "Ranger-V1",
            },
        ],
        "SIM": [
            {
                "id": 4001,
                "serial_number": "SIM-3001",
                "unit_name": "Simulator Prime",
                "customer_id": 3,
                "customer_name": "Urban Transit Corp",
                "contract_id": 103,
                "contract_number": "CTR-2023-220",
                "warranty_valid_from": "2023-08-01",
                "warranty_valid_to": "2024-08-01",
                "sap_part_number": "10000000004001",
                "customer_part_number": "80004001",
                "customer_part_no": "80004001",
                "make": "VajraCorp",
                "model": "VC-SIM-V1",
                "software_version": "1.0.4",
                "status": "Expired",
            },
        ],
        "RDV": [
            {
                "id": 5001,
                "serial_number": "RDV-1001",
                "unit_name": "RDV Alpha",
                "sap_part_number": "20000000005001",
                "customer_part_no": "90005001",
                "customer_id": 1,
                "customer_name": "Acme Rail Systems",
                "contract_id": 101,
                "contract_number": "CTR-2024-001",
                "warranty_valid_from": "2024-03-01",
                "warranty_valid_to": "2026-03-01",
                "make": "RDVCorp",
                "model": "Alpha-V1",
                "last_servicing_done": "2024-09-01",
                "next_servicing_due": "2025-09-01",
                "status": "Active",
            },
        ],
        "BATTERY": [
            {
                "id": 7001,
                "serial_number": "BATT-0001",
                "unit_name": "Battery Pack Alpha",
                "sap_part_number": "10000000007001",
                "customer_part_number": "80007001",
                "customer_id": 1,
                "customer_name": "Acme Rail Systems",
                "contract_id": 101,
                "contract_number": "CTR-2024-001",
                "warranty_valid_from": "2024-02-01",
                "warranty_valid_to": "2026-02-01",
                "battery_type": "Lithium-Ion 12S 44.4V",
                "battery_and_its_types": "LiPo 12S",
                "battery_chargers": "Vajra Charger Dual",
                "make": "VajraCorp",
                "model": "VC-BATT-V1",
                "software_version": "1.0.4",
                "status": "Active",
            },
        ],
        "WARHEAD": [
            {
                "id": 8001,
                "serial_number": "WH-0001",
                "unit_name": "Warhead Charge Alpha",
                "sap_part_number": "10000000008001",
                "customer_part_number": "80008001",
                "customer_id": 1,
                "customer_name": "Acme Rail Systems",
                "contract_id": 101,
                "contract_number": "CTR-2024-001",
                "warranty_valid_from": "2024-02-01",
                "warranty_valid_to": "2026-02-01",
                "srlm_system": "LM",
                "make": "VajraCorp",
                "model": "VC-WH-V1",
                "software_version": "1.0.4",
                "status": "Active",
            },
        ],
        "MRLS": [
            {
                "id": 9001,
                "serial_number": "MRLS-1001",
                "unit_name": "MRLS Spare Kit Alpha",
                "sap_part_number": "10000000009001",
                "customer_part_number": "80009001",
                "customer_id": 1,
                "customer_name": "Acme Rail Systems",
                "contract_id": 101,
                "contract_number": "CTR-2024-001",
                "warranty_valid_from": "2024-03-01",
                "warranty_valid_to": "2026-03-01",
                "lru_serial_number": "LRU-1001",
                "lru_name": "Guidance Module",
                "platform_variant": "LM Alpha - (LM-0001)",
                "sub_system": "Navigation",
                "make": "VajraCorp",
                "model": "VC-MRLS-V1",
                "software_version": "1.0.4",
                "status": "Active",
            }
        ],
        "SMT_STE": [
            {
                "id": 9101,
                "serial_number": "SMT-1001",
                "unit_name": "SMT-STE Toolset Alpha",
                "sap_part_number": "10000000009101",
                "customer_part_number": "80009101",
                "customer_id": 1,
                "customer_name": "Acme Rail Systems",
                "contract_id": 101,
                "contract_number": "CTR-2024-001",
                "warranty_valid_from": "2024-03-01",
                "warranty_valid_to": "2026-03-01",
                "lru_serial_number": "SMT-STE-1001",
                "lru_name": "Hexagon Toolset",
                "platform_variant": "LM Alpha - (LM-0001)",
                "sub_system": "Mechanical Support",
                "make": "VajraCorp",
                "model": "VC-SMT-V1",
                "software_version": "1.0.4",
                "status": "Active",
            }
        ],
        "SAM": [
            {
                "id": 9201,
                "serial_number": "SAM-1001",
                "unit_name": "SAM System Alpha",
                "sap_part_number": "10000000009201",
                "customer_part_number": "80009201",
                "customer_id": 1,
                "customer_name": "Acme Rail Systems",
                "contract_id": 101,
                "contract_number": "CTR-2024-001",
                "warranty_valid_from": "2024-03-01",
                "warranty_valid_to": "2026-03-01",
                "srlm_system": "LM",
                "make": "VajraCorp",
                "model": "VC-SAM-V1",
                "software_version": "1.0.4",
                "status": "Active",
            }
        ],
    }
    return base.get(unit_type, [])


def _get_sample_platform_variants():
    return [
        "LM Alpha - (LM-0001)",
        "LM Bravo - (LM-0002)",
        "GCS North - (GCS-0101)",
        "TMV Ranger - (TMV-2201)",
        "Simulator Prime - (SIM-3001)",
    ]


def _get_sample_lrus():
    items = [
        {
            "id": 5001,
            "serial_number": "LRU-1001",
            "name": "Guidance Module",
            "platform_variant": "LM Alpha - (LM-0001)",
            "sub_system": "Navigation",
            "status": "Active",
        },
        {
            "id": 5002,
            "serial_number": "LRU-2033",
            "name": "Comm Unit",
            "platform_variant": "GCS North - (GCS-0101)",
            "sub_system": "Communications",
            "status": "Active",
        },
        {
            "id": 5003,
            "serial_number": "LRU-1002",
            "name": "Airframe Sensor Pack",
            "platform_variant": "LM Alpha - (LM-0001)",
            "sub_system": "Airframe",
            "status": "Active",
        },
        {
            "id": 5004,
            "serial_number": "LRU-1003",
            "name": "Airframe Control Unit",
            "platform_variant": "LM Alpha - (LM-0001)",
            "sub_system": "Airframe",
            "status": "Active",
        },
        {
            "id": 5005,
            "serial_number": "LRU-1004",
            "name": "Propulsion Pump",
            "platform_variant": "LM Alpha - (LM-0001)",
            "sub_system": "Propulsion",
            "status": "Active",
        },
        {
            "id": 5006,
            "serial_number": "LRU-1005",
            "name": "Propulsion Controller",
            "platform_variant": "LM Alpha - (LM-0001)",
            "sub_system": "Propulsion",
            "status": "Active",
        },
        {
            "id": 5007,
            "serial_number": "LRU-1006",
            "name": "Flight Computer",
            "platform_variant": "LM Alpha - (LM-0001)",
            "sub_system": "Avionics & Flight Control",
            "status": "Active",
        },
        {
            "id": 5008,
            "serial_number": "LRU-1007",
            "name": "Autopilot Module",
            "platform_variant": "LM Alpha - (LM-0001)",
            "sub_system": "Avionics & Flight Control",
            "status": "Active",
        },
        {
            "id": 5009,
            "serial_number": "LRU-1008",
            "name": "Data Link Radio",
            "platform_variant": "LM Alpha - (LM-0001)",
            "sub_system": "Communication",
            "status": "Active",
        },
        {
            "id": 5010,
            "serial_number": "LRU-1009",
            "name": "Antenna Array",
            "platform_variant": "LM Alpha - (LM-0001)",
            "sub_system": "Communication",
            "status": "Active",
        },
        {
            "id": 5011,
            "serial_number": "LRU-1010",
            "name": "Payload Control Unit",
            "platform_variant": "LM Alpha - (LM-0001)",
            "sub_system": "Payload",
            "status": "Active",
        },
        {
            "id": 5012,
            "serial_number": "LRU-1011",
            "name": "Payload Sensor",
            "platform_variant": "LM Alpha - (LM-0001)",
            "sub_system": "Payload",
            "status": "Active",
        },
        {
            "id": 5013,
            "serial_number": "LRU-2101",
            "name": "Compute Node A",
            "platform_variant": "GCS North - (GCS-0101)",
            "sub_system": "Computing",
            "status": "Active",
        },
        {
            "id": 5014,
            "serial_number": "LRU-2102",
            "name": "Compute Node B",
            "platform_variant": "GCS North - (GCS-0101)",
            "sub_system": "Computing",
            "status": "Active",
        },
        {
            "id": 5015,
            "serial_number": "LRU-2103",
            "name": "Comms Router",
            "platform_variant": "GCS North - (GCS-0101)",
            "sub_system": "Communication",
            "status": "Active",
        },
        {
            "id": 5016,
            "serial_number": "LRU-2104",
            "name": "Comms Gateway",
            "platform_variant": "GCS North - (GCS-0101)",
            "sub_system": "Communication",
            "status": "Active",
        },
        {
            "id": 5017,
            "serial_number": "LRU-2105",
            "name": "Display Panel A",
            "platform_variant": "GCS North - (GCS-0101)",
            "sub_system": "Display",
            "status": "Active",
        },
        {
            "id": 5018,
            "serial_number": "LRU-2106",
            "name": "Display Panel B",
            "platform_variant": "GCS North - (GCS-0101)",
            "sub_system": "Display",
            "status": "Active",
        },
        {
            "id": 5019,
            "serial_number": "LRU-2107",
            "name": "Control Console",
            "platform_variant": "GCS North - (GCS-0101)",
            "sub_system": "Control Interface",
            "status": "Active",
        },
        {
            "id": 5020,
            "serial_number": "LRU-2108",
            "name": "Input Device Hub",
            "platform_variant": "GCS North - (GCS-0101)",
            "sub_system": "Control Interface",
            "status": "Active",
        },
        {
            "id": 5021,
            "serial_number": "LRU-2109",
            "name": "Power Supply A",
            "platform_variant": "GCS North - (GCS-0101)",
            "sub_system": "Power",
            "status": "Active",
        },
        {
            "id": 5022,
            "serial_number": "LRU-2110",
            "name": "Power Supply B",
            "platform_variant": "GCS North - (GCS-0101)",
            "sub_system": "Power",
            "status": "Active",
        },
        {
            "id": 5023,
            "serial_number": "LRU-3101",
            "name": "Transmission Module",
            "platform_variant": "TMV Ranger - (TMV-2201)",
            "sub_system": "Powertrain",
            "status": "Active",
        },
        {
            "id": 5024,
            "serial_number": "LRU-3102",
            "name": "Engine Control Unit",
            "platform_variant": "TMV Ranger - (TMV-2201)",
            "sub_system": "Powertrain",
            "status": "Active",
        },
        {
            "id": 5025,
            "serial_number": "LRU-3103",
            "name": "Battery Pack",
            "platform_variant": "TMV Ranger - (TMV-2201)",
            "sub_system": "Electrical",
            "status": "Active",
        },
        {
            "id": 5026,
            "serial_number": "LRU-3104",
            "name": "Power Distribution Unit",
            "platform_variant": "TMV Ranger - (TMV-2201)",
            "sub_system": "Electrical",
            "status": "Active",
        },
        {
            "id": 5027,
            "serial_number": "LRU-3105",
            "name": "Vehicle Radio",
            "platform_variant": "TMV Ranger - (TMV-2201)",
            "sub_system": "Communication",
            "status": "Active",
        },
        {
            "id": 5028,
            "serial_number": "LRU-3106",
            "name": "Satellite Modem",
            "platform_variant": "TMV Ranger - (TMV-2201)",
            "sub_system": "Communication",
            "status": "Active",
        },
        {
            "id": 5029,
            "serial_number": "LRU-3107",
            "name": "Nav Sensor",
            "platform_variant": "TMV Ranger - (TMV-2201)",
            "sub_system": "Navigation",
            "status": "Active",
        },
        {
            "id": 5030,
            "serial_number": "LRU-3108",
            "name": "GPS Module",
            "platform_variant": "TMV Ranger - (TMV-2201)",
            "sub_system": "Navigation",
            "status": "Active",
        },
        {
            "id": 5031,
            "serial_number": "LRU-3109",
            "name": "Payload Arm",
            "platform_variant": "TMV Ranger - (TMV-2201)",
            "sub_system": "Payload Handling",
            "status": "Active",
        },
        {
            "id": 5032,
            "serial_number": "LRU-3110",
            "name": "Payload Lift",
            "platform_variant": "TMV Ranger - (TMV-2201)",
            "sub_system": "Payload Handling",
            "status": "Active",
        },
        {
            "id": 5033,
            "serial_number": "LRU-4101",
            "name": "Sim Compute Node",
            "platform_variant": "Simulator Prime - (SIM-3001)",
            "sub_system": "Computing",
            "status": "Active",
        },
        {
            "id": 5034,
            "serial_number": "LRU-4102",
            "name": "Sim GPU Module",
            "platform_variant": "Simulator Prime - (SIM-3001)",
            "sub_system": "Computing",
            "status": "Active",
        },
        {
            "id": 5035,
            "serial_number": "LRU-4103",
            "name": "Display Controller",
            "platform_variant": "Simulator Prime - (SIM-3001)",
            "sub_system": "Display",
            "status": "Active",
        },
        {
            "id": 5036,
            "serial_number": "LRU-4104",
            "name": "Projection Unit",
            "platform_variant": "Simulator Prime - (SIM-3001)",
            "sub_system": "Display",
            "status": "Active",
        },
        {
            "id": 5037,
            "serial_number": "LRU-4105",
            "name": "Control Console",
            "platform_variant": "Simulator Prime - (SIM-3001)",
            "sub_system": "Control",
            "status": "Active",
        },
        {
            "id": 5038,
            "serial_number": "LRU-4106",
            "name": "Control Interface Hub",
            "platform_variant": "Simulator Prime - (SIM-3001)",
            "sub_system": "Control",
            "status": "Active",
        },
        {
            "id": 5039,
            "serial_number": "LRU-4107",
            "name": "Audio Mixer",
            "platform_variant": "Simulator Prime - (SIM-3001)",
            "sub_system": "Audio",
            "status": "Active",
        },
        {
            "id": 5040,
            "serial_number": "LRU-4108",
            "name": "Speaker Array",
            "platform_variant": "Simulator Prime - (SIM-3001)",
            "sub_system": "Audio",
            "status": "Active",
        },
        {
            "id": 5041,
            "serial_number": "LRU-4109",
            "name": "Simulation Core",
            "platform_variant": "Simulator Prime - (SIM-3001)",
            "sub_system": "Software",
            "status": "Active",
        },
        {
            "id": 5042,
            "serial_number": "LRU-4110",
            "name": "Scenario Engine",
            "platform_variant": "Simulator Prime - (SIM-3001)",
            "sub_system": "Software",
            "status": "Active",
        },
        {
            "id": 5043,
            "serial_number": "LRU-1201",
            "name": "Guidance Module B",
            "platform_variant": "LM Bravo - (LM-0002)",
            "sub_system": "Navigation",
            "status": "Active",
        },
        {
            "id": 5044,
            "serial_number": "LRU-1202",
            "name": "Airframe Sensor Pack B",
            "platform_variant": "LM Bravo - (LM-0002)",
            "sub_system": "Airframe",
            "status": "Active",
        },
        {
            "id": 5045,
            "serial_number": "LRU-1203",
            "name": "Airframe Control Unit B",
            "platform_variant": "LM Bravo - (LM-0002)",
            "sub_system": "Airframe",
            "status": "Active",
        },
        {
            "id": 5046,
            "serial_number": "LRU-1204",
            "name": "Propulsion Pump B",
            "platform_variant": "LM Bravo - (LM-0002)",
            "sub_system": "Propulsion",
            "status": "Active",
        },
        {
            "id": 5047,
            "serial_number": "LRU-1205",
            "name": "Propulsion Controller B",
            "platform_variant": "LM Bravo - (LM-0002)",
            "sub_system": "Propulsion",
            "status": "Active",
        },
        {
            "id": 5048,
            "serial_number": "LRU-1206",
            "name": "Flight Computer B",
            "platform_variant": "LM Bravo - (LM-0002)",
            "sub_system": "Avionics & Flight Control",
            "status": "Active",
        },
        {
            "id": 5049,
            "serial_number": "LRU-1207",
            "name": "Autopilot Module B",
            "platform_variant": "LM Bravo - (LM-0002)",
            "sub_system": "Avionics & Flight Control",
            "status": "Active",
        },
        {
            "id": 5050,
            "serial_number": "LRU-1208",
            "name": "Data Link Radio B",
            "platform_variant": "LM Bravo - (LM-0002)",
            "sub_system": "Communication",
            "status": "Active",
        },
        {
            "id": 5051,
            "serial_number": "LRU-1209",
            "name": "Antenna Array B",
            "platform_variant": "LM Bravo - (LM-0002)",
            "sub_system": "Communication",
            "status": "Active",
        },
        {
            "id": 5052,
            "serial_number": "LRU-1210",
            "name": "Payload Control Unit B",
            "platform_variant": "LM Bravo - (LM-0002)",
            "sub_system": "Payload",
            "status": "Active",
        },
        {
            "id": 5053,
            "serial_number": "LRU-1211",
            "name": "Payload Sensor B",
            "platform_variant": "LM Bravo - (LM-0002)",
            "sub_system": "Payload",
            "status": "Active",
        },
    ]
    for idx, item in enumerate(items):
        item.setdefault("sap_part_number", f"1000000000{5000+idx}")
        item.setdefault("customer_part_number", f"8000{3000+idx}")
        item.setdefault("make", "VajraCorp")
        item.setdefault("model", f"VC-{item['name'].split()[0]}-V1")
        item.setdefault("software_version", "1.0.4")
    return items


def _get_sample_sub_systems():
    return [
        {
            "id": 6001,
            "srlm_system": "LM",
            "sub_system": "Navigation",
            "status": "Active",
        },
        {
            "id": 6002,
            "srlm_system": "GCS",
            "sub_system": "Communications",
            "status": "Active",
        },
        {
            "id": 6003,
            "srlm_system": "LM",
            "sub_system": "Airframe",
            "status": "Active",
        },
        {
            "id": 6004,
            "srlm_system": "LM",
            "sub_system": "Propulsion",
            "status": "Active",
        },
        {
            "id": 6005,
            "srlm_system": "LM",
            "sub_system": "Avionics & Flight Control",
            "status": "Active",
        },
        {
            "id": 6006,
            "srlm_system": "LM",
            "sub_system": "Communication",
            "status": "Active",
        },
        {
            "id": 6007,
            "srlm_system": "LM",
            "sub_system": "Payload",
            "status": "Active",
        },
        {
            "id": 6008,
            "srlm_system": "GCS",
            "sub_system": "Computing",
            "status": "Active",
        },
        {
            "id": 6009,
            "srlm_system": "GCS",
            "sub_system": "Communication",
            "status": "Active",
        },
        {
            "id": 6010,
            "srlm_system": "GCS",
            "sub_system": "Display",
            "status": "Active",
        },
        {
            "id": 6011,
            "srlm_system": "GCS",
            "sub_system": "Control Interface",
            "status": "Active",
        },
        {
            "id": 6012,
            "srlm_system": "GCS",
            "sub_system": "Power",
            "status": "Active",
        },
        {
            "id": 6013,
            "srlm_system": "TMV",
            "sub_system": "Powertrain",
            "status": "Active",
        },
        {
            "id": 6014,
            "srlm_system": "TMV",
            "sub_system": "Electrical",
            "status": "Active",
        },
        {
            "id": 6015,
            "srlm_system": "TMV",
            "sub_system": "Communication",
            "status": "Active",
        },
        {
            "id": 6016,
            "srlm_system": "TMV",
            "sub_system": "Navigation",
            "status": "Active",
        },
        {
            "id": 6017,
            "srlm_system": "TMV",
            "sub_system": "Payload Handling",
            "status": "Active",
        },
        {
            "id": 6018,
            "srlm_system": "Simulator",
            "sub_system": "Computing",
            "status": "Active",
        },
        {
            "id": 6019,
            "srlm_system": "Simulator",
            "sub_system": "Display",
            "status": "Active",
        },
        {
            "id": 6020,
            "srlm_system": "Simulator",
            "sub_system": "Control",
            "status": "Active",
        },
        {
            "id": 6021,
            "srlm_system": "Simulator",
            "sub_system": "Audio",
            "status": "Active",
        },
        {
            "id": 6022,
            "srlm_system": "Simulator",
            "sub_system": "Software",
            "status": "Active",
        },
    ]


@router.get("/admin/customers/{customer_id}")
def customer_view_page(request: Request, customer_id: int, db: Session = Depends(get_db)):
    customer_obj = db.query(Customer).filter(Customer.id == customer_id).first()
    contracts = []
    if customer_obj:
        customer = {"id": customer_obj.id, **(customer_obj.data or {})}
        # Load contracts for this customer
        db_contracts = db.query(Contract).filter(Contract.customer_id == customer_id).all()
        contracts = [{"id": c.id, "number": c.number, **(c.data or {})} for c in db_contracts]
    else:
        customer = next((item for item in _get_sample_customers() if item["id"] == customer_id), None)
    context = build_template_context(request, customer=customer, contracts=contracts, mode="view")
    return templates.TemplateResponse(request, "customer_config.html", context)


@router.get("/admin/customers/{customer_id}/edit")
def customer_edit_page(request: Request, customer_id: int, db: Session = Depends(get_db)):
    customer_obj = db.query(Customer).filter(Customer.id == customer_id).first()
    contracts = []
    if customer_obj:
        customer = {"id": customer_obj.id, **(customer_obj.data or {})}
        # Load contracts for this customer
        db_contracts = db.query(Contract).filter(Contract.customer_id == customer_id).all()
        contracts = [{"id": c.id, "number": c.number, **(c.data or {})} for c in db_contracts]
    else:
        customer = next((item for item in _get_sample_customers() if item["id"] == customer_id), None)
    context = build_template_context(request, customer=customer, contracts=contracts, mode="edit")
    return templates.TemplateResponse(request, "customer_config.html", context)


@router.get("/admin/customers/{customer_id}/disable")
def customer_disable(request: Request, customer_id: int):
    return redirect_with_flash("/admin/customers", request, "Customer expended.", "success")


@router.get("/admin/contracts")
def contracts_list_page(request: Request, db: Session = Depends(get_db)):
    page = int(request.query_params.get("page", 1))
    db_contracts = db.query(Contract).order_by(Contract.id).all()
    all_contracts = [
        entity_to_dict(contract, db=db, top_level_fields=["number", "customer_id"])
        for contract in db_contracts
    ]
    
    import datetime
    today = datetime.date.today()
    for contract in all_contracts:
        valid_till = contract.get("valid_till")
        if valid_till:
            try:
                vt_date = datetime.datetime.strptime(valid_till, "%Y-%m-%d").date()
                if vt_date < today:
                    contract["status"] = "Expired"
            except Exception:
                pass
                
    pagination = paginate(all_contracts, page=page, per_page=50)
    context = build_template_context(request, contracts=pagination["items"], pagination=pagination)
    return templates.TemplateResponse(request, "contracts_list.html", context)


@router.post("/admin/contracts")
async def create_contract(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    data = parse_form_data(form)
    
    # Auto-expire if date is in the past
    valid_till = data.get("valid_till")
    if valid_till:
        try:
            import datetime
            vt_date = datetime.datetime.strptime(valid_till, "%Y-%m-%d").date()
            if vt_date < datetime.date.today():
                data["status"] = "Expired"
        except Exception:
            pass
            
    customer_id = parse_int(data.get("customer") or data.get("customer_id"))
    contract = Contract(
        number=data.get("contract_number", ""),
        customer_id=customer_id,
        data=data,
    )
    db.add(contract)
    db.commit()
    return redirect_with_flash("/admin/contracts", request, "Contract saved.", "success")


@router.post("/admin/contracts/{contract_id}")
async def update_contract(request: Request, contract_id: int, db: Session = Depends(get_db)):
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        return redirect_with_flash("/admin/contracts", request, "Contract not found.", "error")
    
    form = await request.form()
    data = parse_form_data(form)
    
    # Auto-expire if date is in the past
    valid_till = data.get("valid_till")
    if valid_till:
        try:
            import datetime
            vt_date = datetime.datetime.strptime(valid_till, "%Y-%m-%d").date()
            if vt_date < datetime.date.today():
                data["status"] = "Expired"
        except Exception:
            pass
            
    customer_id = parse_int(data.get("customer") or data.get("customer_id"))
    
    contract.number = data.get("contract_number", contract.number)
    contract.customer_id = customer_id
    contract.data = data
    
    db.commit()
    return redirect_with_flash("/admin/contracts", request, "Contract updated.", "success")


@router.get("/admin/tables")
def tables_list_page(request: Request):
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    tables = [name for name in tables if not name.startswith("sqlite_")]
    table_info = []
    for table_name in tables:
        columns = inspector.get_columns(table_name)
        row_count = None
        try:
            with engine.connect() as conn:
                row_count = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar_one()
        except Exception:
            row_count = None

        table_info.append({
            "name": table_name,
            "db_column_count": len(columns),
            "db_columns": [col["name"] for col in columns],
            "row_count": row_count,
        })

    template_dir = Path("templates")
    form_rules = {
        "batteries": "battery_config.html",
        "battery_types": "battery_types.html",
        "ground_control_systems": "ground_control_system.html",
        "loitering_munitions": "loitering_munition.html",
        "contracts": "contract_config.html",
        "customers": "customer_config.html",
        "tactical_mobility_vehicles": "tactical_mobility_vehicle.html",
        "simulators": "simulator.html",
        "rapid_deployment_vehicles": "rapid_deployment_vehicle.html",
        "mrls": "mrls_config.html",
        "warheads": "warhead_config.html",
        "smt_stes": "smt_ste_config.html",
        "sams": "sam_config.html",
        "lrus": "lru_config.html",
        "sub_systems": "sub_systems_config.html",
        "groups": "group_config.html",
        "licenses": "license_detail.html",
        "users": "user_config.html",
        "workflows": "builder.html",
        "stages": "builder.html",
        "task_definitions": "builder.html",
        "knowledge_articles": "knowledge_article_form.html",
        "knowledge_documents": "knowledge_form.html",
    }

    for info in table_info:
        template_name = form_rules.get(info["name"])
        db_cols_set = set(info["db_columns"])
        
        # Standard system columns that shouldn't be in forms
        system_columns = {"id", "created_at", "updated_at", "data"}
        
        if template_name:
            path = template_dir / template_name
            if path.exists():
                content = path.read_text(encoding="utf-8")
                found = re.findall(r'name=(?:"([^"]+)"|\'([^\']+)\')', content)
                fields = {item[0] or item[1] for item in found if item[0] or item[1]}
                
                # Remove array notation (e.g., "name[]" -> "name")
                clean_fields = set()
                for field in fields:
                    clean_field = field.rstrip("[]")
                    # Skip Jinja2 template syntax
                    if not clean_field.startswith("{{"):
                        clean_fields.add(clean_field)
                
                info["form_fields"] = sorted(clean_fields)
                info["form_columns"] = len(info["form_fields"])
                
                # If table has a "data" column, all form fields are OK (they go into JSON)
                explicit_columns = db_cols_set - system_columns
                
                if "data" in db_cols_set:
                    # Form fields can go into the data JSON column - no issues
                    info["missing_fields"] = []
                    info["has_issues"] = False
                else:
                    # No data column - fields must match explicit columns
                    missing_in_db = sorted(clean_fields - explicit_columns)
                    info["missing_fields"] = missing_in_db
                    info["has_issues"] = len(missing_in_db) > 0
            else:
                info["form_fields"] = []
                info["form_columns"] = None
                info["missing_fields"] = []
                info["has_issues"] = False
        else:
            info["form_fields"] = []
            info["form_columns"] = None
            info["missing_fields"] = []
            info["has_issues"] = False

    context = build_template_context(request, tables=table_info)
    return templates.TemplateResponse(request, "tables_list.html", context)


@router.get("/admin/contracts/new")
def contract_configuration_page(request: Request, db: Session = Depends(get_db)):
    db_customers = db.query(Customer).order_by(Customer.id).all()
    customers = [{"id": c.id, "name": c.name, **(c.data or {})} for c in db_customers]
    context = build_template_context(request, customers=customers)
    return templates.TemplateResponse(request, "contract_config.html", context)


@router.get("/admin/contracts/{contract_id}")
def contract_view_page(request: Request, contract_id: int, db: Session = Depends(get_db)):
    contract_obj = db.query(Contract).filter(Contract.id == contract_id).first()
    if contract_obj:
        contract = entity_to_dict(contract_obj, db=db, top_level_fields=["number", "customer_id"])
    else:
        contract = next((item for item in _get_sample_contracts() if item["id"] == contract_id), None)
        
    if contract:
        valid_till = contract.get("valid_till")
        if valid_till:
            try:
                import datetime
                vt_date = datetime.datetime.strptime(valid_till, "%Y-%m-%d").date()
                if vt_date < datetime.date.today():
                    contract["status"] = "Expired"
            except Exception:
                pass
                
    db_customers = db.query(Customer).order_by(Customer.id).all()
    customers = [{"id": c.id, "name": c.name, **(c.data or {})} for c in db_customers]
    context = build_template_context(request, contract=contract, customers=customers, mode="view")
    return templates.TemplateResponse(request, "contract_config.html", context)


@router.get("/admin/contracts/{contract_id}/edit")
def contract_edit_page(request: Request, contract_id: int, db: Session = Depends(get_db)):
    contract_obj = db.query(Contract).filter(Contract.id == contract_id).first()
    if contract_obj:
        contract = entity_to_dict(contract_obj, db=db, top_level_fields=["number", "customer_id"])
    else:
        contract = next((item for item in _get_sample_contracts() if item["id"] == contract_id), None)
        
    if contract:
        valid_till = contract.get("valid_till")
        if valid_till:
            try:
                import datetime
                vt_date = datetime.datetime.strptime(valid_till, "%Y-%m-%d").date()
                if vt_date < datetime.date.today():
                    contract["status"] = "Expired"
            except Exception:
                pass
                
    db_customers = db.query(Customer).order_by(Customer.id).all()
    customers = [{"id": c.id, "name": c.name, **(c.data or {})} for c in db_customers]
    context = build_template_context(request, contract=contract, customers=customers, mode="edit")
    return templates.TemplateResponse(request, "contract_config.html", context)


@router.get("/admin/contracts/{contract_id}/disable")
def contract_disable(request: Request, contract_id: int):
    return redirect_with_flash("/admin/contracts", request, "Contract expended.", "success")


@router.get("/admin/lm")
def loitering_munition_list_page(request: Request, db: Session = Depends(get_db)):
    page = int(request.query_params.get("page", 1))
    status_filter = request.query_params.get("status")  # next-month, next-quarter, past-due
    warranty_filter = request.query_params.get("warranty")  # expired, expiring, active
    
    all_units = list_or_sample(db, LoiteringMunition, unit_type="LM", top_level_fields=["unit_name", "serial_number"])
    
    # Load contracts to override warranty dates dynamically
    _, contracts = _load_customers_and_contracts(db)
    import datetime
    today = datetime.date.today()
    month_start = today.replace(day=1)
    month_end = (month_start + datetime.timedelta(days=32)).replace(day=1) - datetime.timedelta(days=1)
    next_month_start = (month_end + datetime.timedelta(days=1))
    next_month_end = (next_month_start + datetime.timedelta(days=32)).replace(day=1) - datetime.timedelta(days=1)
    quarter_end = today + datetime.timedelta(days=90)
    
    filtered_units = []
    for u in all_units:
        c_id = u.get("contract_id")
        c_num = u.get("contract_number")
        con = None
        if c_id:
            con = next((c for c in contracts if str(c.get("id")) == str(c_id)), None)
        if not con and c_num:
            con = next((c for c in contracts if str(c.get("number")) == str(c_num)), None)
        
        warranty_status = "unknown"
        service_status = "unknown"
        
        # Check warranty status
        warranty_date_str = None
        if con:
            u["warranty_valid_from"] = con.get("executed_on", "")
            u["warranty_valid_to"] = con.get("valid_till", "")
            warranty_date_str = con.get("valid_till", "")
        else:
            warranty_date_str = u.get("warranty_valid_to")
        
        if warranty_date_str:
            try:
                warranty_date = datetime.datetime.strptime(warranty_date_str, "%Y-%m-%d").date()
                if warranty_date < today:
                    warranty_status = "expired"
                    if month_start <= warranty_date <= month_end:
                        warranty_status = "expired"
                elif month_start <= warranty_date <= month_end:
                    warranty_status = "expired"
                elif next_month_start <= warranty_date <= next_month_end:
                    warranty_status = "expiring"
                elif warranty_date <= quarter_end:
                    warranty_status = "expiring"
                else:
                    warranty_status = "active"
            except ValueError:
                pass
        
        # Check service status (from seeded data which is merged into dict by entity_to_dict)
        next_service_due_str = u.get('next_service_due')
        
        if next_service_due_str:
            try:
                next_service_date = datetime.datetime.strptime(next_service_due_str, "%d-%m-%Y").date()
                if next_service_date < today:
                    service_status = "past-due"
                elif next_service_date <= month_end:
                    service_status = "next-month"
                elif next_service_date <= quarter_end:
                    service_status = "next-quarter"
            except ValueError:
                pass
        
        # Apply filters
        include_unit = True
        if status_filter:
            include_unit = (service_status == status_filter)
        elif warranty_filter:
            include_unit = (warranty_status == warranty_filter)
        
        if include_unit:
            u["warranty_status"] = warranty_status
            u["service_status"] = service_status
            filtered_units.append(u)

    pagination = paginate(filtered_units, page=page, per_page=50)
    context = build_template_context(request, units=pagination["items"], unit_label="Loitering Munition (LM)", pagination=pagination)
    return templates.TemplateResponse(request, "lm_list.html", context)


@router.get("/admin/lm/new")
def loitering_munition_new_page(request: Request, db: Session = Depends(get_db)):
    customers, contracts = _load_customers_and_contracts(db)
    context = build_template_context(
        request, 
        customers=customers, 
        contracts=contracts,
        route_cards=LM_ROUTE_CARDS,
        kitting_items=[]
    )
    return templates.TemplateResponse(request, "loitering_munition.html", context)


@router.get("/admin/master-products")
def master_products_list_page(request: Request, db: Session = Depends(get_db)):
    """Master Product Table - Replaced by LM Kitting table data and columns"""
    page = int(request.query_params.get("page", 1))
    q = request.query_params.get("q", "").strip()
    
    query = db.query(KittingItem).filter(KittingItem.product_category == "LM")
    if q:
        query = query.filter(
            (KittingItem.part_number.ilike(f"%{q}%")) |
            (KittingItem.sap_part_number.ilike(f"%{q}%")) |
            (KittingItem.material_description.ilike(f"%{q}%")) |
            (KittingItem.product_serial_no.ilike(f"%{q}%")) |
            (KittingItem.route_card_description.ilike(f"%{q}%")) |
            (KittingItem.subsystems.ilike(f"%{q}%"))
        )
    
    all_items = query.order_by(KittingItem.id.desc()).all()
    pagination = paginate(all_items, page=page, per_page=50)
    
    context = build_template_context(
        request, 
        items=pagination["items"], 
        pagination=pagination, 
        q=q
    )
    return templates.TemplateResponse(request, "master_product_table.html", context)


LM_ROUTE_CARDS = [
    "LH Side Wing Integration Assembly",
    "RH Side Wing Integration Assembly",
    "LH Empennage Integration Assembly",
    "RH Empennage Integration Assembly",
    "VTOL Boom Bracket Integration Assembly LH",
    "VTOL Boom Bracket Integration Assembly RH",
    "Centre Wing Integration Assembly",
    "Fuselage Integration Assembly",
    "Aircraft ERLM Assembly"
]

GCS_ROUTE_CARDS = [
    "GCS Shelter Integration Assembly",
    "GCS Ground Antenna Integration Assembly"
]


@router.get("/admin/lm/{unit_id}")
def loitering_munition_view_page(request: Request, unit_id: int, db: Session = Depends(get_db)):
    unit = load_entity(db, LoiteringMunition, unit_type="LM", unit_id=unit_id, top_level_fields=["unit_name", "serial_number"])
    customers, contracts = _load_customers_and_contracts(db)
    if unit and unit.get("contract_id"):
        con = next((c for c in contracts if str(c.get("id")) == str(unit.get("contract_id"))), None)
        if con:
            unit["warranty_valid_from"] = con.get("executed_on", "")
            unit["warranty_valid_to"] = con.get("valid_till", "")
    
    kitting_items = []
    if unit and "serial_number" in unit:
        db_items = db.query(KittingItem).filter(
            KittingItem.product_serial_no == unit["serial_number"],
            KittingItem.product_category == "LM"
        ).all()
        kitting_items = [
            {
                "id": item.id,
                "part_number": item.part_number,
                "sap_part_number": item.sap_part_number,
                "material_description": item.material_description,
                "batch_no_po_no": item.batch_no_po_no,
                "material_serial_no": item.material_serial_no,
                "weight_in_grams": item.weight_in_grams,
                "required_quantity": item.required_quantity,
                "uom": item.uom,
                "remarks": item.remarks,
                "subsystems": item.subsystems,
                "route_card_description": item.route_card_description,
            }
            for item in db_items
        ]
        
    context = build_template_context(
        request, 
        unit=unit, 
        customers=customers, 
        contracts=contracts, 
        mode="view",
        route_cards=LM_ROUTE_CARDS,
        kitting_items=kitting_items
    )
    return templates.TemplateResponse(request, "loitering_munition.html", context)


@router.get("/admin/lm/{unit_id}/edit")
def loitering_munition_edit_page(request: Request, unit_id: int, db: Session = Depends(get_db)):
    unit = load_entity(db, LoiteringMunition, unit_type="LM", unit_id=unit_id, top_level_fields=["unit_name", "serial_number"])
    customers, contracts = _load_customers_and_contracts(db)
    if unit and unit.get("contract_id"):
        con = next((c for c in contracts if str(c.get("id")) == str(unit.get("contract_id"))), None)
        if con:
            unit["warranty_valid_from"] = con.get("executed_on", "")
            unit["warranty_valid_to"] = con.get("valid_till", "")
    
    kitting_items = []
    if unit and "serial_number" in unit:
        db_items = db.query(KittingItem).filter(
            KittingItem.product_serial_no == unit["serial_number"],
            KittingItem.product_category == "LM"
        ).all()
        kitting_items = [
            {
                "id": item.id,
                "part_number": item.part_number,
                "sap_part_number": item.sap_part_number,
                "material_description": item.material_description,
                "batch_no_po_no": item.batch_no_po_no,
                "material_serial_no": item.material_serial_no,
                "weight_in_grams": item.weight_in_grams,
                "required_quantity": item.required_quantity,
                "uom": item.uom,
                "remarks": item.remarks,
                "subsystems": item.subsystems,
                "route_card_description": item.route_card_description,
            }
            for item in db_items
        ]
        
    context = build_template_context(
        request, 
        unit=unit, 
        customers=customers, 
        contracts=contracts, 
        mode="edit",
        route_cards=LM_ROUTE_CARDS,
        kitting_items=kitting_items
    )
    return templates.TemplateResponse(request, "loitering_munition.html", context)


@router.get("/admin/lm/{unit_id}/disable")
def loitering_munition_disable(request: Request, unit_id: int):
    return redirect_with_flash("/admin/lm", request, "Unit expended.", "success")


@router.get("/admin/gcs")
def ground_control_system_list_page(request: Request, db: Session = Depends(get_db)):
    page = int(request.query_params.get("page", 1))
    all_units = list_or_sample(db, GroundControlSystem, unit_type="GCS", top_level_fields=["unit_name", "serial_number"])
    
    # Load contracts to override warranty dates dynamically
    _, contracts = _load_customers_and_contracts(db)
    import datetime
    today = datetime.date.today()
    for u in all_units:
        c_id = u.get("contract_id")
        c_num = u.get("contract_number")
        con = None
        if c_id:
            con = next((c for c in contracts if str(c.get("id")) == str(c_id)), None)
        if not con and c_num:
            con = next((c for c in contracts if str(c.get("number")) == str(c_num)), None)
        if con:
            u["warranty_valid_from"] = con.get("executed_on", "")
            u["warranty_valid_to"] = con.get("valid_till", "")
            
            vt = con.get("valid_till")
            if vt:
                try:
                    vt_date = datetime.datetime.strptime(vt, "%Y-%m-%d").date()
                    if vt_date < today:
                        u["status"] = "Expired"
                except Exception:
                    pass

    pagination = paginate(all_units, page=page, per_page=50)
    context = build_template_context(request, units=pagination["items"], unit_label="Ground Control Systems (GCS)", pagination=pagination)
    return templates.TemplateResponse(request, "gcs_list.html", context)


@router.get("/admin/gcs/new")
def ground_control_system_new_page(request: Request, db: Session = Depends(get_db)):
    customers, contracts = _load_customers_and_contracts(db)
    context = build_template_context(
        request, 
        customers=customers, 
        contracts=contracts,
        route_cards=GCS_ROUTE_CARDS,
        kitting_items=[]
    )
    return templates.TemplateResponse(request, "ground_control_system.html", context)


@router.get("/admin/gcs/{unit_id}")
def ground_control_system_view_page(request: Request, unit_id: int, db: Session = Depends(get_db)):
    unit = load_entity(db, GroundControlSystem, unit_type="GCS", unit_id=unit_id, top_level_fields=["unit_name", "serial_number"])
    customers, contracts = _load_customers_and_contracts(db)
    if unit and unit.get("contract_id"):
        con = next((c for c in contracts if str(c.get("id")) == str(unit.get("contract_id"))), None)
        if con:
            unit["warranty_valid_from"] = con.get("executed_on", "")
            unit["warranty_valid_to"] = con.get("valid_till", "")
    
    kitting_items = []
    if unit and "serial_number" in unit:
        db_items = db.query(KittingItem).filter(
            KittingItem.product_serial_no == unit["serial_number"],
            KittingItem.product_category == "GCS"
        ).all()
        kitting_items = [
            {
                "id": item.id,
                "part_number": item.part_number,
                "sap_part_number": item.sap_part_number,
                "material_description": item.material_description,
                "batch_no_po_no": item.batch_no_po_no,
                "material_serial_no": item.material_serial_no,
                "weight_in_grams": item.weight_in_grams,
                "required_quantity": item.required_quantity,
                "uom": item.uom,
                "remarks": item.remarks,
                "subsystems": item.subsystems,
                "route_card_description": item.route_card_description,
            }
            for item in db_items
        ]
        
    context = build_template_context(
        request, 
        unit=unit, 
        customers=customers, 
        contracts=contracts, 
        mode="view",
        route_cards=GCS_ROUTE_CARDS,
        kitting_items=kitting_items
    )
    return templates.TemplateResponse(request, "ground_control_system.html", context)


@router.get("/admin/gcs/{unit_id}/edit")
def ground_control_system_edit_page(request: Request, unit_id: int, db: Session = Depends(get_db)):
    unit = load_entity(db, GroundControlSystem, unit_type="GCS", unit_id=unit_id, top_level_fields=["unit_name", "serial_number"])
    customers, contracts = _load_customers_and_contracts(db)
    if unit and unit.get("contract_id"):
        con = next((c for c in contracts if str(c.get("id")) == str(unit.get("contract_id"))), None)
        if con:
            unit["warranty_valid_from"] = con.get("executed_on", "")
            unit["warranty_valid_to"] = con.get("valid_till", "")
    
    kitting_items = []
    if unit and "serial_number" in unit:
        db_items = db.query(KittingItem).filter(
            KittingItem.product_serial_no == unit["serial_number"],
            KittingItem.product_category == "GCS"
        ).all()
        kitting_items = [
            {
                "id": item.id,
                "part_number": item.part_number,
                "sap_part_number": item.sap_part_number,
                "material_description": item.material_description,
                "batch_no_po_no": item.batch_no_po_no,
                "material_serial_no": item.material_serial_no,
                "weight_in_grams": item.weight_in_grams,
                "required_quantity": item.required_quantity,
                "uom": item.uom,
                "remarks": item.remarks,
                "subsystems": item.subsystems,
                "route_card_description": item.route_card_description,
            }
            for item in db_items
        ]
        
    context = build_template_context(
        request, 
        unit=unit, 
        customers=customers, 
        contracts=contracts, 
        mode="edit",
        route_cards=GCS_ROUTE_CARDS,
        kitting_items=kitting_items
    )
    return templates.TemplateResponse(request, "ground_control_system.html", context)


@router.get("/admin/gcs/{unit_id}/disable")
def ground_control_system_disable(request: Request, unit_id: int):
    return redirect_with_flash("/admin/gcs", request, "Unit expended.", "success")


# LM Kitting list, search, and pagination
@router.get("/admin/lm-kitting")
def lm_kitting_list_page(request: Request, db: Session = Depends(get_db)):
    page = int(request.query_params.get("page", 1))
    q = request.query_params.get("q", "").strip()
    
    query = db.query(KittingItem).filter(KittingItem.product_category == "LM")
    if q:
        query = query.filter(
            (KittingItem.part_number.ilike(f"%{q}%")) |
            (KittingItem.sap_part_number.ilike(f"%{q}%")) |
            (KittingItem.material_description.ilike(f"%{q}%")) |
            (KittingItem.product_serial_no.ilike(f"%{q}%")) |
            (KittingItem.route_card_description.ilike(f"%{q}%")) |
            (KittingItem.subsystems.ilike(f"%{q}%"))
        )
    
    all_items = query.order_by(KittingItem.id.desc()).all()
    pagination = paginate(all_items, page=page, per_page=50)
    
    lm_units = db.query(LoiteringMunition).all()
    lm_serials = [u.serial_number for u in lm_units if u.serial_number]
    for s in ["LM-0001", "LM-0002"]:
        if s not in lm_serials:
            lm_serials.append(s)

    context = build_template_context(
        request, 
        items=pagination["items"], 
        category="LM", 
        title="LM Kitting", 
        pagination=pagination, 
        q=q,
        route_cards=LM_ROUTE_CARDS,
        serials=lm_serials
    )
    return templates.TemplateResponse(request, "kitting_table.html", context)


# Add single kitting item manually
@router.post("/admin/lm-kitting")
def create_lm_kitting_item(
    request: Request,
    db: Session = Depends(get_db),
    product_serial_no: str = Form(...),
    route_card_description: str = Form(...),
    part_number: str = Form(""),
    sap_part_number: str = Form(""),
    material_description: str = Form(""),
    batch_no_po_no: str = Form(""),
    material_serial_no: str = Form(""),
    weight_in_grams: str = Form(""),
    required_quantity: str = Form(""),
    uom: str = Form(""),
    remarks: str = Form(""),
    subsystems: str = Form("")
):
    item = KittingItem(
        product_serial_no=product_serial_no,
        product_category="LM",
        route_card_description=route_card_description,
        part_number=part_number,
        sap_part_number=sap_part_number,
        material_description=material_description,
        batch_no_po_no=batch_no_po_no,
        material_serial_no=material_serial_no,
        weight_in_grams=weight_in_grams,
        required_quantity=required_quantity,
        uom=uom,
        remarks=remarks,
        subsystems=subsystems
    )
    db.add(item)
    db.commit()
    return redirect_with_flash("/admin/lm-kitting", request, "Kitting item added successfully.", "success")


# CSV Import
@router.post("/admin/lm-kitting/import")
async def import_lm_kitting(request: Request, file: UploadFile = File(...), db: Session = Depends(get_db)):
    import csv
    try:
        contents = await file.read()
        decoded = contents.decode("utf-8-sig").splitlines()
        reader = csv.reader(decoded)
        
        first_row = next(reader, None)
        if not first_row:
            return redirect_with_flash("/admin/lm-kitting", request, "The uploaded file is empty.", "error")
            
        is_header = any("part" in cell.lower() or "serial" in cell.lower() or "material" in cell.lower() or "route" in cell.lower() for cell in first_row)
        rows_to_process = reader if is_header else [first_row] + list(reader)
        
        count = 0
        for row in rows_to_process:
            if not row or len(row) < 3:
                continue
            
            psn = row[0].strip() if len(row) > 0 else ""
            pcat = row[1].strip() if len(row) > 1 else "LM"
            rcd = row[2].strip() if len(row) > 2 else ""
            pn = row[3].strip() if len(row) > 3 else ""
            spn = row[4].strip() if len(row) > 4 else ""
            md = row[5].strip() if len(row) > 5 else ""
            bn = row[6].strip() if len(row) > 6 else ""
            msn = row[7].strip() if len(row) > 7 else ""
            wg = row[8].strip() if len(row) > 8 else ""
            rq = row[9].strip() if len(row) > 9 else ""
            uom = row[10].strip() if len(row) > 10 else ""
            rem = row[11].strip() if len(row) > 11 else ""
            subs = row[12].strip() if len(row) > 12 else ""
            
            if not psn or not rcd:
                continue
                
            item = KittingItem(
                product_serial_no=psn,
                product_category="LM",
                route_card_description=rcd,
                part_number=pn,
                sap_part_number=spn,
                material_description=md,
                batch_no_po_no=bn,
                material_serial_no=msn,
                weight_in_grams=wg,
                required_quantity=rq,
                uom=uom,
                remarks=rem,
                subsystems=subs
            )
            db.add(item)
            count += 1
            
        db.commit()
        return redirect_with_flash("/admin/lm-kitting", request, f"Successfully imported {count} items.", "success")
    except Exception as e:
        return redirect_with_flash("/admin/lm-kitting", request, f"Failed to import CSV: {str(e)}", "error")


# Delete kitting item
@router.post("/admin/lm-kitting/{id}/delete")
def delete_lm_kitting_item(request: Request, id: int, db: Session = Depends(get_db)):
    item = db.query(KittingItem).filter(KittingItem.id == id, KittingItem.product_category == "LM").first()
    if item:
        db.delete(item)
        db.commit()
        return redirect_with_flash("/admin/lm-kitting", request, "Kitting item deleted.", "success")
    return redirect_with_flash("/admin/lm-kitting", request, "Kitting item not found.", "error")


# View and Edit Kitting Item
@router.get("/admin/lm-kitting/{id}")
def lm_kitting_detail_page(request: Request, id: int, db: Session = Depends(get_db)):
    item = db.query(KittingItem).filter(KittingItem.id == id, KittingItem.product_category == "LM").first()
    if not item:
        return redirect_with_flash("/admin/lm-kitting", request, "Kitting item not found.", "error")
    context = build_template_context(
        request,
        item=item,
        category="LM",
        route_cards=LM_ROUTE_CARDS,
        mode="edit",
        title="LM Kitting Item"
    )
    return templates.TemplateResponse(request, "kitting_config.html", context)


@router.post("/admin/lm-kitting/{id}")
async def update_lm_kitting_item(request: Request, id: int, db: Session = Depends(get_db)):
    item = db.query(KittingItem).filter(KittingItem.id == id, KittingItem.product_category == "LM").first()
    if not item:
        return redirect_with_flash("/admin/lm-kitting", request, "Kitting item not found.", "error")
    
    form = await request.form()
    data = parse_form_data(form)
    
    # CRITICAL: Validate required fields to prevent record loss
    product_serial_no = data.get("product_serial_no", "").strip()
    if not product_serial_no:
        product_serial_no = item.product_serial_no  # Keep existing value
    
    product_category = data.get("product_category", "").strip()
    if not product_category:
        product_category = item.product_category  # Keep existing value
    
    # Prepare update dict with proper null/empty handling
    updates = {
        "product_serial_no": product_serial_no,
        "product_category": product_category,
        "route_card_description": data.get("route_card_description") or item.route_card_description,
        "part_number": data.get("part_number") or item.part_number,
        "sap_part_number": data.get("sap_part_number") or item.sap_part_number,
        "material_description": data.get("material_description") or item.material_description,
        "batch_no_po_no": data.get("batch_no_po_no") or item.batch_no_po_no,
        "material_serial_no": data.get("material_serial_no") or item.material_serial_no,
        "weight_in_grams": data.get("weight_in_grams") or item.weight_in_grams,
        "required_quantity": data.get("required_quantity") or item.required_quantity,
        "uom": data.get("uom") or item.uom,
        "remarks": data.get("remarks") or item.remarks,
        "subsystems": data.get("subsystems") or item.subsystems,
    }
    
    # Audit log change tracking - capture ALL changes with timestamp and user
    change_log = (item.data or {}).get("change_log", []) if item.data else []
    fields_to_track = list(updates.keys())
    
    import datetime
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    for field in fields_to_track:
        old_val = getattr(item, field, "")
        new_val = updates.get(field, "")
        if str(old_val).strip() != str(new_val).strip():
            change_log.append({
                "timestamp": timestamp,
                "user": "admin",
                "field": field.replace("_", " ").title(),
                "old_value": str(old_val),
                "new_value": str(new_val)
            })
            
    # Apply all updates together
    for field, value in updates.items():
        setattr(item, field, value)
    
    item.data = {"change_log": change_log}
    db.commit()
    db.refresh(item)
    
    # Flash message includes count of changes
    change_count = len([c for c in change_log if c.get("timestamp") == timestamp])
    message = f"Kitting item updated ({change_count} field{'s' if change_count != 1 else ''} changed)."
    return redirect_with_flash("/admin/lm-kitting", request, message, "success")


# GCS Kitting list, search, and pagination
@router.get("/admin/gcs-kitting")
def gcs_kitting_list_page(request: Request, db: Session = Depends(get_db)):
    page = int(request.query_params.get("page", 1))
    q = request.query_params.get("q", "").strip()
    
    query = db.query(KittingItem).filter(KittingItem.product_category == "GCS")
    if q:
        query = query.filter(
            (KittingItem.part_number.ilike(f"%{q}%")) |
            (KittingItem.sap_part_number.ilike(f"%{q}%")) |
            (KittingItem.material_description.ilike(f"%{q}%")) |
            (KittingItem.product_serial_no.ilike(f"%{q}%")) |
            (KittingItem.route_card_description.ilike(f"%{q}%")) |
            (KittingItem.subsystems.ilike(f"%{q}%"))
        )
    
    all_items = query.order_by(KittingItem.id.desc()).all()
    pagination = paginate(all_items, page=page, per_page=50)
    
    gcs_units = db.query(GroundControlSystem).all()
    gcs_serials = [u.serial_number for u in gcs_units if u.serial_number]
    for s in ["GCS-0101"]:
        if s not in gcs_serials:
            gcs_serials.append(s)

    context = build_template_context(
        request, 
        items=pagination["items"], 
        category="GCS", 
        title="GCS Kitting", 
        pagination=pagination, 
        q=q,
        route_cards=GCS_ROUTE_CARDS,
        serials=gcs_serials
    )
    return templates.TemplateResponse(request, "kitting_table.html", context)


# Add single kitting item manually
@router.post("/admin/gcs-kitting")
def create_gcs_kitting_item(
    request: Request,
    db: Session = Depends(get_db),
    product_serial_no: str = Form(...),
    route_card_description: str = Form(...),
    part_number: str = Form(""),
    sap_part_number: str = Form(""),
    material_description: str = Form(""),
    batch_no_po_no: str = Form(""),
    material_serial_no: str = Form(""),
    weight_in_grams: str = Form(""),
    required_quantity: str = Form(""),
    uom: str = Form(""),
    remarks: str = Form(""),
    subsystems: str = Form("")
):
    item = KittingItem(
        product_serial_no=product_serial_no,
        product_category="GCS",
        route_card_description=route_card_description,
        part_number=part_number,
        sap_part_number=sap_part_number,
        material_description=material_description,
        batch_no_po_no=batch_no_po_no,
        material_serial_no=material_serial_no,
        weight_in_grams=weight_in_grams,
        required_quantity=required_quantity,
        uom=uom,
        remarks=remarks,
        subsystems=subsystems
    )
    db.add(item)
    db.commit()
    return redirect_with_flash("/admin/gcs-kitting", request, "Kitting item added successfully.", "success")


# CSV Import
@router.post("/admin/gcs-kitting/import")
async def import_gcs_kitting(request: Request, file: UploadFile = File(...), db: Session = Depends(get_db)):
    import csv
    try:
        contents = await file.read()
        decoded = contents.decode("utf-8-sig").splitlines()
        reader = csv.reader(decoded)
        
        first_row = next(reader, None)
        if not first_row:
            return redirect_with_flash("/admin/gcs-kitting", request, "The uploaded file is empty.", "error")
            
        is_header = any("part" in cell.lower() or "serial" in cell.lower() or "material" in cell.lower() or "route" in cell.lower() for cell in first_row)
        rows_to_process = reader if is_header else [first_row] + list(reader)
        
        count = 0
        for row in rows_to_process:
            if not row or len(row) < 3:
                continue
            
            psn = row[0].strip() if len(row) > 0 else ""
            pcat = row[1].strip() if len(row) > 1 else "GCS"
            rcd = row[2].strip() if len(row) > 2 else ""
            pn = row[3].strip() if len(row) > 3 else ""
            spn = row[4].strip() if len(row) > 4 else ""
            md = row[5].strip() if len(row) > 5 else ""
            bn = row[6].strip() if len(row) > 6 else ""
            msn = row[7].strip() if len(row) > 7 else ""
            wg = row[8].strip() if len(row) > 8 else ""
            rq = row[9].strip() if len(row) > 9 else ""
            uom = row[10].strip() if len(row) > 10 else ""
            rem = row[11].strip() if len(row) > 11 else ""
            subs = row[12].strip() if len(row) > 12 else ""
            
            if not psn or not rcd:
                continue
                
            item = KittingItem(
                product_serial_no=psn,
                product_category="GCS",
                route_card_description=rcd,
                part_number=pn,
                sap_part_number=spn,
                material_description=md,
                batch_no_po_no=bn,
                material_serial_no=msn,
                weight_in_grams=wg,
                required_quantity=rq,
                uom=uom,
                remarks=rem,
                subsystems=subs
            )
            db.add(item)
            count += 1
            
        db.commit()
        return redirect_with_flash("/admin/gcs-kitting", request, f"Successfully imported {count} items.", "success")
    except Exception as e:
        return redirect_with_flash("/admin/gcs-kitting", request, f"Failed to import CSV: {str(e)}", "error")


# Delete kitting item
@router.post("/admin/gcs-kitting/{id}/delete")
def delete_gcs_kitting_item(request: Request, id: int, db: Session = Depends(get_db)):
    item = db.query(KittingItem).filter(KittingItem.id == id, KittingItem.product_category == "GCS").first()
    if item:
        db.delete(item)
        db.commit()
        return redirect_with_flash("/admin/gcs-kitting", request, "Kitting item deleted.", "success")
    return redirect_with_flash("/admin/gcs-kitting", request, "Kitting item not found.", "error")


# View and Edit GCS Kitting Item
@router.get("/admin/gcs-kitting/{id}")
def gcs_kitting_detail_page(request: Request, id: int, db: Session = Depends(get_db)):
    item = db.query(KittingItem).filter(KittingItem.id == id, KittingItem.product_category == "GCS").first()
    if not item:
        return redirect_with_flash("/admin/gcs-kitting", request, "Kitting item not found.", "error")
    context = build_template_context(
        request,
        item=item,
        category="GCS",
        route_cards=GCS_ROUTE_CARDS,
        mode="edit",
        title="GCS Kitting Item"
    )
    return templates.TemplateResponse(request, "kitting_config.html", context)


@router.post("/admin/gcs-kitting/{id}")
async def update_gcs_kitting_item(request: Request, id: int, db: Session = Depends(get_db)):
    item = db.query(KittingItem).filter(KittingItem.id == id, KittingItem.product_category == "GCS").first()
    if not item:
        return redirect_with_flash("/admin/gcs-kitting", request, "Kitting item not found.", "error")
    
    form = await request.form()
    data = parse_form_data(form)
    
    # CRITICAL: Validate required fields to prevent record loss
    product_serial_no = data.get("product_serial_no", "").strip()
    if not product_serial_no:
        product_serial_no = item.product_serial_no  # Keep existing value
    
    product_category = data.get("product_category", "").strip()
    if not product_category:
        product_category = item.product_category  # Keep existing value
    
    # Prepare update dict with proper null/empty handling
    updates = {
        "product_serial_no": product_serial_no,
        "product_category": product_category,
        "route_card_description": data.get("route_card_description") or item.route_card_description,
        "part_number": data.get("part_number") or item.part_number,
        "sap_part_number": data.get("sap_part_number") or item.sap_part_number,
        "material_description": data.get("material_description") or item.material_description,
        "batch_no_po_no": data.get("batch_no_po_no") or item.batch_no_po_no,
        "material_serial_no": data.get("material_serial_no") or item.material_serial_no,
        "weight_in_grams": data.get("weight_in_grams") or item.weight_in_grams,
        "required_quantity": data.get("required_quantity") or item.required_quantity,
        "uom": data.get("uom") or item.uom,
        "remarks": data.get("remarks") or item.remarks,
        "subsystems": data.get("subsystems") or item.subsystems,
    }
    
    # Audit log change tracking - capture ALL changes with timestamp and user
    change_log = (item.data or {}).get("change_log", []) if item.data else []
    fields_to_track = list(updates.keys())
    
    import datetime
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    for field in fields_to_track:
        old_val = getattr(item, field, "")
        new_val = updates.get(field, "")
        if str(old_val).strip() != str(new_val).strip():
            change_log.append({
                "timestamp": timestamp,
                "user": "admin",
                "field": field.replace("_", " ").title(),
                "old_value": str(old_val),
                "new_value": str(new_val)
            })
            
    # Apply all updates together
    for field, value in updates.items():
        setattr(item, field, value)
    
    item.data = {"change_log": change_log}
    db.commit()
    db.refresh(item)
    
    # Flash message includes count of changes
    change_count = len([c for c in change_log if c.get("timestamp") == timestamp])
    message = f"Kitting item updated ({change_count} field{'s' if change_count != 1 else ''} changed)."
    return redirect_with_flash("/admin/gcs-kitting", request, message, "success")


@router.get("/admin/tmv")
def tactical_mobility_vehicle_list_page(request: Request, db: Session = Depends(get_db)):
    page = int(request.query_params.get("page", 1))
    all_units = list_or_sample(db, TacticalMobilityVehicle, unit_type="TMV", top_level_fields=["unit_name", "serial_number"])
    pagination = paginate(all_units, page=page, per_page=50)
    context = build_template_context(request, units=pagination["items"], unit_label="Tactical Mobility Vehicle (TMV)", pagination=pagination)
    return templates.TemplateResponse(request, "tmv_list.html", context)


@router.get("/admin/tmv/new")
def tactical_mobility_vehicle_new_page(request: Request):
    customers = _get_sample_customers()
    contracts = _get_sample_contracts()
    context = build_template_context(request, customers=customers, contracts=contracts)
    return templates.TemplateResponse(request, "tactical_mobility_vehicle.html", context)


@router.get("/admin/tmv/{unit_id}")
def tactical_mobility_vehicle_view_page(request: Request, unit_id: int, db: Session = Depends(get_db)):
    unit = load_entity(db, TacticalMobilityVehicle, unit_type="TMV", unit_id=unit_id, top_level_fields=["unit_name", "serial_number"])
    customers = _get_sample_customers()
    contracts = _get_sample_contracts()
    context = build_template_context(request, unit=unit, customers=customers, contracts=contracts, mode="view")
    return templates.TemplateResponse(request, "tactical_mobility_vehicle.html", context)


@router.get("/admin/tmv/{unit_id}/edit")
def tactical_mobility_vehicle_edit_page(request: Request, unit_id: int, db: Session = Depends(get_db)):
    unit = load_entity(db, TacticalMobilityVehicle, unit_type="TMV", unit_id=unit_id, top_level_fields=["unit_name", "serial_number"])
    customers = _get_sample_customers()
    contracts = _get_sample_contracts()
    context = build_template_context(request, unit=unit, customers=customers, contracts=contracts, mode="edit")
    return templates.TemplateResponse(request, "tactical_mobility_vehicle.html", context)


@router.get("/admin/tmv/{unit_id}/disable")
def tactical_mobility_vehicle_disable(request: Request, unit_id: int):
    return redirect_with_flash("/admin/tmv", request, "Unit expended.", "success")


@router.get("/admin/simulator")
def simulator_list_page(request: Request, db: Session = Depends(get_db)):
    page = int(request.query_params.get("page", 1))
    all_units = list_or_sample(db, SimulatorUnit, unit_type="SIM", top_level_fields=["unit_name", "serial_number"])
    pagination = paginate(all_units, page=page, per_page=50)
    context = build_template_context(request, units=pagination["items"], unit_label="Simulator", pagination=pagination)
    return templates.TemplateResponse(request, "simulator_list.html", context)


@router.get("/admin/simulator/new")
def simulator_new_page(request: Request):
    customers = _get_sample_customers()
    contracts = _get_sample_contracts()
    context = build_template_context(request, customers=customers, contracts=contracts)
    return templates.TemplateResponse(request, "simulator.html", context)


@router.get("/admin/simulator/{unit_id}")
def simulator_view_page(request: Request, unit_id: int, db: Session = Depends(get_db)):
    unit = load_entity(db, SimulatorUnit, unit_type="SIM", unit_id=unit_id, top_level_fields=["unit_name", "serial_number"])
    customers = _get_sample_customers()
    contracts = _get_sample_contracts()
    context = build_template_context(request, unit=unit, customers=customers, contracts=contracts, mode="view")
    return templates.TemplateResponse(request, "simulator.html", context)


@router.get("/admin/simulator/{unit_id}/edit")
def simulator_edit_page(request: Request, unit_id: int, db: Session = Depends(get_db)):
    unit = load_entity(db, SimulatorUnit, unit_type="SIM", unit_id=unit_id, top_level_fields=["unit_name", "serial_number"])
    customers = _get_sample_customers()
    contracts = _get_sample_contracts()
    context = build_template_context(request, unit=unit, customers=customers, contracts=contracts, mode="edit")
    return templates.TemplateResponse(request, "simulator.html", context)


@router.get("/admin/simulator/{unit_id}/disable")
def simulator_disable(request: Request, unit_id: int):
    return redirect_with_flash("/admin/simulator", request, "Unit expended.", "success")


@router.get("/admin/rdv")
def rdv_list_page(request: Request, db: Session = Depends(get_db)):
    page = int(request.query_params.get("page", 1))
    all_units = list_or_sample(db, RapidDeploymentVehicle, unit_type="RDV", top_level_fields=["unit_name", "serial_number"])
    pagination = paginate(all_units, page=page, per_page=50)
    context = build_template_context(request, units=pagination["items"], unit_label="Rapid Deployment Vehicle (RDV)", pagination=pagination)
    return templates.TemplateResponse(request, "rdv_list.html", context)


@router.get("/admin/rdv/new")
def rdv_new_page(request: Request):
    customers = _get_sample_customers()
    contracts = _get_sample_contracts()
    context = build_template_context(request, customers=customers, contracts=contracts)
    return templates.TemplateResponse(request, "rapid_deployment_vehicle.html", context)


@router.get("/admin/rdv/{unit_id}")
def rdv_view_page(request: Request, unit_id: int, db: Session = Depends(get_db)):
    unit = load_entity(db, RapidDeploymentVehicle, unit_type="RDV", unit_id=unit_id, top_level_fields=["unit_name", "serial_number"])
    customers = _get_sample_customers()
    contracts = _get_sample_contracts()
    context = build_template_context(request, unit=unit, customers=customers, contracts=contracts, mode="view")
    return templates.TemplateResponse(request, "rapid_deployment_vehicle.html", context)


@router.get("/admin/rdv/{unit_id}/edit")
def rdv_edit_page(request: Request, unit_id: int, db: Session = Depends(get_db)):
    unit = load_entity(db, RapidDeploymentVehicle, unit_type="RDV", unit_id=unit_id, top_level_fields=["unit_name", "serial_number"])
    customers = _get_sample_customers()
    contracts = _get_sample_contracts()
    context = build_template_context(request, unit=unit, customers=customers, contracts=contracts, mode="edit")
    return templates.TemplateResponse(request, "rapid_deployment_vehicle.html", context)


@router.get("/admin/rdv/{unit_id}/disable")
def rdv_disable(request: Request, unit_id: int):
    return redirect_with_flash("/admin/rdv", request, "Unit expended.", "success")


@router.get("/admin/batteries/types")
def manage_battery_types(request: Request):
    context = build_template_context(request, battery_types=BATTERY_TYPES)
    return templates.TemplateResponse(request, "battery_types.html", context)


@router.post("/admin/batteries/types")
def add_battery_type(request: Request, new_type: str = Form(...)):
    new_type_stripped = new_type.strip()
    if new_type_stripped and new_type_stripped not in BATTERY_TYPES:
        BATTERY_TYPES.append(new_type_stripped)
        return redirect_with_flash("/admin/batteries/types", request, "Battery type added.", "success")
    return redirect_with_flash("/admin/batteries/types", request, "Invalid or duplicate battery type.", "error")


@router.get("/admin/batteries/types/{type_idx}/delete")
def delete_battery_type(request: Request, type_idx: int):
    if 0 <= type_idx < len(BATTERY_TYPES):
        removed = BATTERY_TYPES.pop(type_idx)
        return redirect_with_flash("/admin/batteries/types", request, f"Battery type '{removed}' removed.", "success")
    return redirect_with_flash("/admin/batteries/types", request, "Battery type not found.", "error")


@router.get("/admin/batteries")
def batteries_list_page(request: Request, db: Session = Depends(get_db)):
    page = int(request.query_params.get("page", 1))
    all_units = list_or_sample(db, Battery, unit_type="BATTERY", top_level_fields=["unit_name", "serial_number"])
    pagination = paginate(all_units, page=page, per_page=50)
    context = build_template_context(request, units=pagination["items"], unit_label="Batteries", pagination=pagination)
    return templates.TemplateResponse(request, "batteries_list.html", context)


@router.get("/admin/batteries/new")
def batteries_new_page(request: Request):
    customers = _get_sample_customers()
    contracts = _get_sample_contracts()
    context = build_template_context(request, customers=customers, contracts=contracts, battery_types=BATTERY_TYPES)
    return templates.TemplateResponse(request, "battery_config.html", context)


@router.get("/admin/batteries/{unit_id}")
def batteries_view_page(request: Request, unit_id: int, db: Session = Depends(get_db)):
    unit = load_entity(db, Battery, unit_type="BATTERY", unit_id=unit_id, top_level_fields=["unit_name", "serial_number"])
    customers = _get_sample_customers()
    contracts = _get_sample_contracts()
    context = build_template_context(request, unit=unit, customers=customers, contracts=contracts, battery_types=BATTERY_TYPES, mode="view")
    return templates.TemplateResponse(request, "battery_config.html", context)


@router.get("/admin/batteries/{unit_id}/edit")
def batteries_edit_page(request: Request, unit_id: int, db: Session = Depends(get_db)):
    unit = load_entity(db, Battery, unit_type="BATTERY", unit_id=unit_id, top_level_fields=["unit_name", "serial_number"])
    customers = _get_sample_customers()
    contracts = _get_sample_contracts()
    context = build_template_context(request, unit=unit, customers=customers, contracts=contracts, battery_types=BATTERY_TYPES, mode="edit")
    return templates.TemplateResponse(request, "battery_config.html", context)


@router.get("/admin/batteries/{unit_id}/disable")
def batteries_disable(request: Request, unit_id: int):
    return redirect_with_flash("/admin/batteries", request, "Unit expended.", "success")


@router.get("/admin/warhead")
def warhead_list_page(request: Request, db: Session = Depends(get_db)):
    page = int(request.query_params.get("page", 1))
    all_units = list_or_sample(db, Warhead, unit_type="WARHEAD", top_level_fields=["unit_name"])
    pagination = paginate(all_units, page=page, per_page=50)
    context = build_template_context(request, units=pagination["items"], unit_label="War Head", pagination=pagination)
    return templates.TemplateResponse(request, "warhead_list.html", context)


@router.get("/admin/warhead/new")
def warhead_new_page(request: Request):
    customers = _get_sample_customers()
    contracts = _get_sample_contracts()
    context = build_template_context(request, customers=customers, contracts=contracts)
    return templates.TemplateResponse(request, "warhead_config.html", context)


@router.get("/admin/warhead/{unit_id}")
def warhead_view_page(request: Request, unit_id: int, db: Session = Depends(get_db)):
    unit = load_entity(db, Warhead, unit_type="WARHEAD", unit_id=unit_id, top_level_fields=["unit_name"])
    customers = _get_sample_customers()
    contracts = _get_sample_contracts()
    context = build_template_context(request, unit=unit, customers=customers, contracts=contracts, mode="view")
    return templates.TemplateResponse(request, "warhead_config.html", context)


@router.get("/admin/warhead/{unit_id}/edit")
def warhead_edit_page(request: Request, unit_id: int, db: Session = Depends(get_db)):
    unit = load_entity(db, Warhead, unit_type="WARHEAD", unit_id=unit_id, top_level_fields=["unit_name"])
    customers = _get_sample_customers()
    contracts = _get_sample_contracts()
    context = build_template_context(request, unit=unit, customers=customers, contracts=contracts, mode="edit")
    return templates.TemplateResponse(request, "warhead_config.html", context)


@router.get("/admin/warhead/{unit_id}/disable")
def warhead_disable(request: Request, unit_id: int):
    return redirect_with_flash("/admin/warhead", request, "Unit expended.", "success")


@router.get("/admin/mrls")
def mrls_list_page(request: Request, db: Session = Depends(get_db)):
    page = int(request.query_params.get("page", 1))
    all_units = list_or_sample(db, MRLS, unit_type="MRLS", top_level_fields=["unit_name"])
    pagination = paginate(all_units, page=page, per_page=50)
    context = build_template_context(request, units=pagination["items"], unit_label="MRLS", pagination=pagination)
    return templates.TemplateResponse(request, "mrls_list.html", context)


@router.get("/admin/mrls/new")
def mrls_new_page(request: Request):
    customers = _get_sample_customers()
    contracts = _get_sample_contracts()
    platform_variants = _get_sample_platform_variants()
    context = build_template_context(request, customers=customers, contracts=contracts, platform_variants=platform_variants)
    return templates.TemplateResponse(request, "mrls_config.html", context)


@router.get("/admin/mrls/{unit_id}")
def mrls_view_page(request: Request, unit_id: int, db: Session = Depends(get_db)):
    unit = load_entity(db, MRLS, unit_type="MRLS", unit_id=unit_id, top_level_fields=["unit_name"])
    customers = _get_sample_customers()
    contracts = _get_sample_contracts()
    platform_variants = _get_sample_platform_variants()
    context = build_template_context(request, unit=unit, customers=customers, contracts=contracts, platform_variants=platform_variants, mode="view")
    return templates.TemplateResponse(request, "mrls_config.html", context)


@router.get("/admin/mrls/{unit_id}/edit")
def mrls_edit_page(request: Request, unit_id: int, db: Session = Depends(get_db)):
    unit = load_entity(db, MRLS, unit_type="MRLS", unit_id=unit_id, top_level_fields=["unit_name"])
    customers = _get_sample_customers()
    contracts = _get_sample_contracts()
    platform_variants = _get_sample_platform_variants()
    context = build_template_context(request, unit=unit, customers=customers, contracts=contracts, platform_variants=platform_variants, mode="edit")
    return templates.TemplateResponse(request, "mrls_config.html", context)


@router.get("/admin/mrls/{unit_id}/disable")
def mrls_disable(request: Request, unit_id: int):
    return redirect_with_flash("/admin/mrls", request, "Unit expended.", "success")


@router.get("/admin/smt-ste")
def smt_ste_list_page(request: Request, db: Session = Depends(get_db)):
    page = int(request.query_params.get("page", 1))
    all_units = list_or_sample(db, SMTSTE, unit_type="SMT_STE", top_level_fields=["unit_name"])
    pagination = paginate(all_units, page=page, per_page=50)
    context = build_template_context(request, units=pagination["items"], unit_label="Field Assembly Tools/ SMT/ STE", pagination=pagination)
    return templates.TemplateResponse(request, "smt_ste_list.html", context)


@router.get("/admin/smt-ste/new")
def smt_ste_new_page(request: Request):
    customers = _get_sample_customers()
    contracts = _get_sample_contracts()
    platform_variants = _get_sample_platform_variants()
    context = build_template_context(request, customers=customers, contracts=contracts, platform_variants=platform_variants)
    return templates.TemplateResponse(request, "smt_ste_config.html", context)


@router.get("/admin/smt-ste/{unit_id}")
def smt_ste_view_page(request: Request, unit_id: int, db: Session = Depends(get_db)):
    unit = load_entity(db, SMTSTE, unit_type="SMT_STE", unit_id=unit_id, top_level_fields=["unit_name"])
    customers = _get_sample_customers()
    contracts = _get_sample_contracts()
    platform_variants = _get_sample_platform_variants()
    context = build_template_context(request, unit=unit, customers=customers, contracts=contracts, platform_variants=platform_variants, mode="view")
    return templates.TemplateResponse(request, "smt_ste_config.html", context)


@router.get("/admin/smt-ste/{unit_id}/edit")
def smt_ste_edit_page(request: Request, unit_id: int, db: Session = Depends(get_db)):
    unit = load_entity(db, SMTSTE, unit_type="SMT_STE", unit_id=unit_id, top_level_fields=["unit_name"])
    customers = _get_sample_customers()
    contracts = _get_sample_contracts()
    platform_variants = _get_sample_platform_variants()
    context = build_template_context(request, unit=unit, customers=customers, contracts=contracts, platform_variants=platform_variants, mode="edit")
    return templates.TemplateResponse(request, "smt_ste_config.html", context)


@router.get("/admin/smt-ste/{unit_id}/disable")
def smt_ste_disable(request: Request, unit_id: int):
    return redirect_with_flash("/admin/smt-ste", request, "Unit expended.", "success")


@router.get("/admin/sam")
def sam_list_page(request: Request, db: Session = Depends(get_db)):
    page = int(request.query_params.get("page", 1))
    all_units = list_or_sample(db, SAM, unit_type="SAM", top_level_fields=["unit_name"])
    pagination = paginate(all_units, page=page, per_page=50)
    context = build_template_context(request, units=pagination["items"], unit_label="SAM", pagination=pagination)
    return templates.TemplateResponse(request, "sam_list.html", context)


@router.get("/admin/sam/new")
def sam_new_page(request: Request):
    customers = _get_sample_customers()
    contracts = _get_sample_contracts()
    context = build_template_context(request, customers=customers, contracts=contracts)
    return templates.TemplateResponse(request, "sam_config.html", context)


@router.get("/admin/sam/{unit_id}")
def sam_view_page(request: Request, unit_id: int, db: Session = Depends(get_db)):
    unit = load_entity(db, SAM, unit_type="SAM", unit_id=unit_id, top_level_fields=["unit_name"])
    customers = _get_sample_customers()
    contracts = _get_sample_contracts()
    context = build_template_context(request, unit=unit, customers=customers, contracts=contracts, mode="view")
    return templates.TemplateResponse(request, "sam_config.html", context)


@router.get("/admin/sam/{unit_id}/edit")
def sam_edit_page(request: Request, unit_id: int, db: Session = Depends(get_db)):
    unit = load_entity(db, SAM, unit_type="SAM", unit_id=unit_id, top_level_fields=["unit_name"])
    customers = _get_sample_customers()
    contracts = _get_sample_contracts()
    context = build_template_context(request, unit=unit, customers=customers, contracts=contracts, mode="edit")
    return templates.TemplateResponse(request, "sam_config.html", context)


@router.get("/admin/sam/{unit_id}/disable")
def sam_disable(request: Request, unit_id: int):
    return redirect_with_flash("/admin/sam", request, "Unit expended.", "success")


@router.get("/admin/lru")
def lru_list_page(request: Request, db: Session = Depends(get_db)):
    page = int(request.query_params.get("page", 1))
    all_lrus = list_or_sample(db, LineReplaceableUnit, unit_type="LRU", top_level_fields=["unit_name"])
    pagination = paginate(all_lrus, page=page, per_page=50)
    context = build_template_context(request, lrus=pagination["items"], pagination=pagination)
    return templates.TemplateResponse(request, "lru_list.html", context)


@router.get("/admin/lru/new")
def lru_new_page(request: Request):
    platform_variants = _get_sample_platform_variants()
    context = build_template_context(request, platform_variants=platform_variants)
    return templates.TemplateResponse(request, "lru_config.html", context)


@router.get("/admin/lru/{lru_id}")
def lru_view_page(request: Request, lru_id: int, db: Session = Depends(get_db)):
    lru = load_entity(db, LineReplaceableUnit, unit_type="LRU", unit_id=lru_id, top_level_fields=["unit_name"])
    platform_variants = _get_sample_platform_variants()
    context = build_template_context(request, lru=lru, platform_variants=platform_variants, mode="view")
    return templates.TemplateResponse(request, "lru_config.html", context)


@router.get("/admin/lru/{lru_id}/edit")
def lru_edit_page(request: Request, lru_id: int, db: Session = Depends(get_db)):
    lru = load_entity(db, LineReplaceableUnit, unit_type="LRU", unit_id=lru_id, top_level_fields=["unit_name"])
    platform_variants = _get_sample_platform_variants()
    context = build_template_context(request, lru=lru, platform_variants=platform_variants, mode="edit")
    return templates.TemplateResponse(request, "lru_config.html", context)


@router.get("/admin/lru/{lru_id}/disable")
def lru_disable(request: Request, lru_id: int):
    return redirect_with_flash("/admin/lru", request, "LRU expended.", "success")


@router.get("/admin/sub-systems")
def sub_systems_list_page(request: Request, db: Session = Depends(get_db)):
    page = int(request.query_params.get("page", 1))
    all_sub_systems = list_or_sample(db, SubSystem, unit_type="SUB_SYSTEM", top_level_fields=["name"])
    pagination = paginate(all_sub_systems, page=page, per_page=50)
    context = build_template_context(request, sub_systems=pagination["items"], pagination=pagination)
    return templates.TemplateResponse(request, "sub_systems_list.html", context)


@router.get("/admin/sub-systems/new")
def sub_systems_new_page(request: Request):
    platform_variants = _get_sample_platform_variants()
    context = build_template_context(request, platform_variants=platform_variants)
    return templates.TemplateResponse(request, "sub_systems_config.html", context)


@router.get("/admin/sub-systems/{sub_system_id}")
def sub_systems_view_page(request: Request, sub_system_id: int, db: Session = Depends(get_db)):
    sub_system = load_entity(db, SubSystem, unit_type="SUB_SYSTEM", unit_id=sub_system_id, top_level_fields=["name"])
    platform_variants = _get_sample_platform_variants()
    context = build_template_context(
        request,
        sub_system=sub_system,
        platform_variants=platform_variants,
        mode="view",
    )
    return templates.TemplateResponse(request, "sub_systems_config.html", context)


@router.get("/admin/sub-systems/{sub_system_id}/edit")
def sub_systems_edit_page(request: Request, sub_system_id: int, db: Session = Depends(get_db)):
    sub_system = load_entity(db, SubSystem, unit_type="SUB_SYSTEM", unit_id=sub_system_id, top_level_fields=["name"])
    platform_variants = _get_sample_platform_variants()
    context = build_template_context(
        request,
        sub_system=sub_system,
        platform_variants=platform_variants,
        mode="edit",
    )
    return templates.TemplateResponse(request, "sub_systems_config.html", context)


@router.get("/admin/sub-systems/{sub_system_id}/disable")
def sub_systems_disable(request: Request, sub_system_id: int):
    return redirect_with_flash("/admin/sub-systems", request, "Sub-system expended.", "success")


def _get_sample_roles():
    return [
        {
            "id": 1,
            "name": "Administrator",
            "description": "Full system access with complete administrative privileges",
            "permissions": ["read_all", "create_all", "edit_all", "delete_all", "manage_users", "manage_roles"],
        },
        {
            "id": 2,
            "name": "Manager",
            "description": "Project and team management with report generation",
            "permissions": ["read_all", "create_incidents", "edit_own", "manage_team", "generate_reports"],
        },
        {
            "id": 3,
            "name": "Advisor",
            "description": "Technical advisor with knowledge base and recommendation access",
            "permissions": ["read_all", "create_knowledge", "edit_own", "add_recommendations"],
        },
        {
            "id": 4,
            "name": "Field Agent",
            "description": "Field operations and incident reporting",
            "permissions": ["read_incidents", "create_incidents", "edit_own", "submit_reports"],
        },
        {
            "id": 5,
            "name": "Tech Engineer",
            "description": "Technical implementation and system troubleshooting",
            "permissions": ["read_all", "create_incidents", "edit_own", "technical_diagnostics"],
        },
    ]


def _get_sample_managers():
    """Get all users with Manager role for group assignment"""
    return [
        {
            "id": 2,
            "username": "mgr_priya",
            "full_name": "Priya Sharma",
            "email": "priya.sharma@vajra.local",
            "department": "Project Management",
        },
        {
            "id": 3,
            "username": "mgr_vikram",
            "full_name": "Vikram Singh",
            "email": "vikram.singh@vajra.local",
            "department": "Operations",
        },
        {
            "id": 4,
            "username": "mgr_anjali",
            "full_name": "Anjali Verma",
            "email": "anjali.verma@vajra.local",
            "department": "Quality Assurance",
        },
        {
            "id": 5,
            "username": "mgr_aditya",
            "full_name": "Aditya Kumar",
            "email": "aditya.kumar@vajra.local",
            "department": "Field Operations",
        },
        {
            "id": 6,
            "username": "mgr_neha",
            "full_name": "Neha Gupta",
            "email": "neha.gupta@vajra.local",
            "department": "Customer Support",
        },
    ]


def _get_sample_licenses():
    return [
        {
            "id": 1,
            "name": "Standard License",
            "description": "Basic access for individual users with essential features",
            "max_users": 100,
            "features": ["incident_management", "knowledge_base", "basic_reporting"],
        },
        {
            "id": 2,
            "name": "Premium License",
            "description": "Extended features for teams with advanced analytics",
            "max_users": 500,
            "features": ["incident_management", "knowledge_base", "advanced_reporting", "team_management", "custom_workflows"],
        },
        {
            "id": 3,
            "name": "Enterprise License",
            "description": "Complete platform access with dedicated support",
            "max_users": 5000,
            "features": ["all_features", "api_access", "custom_integrations", "sso", "dedicated_support"],
        },
        {
            "id": 4,
            "name": "Developer License",
            "description": "Technical development and testing access",
            "max_users": 50,
            "features": ["technical_access", "api_documentation", "sandbox_environment", "developer_tools"],
        },
    ]


def _get_sample_groups():
    """Generate sample groups based on departments from users"""
    return [
        {
            "id": 1,
            "name": "Administration",
            "description": "Administrative staff managing system and operations",
            "user_ids": [1],  # Rajesh Patel
            "member_count": 1,
        },
        {
            "id": 2,
            "name": "Project Management",
            "description": "Project managers overseeing product development initiatives",
            "user_ids": [2],  # Priya Sharma
            "member_count": 1,
        },
        {
            "id": 3,
            "name": "Operations",
            "description": "Operations team managing day-to-day activities",
            "user_ids": [3],  # Vikram Singh
            "member_count": 1,
        },
        {
            "id": 4,
            "name": "Quality Assurance",
            "description": "QA team ensuring product quality and compliance",
            "user_ids": [4],  # Anjali Verma
            "member_count": 1,
        },
        {
            "id": 5,
            "name": "Field Operations",
            "description": "Field agents managing on-site operations and maintenance",
            "user_ids": [5, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21],  # Aditya Kumar + 10 field agents
            "member_count": 11,
        },
        {
            "id": 6,
            "name": "Customer Support",
            "description": "Customer support team providing technical assistance",
            "user_ids": [6],  # Neha Gupta
            "member_count": 1,
        },
        {
            "id": 7,
            "name": "Technical Consulting",
            "description": "Technical advisors providing architecture and design guidance",
            "user_ids": [7, 8, 9, 10, 11],  # Arjun, Deepak, Pooja, Sameer, Meera
            "member_count": 5,
        },
        {
            "id": 8,
            "name": "Engineering",
            "description": "Software engineers and developers implementing features",
            "user_ids": [22, 23, 24, 25, 26],  # Rohan, Neha Mishra, Aryan, Pooja Shah, Aman
            "member_count": 5,
        },
    ]


def _get_sample_users():
    from datetime import datetime, timedelta
    
    return [
        # Administrator
        {
            "id": 1,
            "username": "admin_rajesh",
            "email": "rajesh.patel@vajra.local",
            "full_name": "Rajesh Patel",
            "role": "Administrator",
            "license_type": "Enterprise License",
            "department": "Administration",
            "location": "Pune HQ",
            "employee_id": "EMP-0001",
            "phone": "+91 98765 43201",
            "hire_date": (datetime.now() - timedelta(days=730)).isoformat(),
            "status": "Active",
        },
        # Managers
        {
            "id": 2,
            "username": "mgr_priya",
            "email": "priya.sharma@vajra.local",
            "full_name": "Priya Sharma",
            "role": "Manager",
            "license_type": "Premium License",
            "department": "Project Management",
            "location": "Pune HQ",
            "employee_id": "EMP-0002",
            "phone": "+91 98765 43202",
            "hire_date": (datetime.now() - timedelta(days=550)).isoformat(),
            "status": "Active",
        },
        {
            "id": 3,
            "username": "mgr_vikram",
            "email": "vikram.singh@vajra.local",
            "full_name": "Vikram Singh",
            "role": "Manager",
            "license_type": "Premium License",
            "department": "Operations",
            "location": "Mumbai Branch",
            "employee_id": "EMP-0003",
            "phone": "+91 98765 43203",
            "hire_date": (datetime.now() - timedelta(days=480)).isoformat(),
            "status": "Active",
        },
        {
            "id": 4,
            "username": "mgr_anjali",
            "email": "anjali.verma@vajra.local",
            "full_name": "Anjali Verma",
            "role": "Manager",
            "license_type": "Premium License",
            "department": "Quality Assurance",
            "location": "Bangalore Branch",
            "employee_id": "EMP-0004",
            "phone": "+91 98765 43204",
            "hire_date": (datetime.now() - timedelta(days=420)).isoformat(),
            "status": "Active",
        },
        {
            "id": 5,
            "username": "mgr_aditya",
            "email": "aditya.kumar@vajra.local",
            "full_name": "Aditya Kumar",
            "role": "Manager",
            "license_type": "Premium License",
            "department": "Field Operations",
            "location": "Delhi Branch",
            "employee_id": "EMP-0005",
            "phone": "+91 98765 43205",
            "hire_date": (datetime.now() - timedelta(days=365)).isoformat(),
            "status": "Active",
        },
        {
            "id": 6,
            "username": "mgr_neha",
            "email": "neha.gupta@vajra.local",
            "full_name": "Neha Gupta",
            "role": "Manager",
            "license_type": "Premium License",
            "department": "Customer Support",
            "location": "Pune HQ",
            "employee_id": "EMP-0006",
            "phone": "+91 98765 43206",
            "hire_date": (datetime.now() - timedelta(days=300)).isoformat(),
            "status": "Active",
        },
        # Advisors
        {
            "id": 7,
            "username": "advisor_arjun",
            "email": "arjun.mehta@vajra.local",
            "full_name": "Arjun Mehta",
            "role": "Advisor",
            "license_type": "Standard License",
            "department": "Technical Consulting",
            "location": "Pune HQ",
            "employee_id": "EMP-0007",
            "specialization": "System Architecture",
            "phone": "+91 98765 43207",
            "hire_date": (datetime.now() - timedelta(days=500)).isoformat(),
            "status": "Active",
        },
        {
            "id": 8,
            "username": "advisor_deepak",
            "email": "deepak.sinha@vajra.local",
            "full_name": "Deepak Sinha",
            "role": "Advisor",
            "license_type": "Standard License",
            "department": "Technical Consulting",
            "location": "Mumbai Branch",
            "employee_id": "EMP-0008",
            "specialization": "Database Optimization",
            "phone": "+91 98765 43208",
            "hire_date": (datetime.now() - timedelta(days=450)).isoformat(),
            "status": "Active",
        },
        {
            "id": 9,
            "username": "advisor_pooja",
            "email": "pooja.joshi@vajra.local",
            "full_name": "Pooja Joshi",
            "role": "Advisor",
            "license_type": "Standard License",
            "department": "Technical Consulting",
            "location": "Bangalore Branch",
            "employee_id": "EMP-0009",
            "specialization": "Cloud Infrastructure",
            "phone": "+91 98765 43209",
            "hire_date": (datetime.now() - timedelta(days=380)).isoformat(),
            "status": "Active",
        },
        {
            "id": 10,
            "username": "advisor_sameer",
            "email": "sameer.khan@vajra.local",
            "full_name": "Sameer Khan",
            "role": "Advisor",
            "license_type": "Standard License",
            "department": "Technical Consulting",
            "location": "Delhi Branch",
            "employee_id": "EMP-0010",
            "specialization": "Security & Compliance",
            "phone": "+91 98765 43210",
            "hire_date": (datetime.now() - timedelta(days=350)).isoformat(),
            "status": "Active",
        },
        {
            "id": 11,
            "username": "advisor_meera",
            "email": "meera.nair@vajra.local",
            "full_name": "Meera Nair",
            "role": "Advisor",
            "license_type": "Standard License",
            "department": "Technical Consulting",
            "location": "Hyderabad Branch",
            "employee_id": "EMP-0011",
            "specialization": "Performance Tuning",
            "phone": "+91 98765 43211",
            "hire_date": (datetime.now() - timedelta(days=320)).isoformat(),
            "status": "Active",
        },
        # Field Agents
        {
            "id": 12,
            "username": "agent_rahul",
            "email": "rahul.mishra@vajra.local",
            "full_name": "Rahul Mishra",
            "role": "Field Agent",
            "license_type": "Standard License",
            "department": "Field Operations",
            "location": "Pune HQ",
            "employee_id": "EMP-0012",
            "phone": "+91 98765 43212",
            "hire_date": (datetime.now() - timedelta(days=200)).isoformat(),
            "status": "Active",
        },
        {
            "id": 13,
            "username": "agent_sneha",
            "email": "sneha.rao@vajra.local",
            "full_name": "Sneha Rao",
            "role": "Field Agent",
            "license_type": "Standard License",
            "department": "Field Operations",
            "location": "Mumbai Branch",
            "employee_id": "EMP-0013",
            "phone": "+91 98765 43213",
            "hire_date": (datetime.now() - timedelta(days=180)).isoformat(),
            "status": "Active",
        },
        {
            "id": 14,
            "username": "agent_karan",
            "email": "karan.bhatt@vajra.local",
            "full_name": "Karan Bhatt",
            "role": "Field Agent",
            "license_type": "Standard License",
            "department": "Field Operations",
            "location": "Bangalore Branch",
            "employee_id": "EMP-0014",
            "phone": "+91 98765 43214",
            "hire_date": (datetime.now() - timedelta(days=160)).isoformat(),
            "status": "Active",
        },
        {
            "id": 15,
            "username": "agent_swati",
            "email": "swati.iyer@vajra.local",
            "full_name": "Swati Iyer",
            "role": "Field Agent",
            "license_type": "Standard License",
            "department": "Field Operations",
            "location": "Delhi Branch",
            "employee_id": "EMP-0015",
            "phone": "+91 98765 43215",
            "hire_date": (datetime.now() - timedelta(days=140)).isoformat(),
            "status": "Active",
        },
        {
            "id": 16,
            "username": "agent_ravi",
            "email": "ravi.saxena@vajra.local",
            "full_name": "Ravi Saxena",
            "role": "Field Agent",
            "license_type": "Standard License",
            "department": "Field Operations",
            "location": "Hyderabad Branch",
            "employee_id": "EMP-0016",
            "phone": "+91 98765 43216",
            "hire_date": (datetime.now() - timedelta(days=120)).isoformat(),
            "status": "Active",
        },
        {
            "id": 17,
            "username": "agent_prerna",
            "email": "prerna.mittal@vajra.local",
            "full_name": "Prerna Mittal",
            "role": "Field Agent",
            "license_type": "Standard License",
            "department": "Field Operations",
            "location": "Pune HQ",
            "employee_id": "EMP-0017",
            "phone": "+91 98765 43217",
            "hire_date": (datetime.now() - timedelta(days=100)).isoformat(),
            "status": "Active",
        },
        {
            "id": 18,
            "username": "agent_sanjay",
            "email": "sanjay.desai@vajra.local",
            "full_name": "Sanjay Desai",
            "role": "Field Agent",
            "license_type": "Standard License",
            "department": "Field Operations",
            "location": "Mumbai Branch",
            "employee_id": "EMP-0018",
            "phone": "+91 98765 43218",
            "hire_date": (datetime.now() - timedelta(days=90)).isoformat(),
            "status": "Active",
        },
        {
            "id": 19,
            "username": "agent_divya",
            "email": "divya.prakash@vajra.local",
            "full_name": "Divya Prakash",
            "role": "Field Agent",
            "license_type": "Standard License",
            "department": "Field Operations",
            "location": "Bangalore Branch",
            "employee_id": "EMP-0019",
            "phone": "+91 98765 43219",
            "hire_date": (datetime.now() - timedelta(days=75)).isoformat(),
            "status": "Active",
        },
        {
            "id": 20,
            "username": "agent_nikhil",
            "email": "nikhil.reddy@vajra.local",
            "full_name": "Nikhil Reddy",
            "role": "Field Agent",
            "license_type": "Standard License",
            "department": "Field Operations",
            "location": "Delhi Branch",
            "employee_id": "EMP-0020",
            "phone": "+91 98765 43220",
            "hire_date": (datetime.now() - timedelta(days=60)).isoformat(),
            "status": "Active",
        },
        {
            "id": 21,
            "username": "agent_kavya",
            "email": "kavya.singh@vajra.local",
            "full_name": "Kavya Singh",
            "role": "Field Agent",
            "license_type": "Standard License",
            "department": "Field Operations",
            "location": "Hyderabad Branch",
            "employee_id": "EMP-0021",
            "phone": "+91 98765 43221",
            "hire_date": (datetime.now() - timedelta(days=45)).isoformat(),
            "status": "Active",
        },
        # Tech Engineers
        {
            "id": 22,
            "username": "engineer_rohan",
            "email": "rohan.gupta@vajra.local",
            "full_name": "Rohan Gupta",
            "role": "Tech Engineer",
            "license_type": "Developer License",
            "department": "Engineering",
            "location": "Pune HQ",
            "employee_id": "EMP-0022",
            "specialization": "Python/Backend",
            "phone": "+91 98765 43222",
            "hire_date": (datetime.now() - timedelta(days=400)).isoformat(),
            "status": "Active",
        },
        {
            "id": 23,
            "username": "engineer_neha",
            "email": "neha.mishra@vajra.local",
            "full_name": "Neha Mishra",
            "role": "Tech Engineer",
            "license_type": "Developer License",
            "department": "Engineering",
            "location": "Pune HQ",
            "employee_id": "EMP-0023",
            "specialization": "React/Frontend",
            "phone": "+91 98765 43223",
            "hire_date": (datetime.now() - timedelta(days=380)).isoformat(),
            "status": "Active",
        },
        {
            "id": 24,
            "username": "engineer_aryan",
            "email": "aryan.verma@vajra.local",
            "full_name": "Aryan Verma",
            "role": "Tech Engineer",
            "license_type": "Developer License",
            "department": "Engineering",
            "location": "Bangalore Branch",
            "employee_id": "EMP-0024",
            "specialization": "DevOps/Infrastructure",
            "phone": "+91 98765 43224",
            "hire_date": (datetime.now() - timedelta(days=350)).isoformat(),
            "status": "Active",
        },
        {
            "id": 25,
            "username": "engineer_pooja",
            "email": "pooja.shah@vajra.local",
            "full_name": "Pooja Shah",
            "role": "Tech Engineer",
            "license_type": "Developer License",
            "department": "Engineering",
            "location": "Mumbai Branch",
            "employee_id": "EMP-0025",
            "specialization": "QA/Testing",
            "phone": "+91 98765 43225",
            "hire_date": (datetime.now() - timedelta(days=320)).isoformat(),
            "status": "Active",
        },
        {
            "id": 26,
            "username": "engineer_aman",
            "email": "aman.chakra@vajra.local",
            "full_name": "Aman Chakrabarti",
            "role": "Tech Engineer",
            "license_type": "Developer License",
            "department": "Engineering",
            "location": "Delhi Branch",
            "employee_id": "EMP-0026",
            "specialization": "Database/SQL",
            "phone": "+91 98765 43226",
            "hire_date": (datetime.now() - timedelta(days=290)).isoformat(),
            "status": "Active",
        },
    ]


@router.post("/admin/roles")
async def create_role(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    data = parse_form_data(form)
    role = Role(
        name=data.get("name", ""),
        permissions=[perm.strip() for perm in data.get("permissions", "").split(",") if perm.strip()],
        data=data,
    )
    db.add(role)
    db.commit()
    return redirect_with_flash("/admin", request, "Role created.", "success")


@router.post("/admin/users")
async def create_user_form(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    data = parse_form_data(form)
    create_user(
        db,
        username=data.get("username", ""),
        email=data.get("email", ""),
        password=data.get("password", "Welcome@123"),
        full_name=data.get("full_name", data.get("username", "")),
        role=data.get("role", "Field Agent"),
        data=data,
    )
    return redirect_with_flash("/admin/users", request, "User created successfully.", "success")


@router.post("/admin/lm")
async def create_loitering_munition(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    data = parse_form_data(form)
    
    # Check if there is an existing unit
    serial_no = data.get("serial_number")
    existing = db.query(LoiteringMunition).filter(LoiteringMunition.serial_number == serial_no).first()
    
    if existing:
        old_data = existing.data or {}
        change_log = old_data.get("change_log", [])
        
        fields_to_track = [
            "unit_name", "customer_id", "contract_id", "sap_part_number", 
            "warranty_valid_from", "warranty_valid_to", "status", "model", 
            "software_version", "last_service_on", "next_service_due", "service_notes"
        ]
        
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        for field in fields_to_track:
            old_val = old_data.get(field, "")
            new_val = data.get(field, "")
            if str(old_val).strip() != str(new_val).strip():
                change_log.append({
                    "timestamp": timestamp,
                    "user": "admin",
                    "field": field.replace("_", " ").title(),
                    "old_value": str(old_val),
                    "new_value": str(new_val)
                })
        
        # Preserve critical fields from old data if not provided in form
        if not data.get("customer") or data.get("customer").strip() == "":
            data["customer"] = old_data.get("customer", "")
        if not data.get("contract") or data.get("contract").strip() == "":
            data["contract"] = old_data.get("contract", "")
        
        # Merge new data with old data to preserve all existing fields
        merged_data = old_data.copy()
        merged_data.update(data)
        merged_data["change_log"] = change_log
        
        existing.unit_name = data.get("unit_name", existing.unit_name)
        existing.data = merged_data
        db.commit()
        db.refresh(existing)
        return redirect_with_flash("/admin/lm", request, "Unit updated and changes logged.", "success")
    else:
        # Create new
        persist_entity(db, LoiteringMunition, data=data, top_level_fields=["unit_name", "serial_number"])
        return redirect_with_flash("/admin/lm", request, "Unit saved.", "success")


@router.post("/admin/gcs")
async def create_ground_control_system(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    data = parse_form_data(form)
    serial_no = data.get("serial_number")
    existing = db.query(GroundControlSystem).filter(GroundControlSystem.serial_number == serial_no).first()
    
    if existing:
        old_data = existing.data or {}
        
        # Preserve critical fields from old data if not provided in form
        if not data.get("customer") or data.get("customer").strip() == "":
            data["customer"] = old_data.get("customer", "")
        if not data.get("contract") or data.get("contract").strip() == "":
            data["contract"] = old_data.get("contract", "")
        
        # Merge new data with old data to preserve all existing fields
        merged_data = old_data.copy()
        merged_data.update(data)
        
        existing.unit_name = data.get("unit_name", existing.unit_name)
        existing.data = merged_data
        db.commit()
        db.refresh(existing)
        return redirect_with_flash("/admin/gcs", request, "Unit updated.", "success")
    else:
        persist_entity(db, GroundControlSystem, data=data, top_level_fields=["unit_name", "serial_number"])
        return redirect_with_flash("/admin/gcs", request, "Unit saved.", "success")


@router.post("/admin/tmv")
async def create_tactical_mobility_vehicle(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    data = parse_form_data(form)
    persist_entity(db, TacticalMobilityVehicle, data=data, top_level_fields=["unit_name", "serial_number"])
    return redirect_with_flash("/admin/tmv", request, "Unit saved.", "success")


@router.post("/admin/simulator")
async def create_simulator(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    data = parse_form_data(form)
    persist_entity(db, SimulatorUnit, data=data, top_level_fields=["unit_name", "serial_number"])
    return redirect_with_flash("/admin/simulator", request, "Unit saved.", "success")


@router.post("/admin/rdv")
async def create_rdv(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    data = parse_form_data(form)
    persist_entity(db, RapidDeploymentVehicle, data=data, top_level_fields=["unit_name", "serial_number"])
    return redirect_with_flash("/admin/rdv", request, "Unit saved.", "success")


@router.post("/admin/lru")
async def create_lru(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    data = parse_form_data(form)
    if "lru_name" in data:
        data["unit_name"] = data["lru_name"]
    persist_entity(db, LineReplaceableUnit, data=data, top_level_fields=["unit_name"])
    return redirect_with_flash("/admin/lru", request, "LRU saved.", "success")


@router.post("/admin/sub-systems")
async def create_sub_system(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    data = parse_form_data(form)
    persist_entity(db, SubSystem, data=data, top_level_fields=["name"])
    return redirect_with_flash("/admin/sub-systems", request, "Sub-system saved.", "success")


@router.post("/admin/batteries")
async def create_battery(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    data = parse_form_data(form)
    persist_entity(db, Battery, data=data, top_level_fields=["unit_name", "serial_number"])
    return redirect_with_flash("/admin/batteries", request, "Unit saved.", "success")


@router.post("/admin/warhead")
async def create_warhead(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    data = parse_form_data(form)
    persist_entity(db, Warhead, data=data, top_level_fields=["unit_name"])
    return redirect_with_flash("/admin/warhead", request, "Unit saved.", "success")


@router.post("/admin/mrls")
async def create_mrls(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    data = parse_form_data(form)
    persist_entity(db, MRLS, data=data, top_level_fields=["unit_name"])
    return redirect_with_flash("/admin/mrls", request, "Unit saved.", "success")


@router.post("/admin/smt-ste")
async def create_smt_ste(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    data = parse_form_data(form)
    persist_entity(db, SMTSTE, data=data, top_level_fields=["unit_name"])
    return redirect_with_flash("/admin/smt-ste", request, "Unit saved.", "success")


@router.post("/admin/sam")
async def create_sam(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    data = parse_form_data(form)
    persist_entity(db, SAM, data=data, top_level_fields=["unit_name"])
    return redirect_with_flash("/admin/sam", request, "Unit saved.", "success")


# Repair Execution Routes
@router.get("/admin/repair-execution")
async def get_repair_executions(request: Request, db: Session = Depends(get_db)):
    """Display repair execution list"""
    items = db.query(RepairExecution).order_by(RepairExecution.repair_execution, RepairExecution.order).all()
    context = build_template_context(request, title="Repair Executions")
    context["items"] = items
    context["total_items"] = len(items)
    return templates.TemplateResponse("repair_execution.html", context)


@router.get("/admin/repair-execution/new")
async def new_repair_execution(request: Request, db: Session = Depends(get_db)):
    """Create new repair execution form"""
    context = build_template_context(request, title="New Repair Execution")
    return templates.TemplateResponse("repair_execution_form.html", context)


@router.post("/admin/repair-execution")
async def create_repair_execution(request: Request, db: Session = Depends(get_db)):
    """Create new repair execution"""
    form = await request.form()
    
    repair_execution = form.get("repair_execution", "").strip()
    status = form.get("status", "").strip()
    order = int(form.get("order", "0") or "0")
    
    if not repair_execution or not status:
        return redirect_with_flash("/admin/repair-execution", request, "Repair Execution and Status are required.", "error")
    
    item = RepairExecution(
        repair_execution=repair_execution,
        status=status,
        order=order
    )
    db.add(item)
    db.commit()
    
    return redirect_with_flash("/admin/repair-execution", request, "Repair Execution created successfully.", "success")


@router.get("/admin/repair-execution/{item_id}/edit")
async def edit_repair_execution(item_id: int, request: Request, db: Session = Depends(get_db)):
    """Edit repair execution"""
    item = db.query(RepairExecution).filter(RepairExecution.id == item_id).first()
    if not item:
        return redirect_with_flash("/admin/repair-execution", request, "Repair Execution not found.", "error")
    
    context = build_template_context(request, title=f"Edit Repair Execution")
    context["item"] = item
    return templates.TemplateResponse("repair_execution_edit.html", context)


@router.post("/admin/repair-execution/{item_id}")
async def update_repair_execution(item_id: int, request: Request, db: Session = Depends(get_db)):
    """Update repair execution"""
    item = db.query(RepairExecution).filter(RepairExecution.id == item_id).first()
    if not item:
        return redirect_with_flash("/admin/repair-execution", request, "Repair Execution not found.", "error")
    
    form = await request.form()
    
    item.repair_execution = form.get("repair_execution", "").strip()
    item.status = form.get("status", "").strip()
    item.order = int(form.get("order", "0") or "0")
    
    if not item.repair_execution or not item.status:
        return redirect_with_flash("/admin/repair-execution", request, "Repair Execution and Status are required.", "error")
    
    db.commit()
    
    return redirect_with_flash("/admin/repair-execution", request, "Repair Execution updated successfully.", "success")


@router.get("/admin/repair-execution/{item_id}/delete")
async def delete_repair_execution(item_id: int, request: Request, db: Session = Depends(get_db)):
    """Delete repair execution"""
    item = db.query(RepairExecution).filter(RepairExecution.id == item_id).first()
    if item:
        db.delete(item)
        db.commit()
    return redirect_with_flash("/admin/repair-execution", request, "Repair Execution deleted.", "success")


import json
from sqlalchemy.sql import func
from models.incident import Incident

def aggregate_report_data(db: Session, data_source: str, x_field: str):
    labels = []
    values = []
    
    if data_source == "incidents":
        if hasattr(Incident, x_field):
            field_attr = getattr(Incident, x_field)
            results = db.query(field_attr, func.count(Incident.id)).group_by(field_attr).all()
            for label, val in results:
                labels.append(str(label or "None"))
                values.append(val)
    elif data_source == "kitting_items":
        if hasattr(KittingItem, x_field):
            field_attr = getattr(KittingItem, x_field)
            results = db.query(field_attr, func.count(KittingItem.id)).group_by(field_attr).all()
            for label, val in results:
                labels.append(str(label or "None"))
                values.append(val)
    elif data_source == "customers":
        if hasattr(Customer, x_field):
            field_attr = getattr(Customer, x_field)
            results = db.query(field_attr, func.count(Customer.id)).group_by(field_attr).all()
            for label, val in results:
                labels.append(str(label or "None"))
                values.append(val)
                
    return {"labels": labels, "values": values}


@router.get("/admin/reports")
def get_reports_page(request: Request, db: Session = Depends(get_db)):
    # Check if we need to seed default reports
    count = db.query(Report).count()
    if count == 0:
        default_reports = [
            Report(
                name="Incident Distribution by Priority",
                description="Overview of incidents across priority levels",
                data_source="incidents",
                chart_type="bar",
                x_field="priority",
                y_field="count"
            ),
            Report(
                name="Incident Status Breakdown",
                description="Status distribution for all open and closed incidents",
                data_source="incidents",
                chart_type="pie",
                x_field="status",
                y_field="count"
            ),
            Report(
                name="Kitting Items by Subsystem",
                description="Count of kitting parts mapped to subsystems",
                data_source="kitting_items",
                chart_type="bar",
                x_field="subsystems",
                y_field="count"
            )
        ]
        for r in default_reports:
            db.add(r)
        db.commit()
    
    db_reports = db.query(Report).order_by(Report.id.desc()).all()
    reports_with_data = []
    
    for r in db_reports:
        chart_data = aggregate_report_data(db, r.data_source, r.x_field)
        reports_with_data.append({
            "id": r.id,
            "name": r.name,
            "description": r.description,
            "data_source": r.data_source,
            "chart_type": r.chart_type,
            "x_field": r.x_field,
            "labels": json.dumps(chart_data["labels"]),
            "values": json.dumps(chart_data["values"])
        })
        
    context = build_template_context(request, reports=reports_with_data)
    return templates.TemplateResponse(request, "reports_dashboards.html", context)


@router.post("/admin/reports")
def create_custom_report(
    request: Request,
    db: Session = Depends(get_db),
    name: str = Form(...),
    description: str = Form(""),
    data_source: str = Form(...),
    chart_type: str = Form(...),
    x_field: str = Form(...),
):
    try:
        report = Report(
            name=name.strip(),
            description=description.strip(),
            data_source=data_source,
            chart_type=chart_type,
            x_field=x_field,
            y_field="count"
        )
        db.add(report)
        db.commit()
        return redirect_with_flash("/admin/reports", request, "Report created successfully.", "success")
    except Exception as e:
        db.rollback()
        return redirect_with_flash("/admin/reports", request, f"Error creating report: {str(e)}", "error")


@router.post("/admin/reports/{report_id}/delete")
def delete_custom_report(report_id: int, request: Request, db: Session = Depends(get_db)):
    report = db.query(Report).filter(Report.id == report_id).first()
    if report:
        db.delete(report)
        db.commit()
        return redirect_with_flash("/admin/reports", request, "Report deleted successfully.", "success")
    return redirect_with_flash("/admin/reports", request, "Report not found.", "error")




