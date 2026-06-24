from fastapi import APIRouter, Depends, Form, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from database import get_db
from models.admin import Role, User, License, Group
from services.auth import create_user
from utils import build_template_context, redirect_with_flash, paginate

router = APIRouter()
templates = Jinja2Templates(directory="templates")

BATTERY_TYPES = [
    "Lithium-Ion 12S 44.4V",
    "Li-Polymer 6S 22.2V",
    "Li-Fe 4S 12.8V"
]


@router.get("/admin")
def admin_page(request: Request, db: Session = Depends(get_db)):
    roles = _get_sample_roles()
    licenses = _get_sample_licenses()
    groups = _get_sample_groups()
    users = _get_sample_users()
    context = build_template_context(request, roles=roles, licenses=licenses, groups=groups, users=users)
    return templates.TemplateResponse(request, "admin.html", context)


@router.get("/admin/users")
def users_list_page(request: Request):
    page = int(request.query_params.get("page", 1))
    all_users = _get_sample_users()
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
def user_view_page(request: Request, user_id: int):
    user = next((item for item in _get_sample_users() if item["id"] == user_id), None)
    roles = _get_sample_roles()
    licenses = _get_sample_licenses()
    context = build_template_context(request, user=user, roles=roles, licenses=licenses, mode="view")
    return templates.TemplateResponse(request, "user_config.html", context)


@router.get("/admin/users/{user_id}/edit")
def user_edit_page(request: Request, user_id: int):
    user = next((item for item in _get_sample_users() if item["id"] == user_id), None)
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
def licenses_list_page(request: Request):
    page = int(request.query_params.get("page", 1))
    all_licenses = _get_sample_licenses()
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
def groups_list_page(request: Request):
    page = int(request.query_params.get("page", 1))
    all_groups = _get_sample_groups()
    pagination = paginate(all_groups, page=page, per_page=50)
    context = build_template_context(request, groups=pagination["items"], pagination=pagination)
    return templates.TemplateResponse(request, "groups_list.html", context)


@router.get("/admin/groups/new")
def groups_new_page(request: Request):
    managers = _get_sample_managers()
    context = build_template_context(request, managers=managers)
    return templates.TemplateResponse(request, "group_config.html", context)


@router.get("/admin/groups/{group_id}")
def view_group_page(request: Request, group_id: int):
    all_groups = _get_sample_groups()
    all_users = _get_sample_users()
    group = next((g for g in all_groups if g["id"] == group_id), None)
    if not group:
        return redirect_with_flash("/admin/groups", request, "Group not found.", "error")
    # Get full user objects for the group
    group_users = [u for u in all_users if u["id"] in group.get("user_ids", [])]
    context = build_template_context(request, group=group, group_users=group_users, mode="view")
    return templates.TemplateResponse(request, "group_config.html", context)


@router.get("/admin/groups/{group_id}/edit")
def edit_group_page(request: Request, group_id: int):
    all_groups = _get_sample_groups()
    all_users = _get_sample_users()
    managers = _get_sample_managers()
    group = next((g for g in all_groups if g["id"] == group_id), None)
    if not group:
        return redirect_with_flash("/admin/groups", request, "Group not found.", "error")
    group_users = [u for u in all_users if u["id"] in group.get("user_ids", [])]
    context = build_template_context(request, group=group, group_users=group_users, managers=managers, mode="edit")
    return templates.TemplateResponse(request, "group_config.html", context)


@router.post("/admin/groups")
def create_or_update_group(
    request: Request,
    name: str = Form(...),
    description: str = Form(""),
    group_email: str = Form(""),
    manager_id: str = Form(""),
    parent: str = Form(""),
):
    # In a real app, save to database with new fields
    return redirect_with_flash("/admin/groups", request, "Group saved successfully.", "success")


@router.get("/admin/customers")
def customer_list_page(request: Request):
    page = int(request.query_params.get("page", 1))
    all_customers = _get_sample_customers()
    pagination = paginate(all_customers, page=page, per_page=50)
    context = build_template_context(request, customers=pagination["items"], pagination=pagination)
    return templates.TemplateResponse(request, "customers_list.html", context)


@router.get("/admin/customers/new")
def customer_configuration_page(request: Request):
    context = build_template_context(request)
    return templates.TemplateResponse(request, "customer_config.html", context)


@router.post("/admin/customers")
def create_customer(request: Request):
    return redirect_with_flash("/admin/customers", request, "Customer saved.", "success")


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
            "status": "Disabled",
        },
    ]


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
def customer_view_page(request: Request, customer_id: int):
    customer = next((item for item in _get_sample_customers() if item["id"] == customer_id), None)
    context = build_template_context(request, customer=customer, mode="view")
    return templates.TemplateResponse(request, "customer_config.html", context)


@router.get("/admin/customers/{customer_id}/edit")
def customer_edit_page(request: Request, customer_id: int):
    customer = next((item for item in _get_sample_customers() if item["id"] == customer_id), None)
    context = build_template_context(request, customer=customer, mode="edit")
    return templates.TemplateResponse(request, "customer_config.html", context)


@router.get("/admin/customers/{customer_id}/disable")
def customer_disable(request: Request, customer_id: int):
    return redirect_with_flash("/admin/customers", request, "Customer disabled.", "success")


@router.get("/admin/contracts")
def contracts_list_page(request: Request):
    page = int(request.query_params.get("page", 1))
    all_contracts = _get_sample_contracts()
    pagination = paginate(all_contracts, page=page, per_page=50)
    context = build_template_context(request, contracts=pagination["items"], pagination=pagination)
    return templates.TemplateResponse(request, "contracts_list.html", context)


@router.get("/admin/contracts/new")
def contract_configuration_page(request: Request):
    customers = _get_sample_customers()
    context = build_template_context(request, customers=customers)
    return templates.TemplateResponse(request, "contract_config.html", context)


@router.get("/admin/contracts/{contract_id}")
def contract_view_page(request: Request, contract_id: int):
    contract = next((item for item in _get_sample_contracts() if item["id"] == contract_id), None)
    customers = _get_sample_customers()
    context = build_template_context(request, contract=contract, customers=customers, mode="view")
    return templates.TemplateResponse(request, "contract_config.html", context)


@router.get("/admin/contracts/{contract_id}/edit")
def contract_edit_page(request: Request, contract_id: int):
    contract = next((item for item in _get_sample_contracts() if item["id"] == contract_id), None)
    customers = _get_sample_customers()
    context = build_template_context(request, contract=contract, customers=customers, mode="edit")
    return templates.TemplateResponse(request, "contract_config.html", context)


@router.get("/admin/contracts/{contract_id}/disable")
def contract_disable(request: Request, contract_id: int):
    return redirect_with_flash("/admin/contracts", request, "Contract disabled.", "success")


@router.get("/admin/lm")
def loitering_munition_list_page(request: Request):
    page = int(request.query_params.get("page", 1))
    all_units = _get_sample_units("LM")
    pagination = paginate(all_units, page=page, per_page=50)
    context = build_template_context(request, units=pagination["items"], unit_label="Loitering Munition (LM)", pagination=pagination)
    return templates.TemplateResponse(request, "lm_list.html", context)


@router.get("/admin/lm/new")
def loitering_munition_new_page(request: Request):
    customers = _get_sample_customers()
    contracts = _get_sample_contracts()
    context = build_template_context(request, customers=customers, contracts=contracts)
    return templates.TemplateResponse(request, "loitering_munition.html", context)


@router.get("/admin/lm/{unit_id}")
def loitering_munition_view_page(request: Request, unit_id: int):
    unit = next((item for item in _get_sample_units("LM") if item["id"] == unit_id), None)
    customers = _get_sample_customers()
    contracts = _get_sample_contracts()
    context = build_template_context(request, unit=unit, customers=customers, contracts=contracts, mode="view")
    return templates.TemplateResponse(request, "loitering_munition.html", context)


@router.get("/admin/lm/{unit_id}/edit")
def loitering_munition_edit_page(request: Request, unit_id: int):
    unit = next((item for item in _get_sample_units("LM") if item["id"] == unit_id), None)
    customers = _get_sample_customers()
    contracts = _get_sample_contracts()
    context = build_template_context(request, unit=unit, customers=customers, contracts=contracts, mode="edit")
    return templates.TemplateResponse(request, "loitering_munition.html", context)


@router.get("/admin/lm/{unit_id}/disable")
def loitering_munition_disable(request: Request, unit_id: int):
    return redirect_with_flash("/admin/lm", request, "Unit disabled.", "success")


@router.get("/admin/gcs")
def ground_control_system_list_page(request: Request):
    page = int(request.query_params.get("page", 1))
    all_units = _get_sample_units("GCS")
    pagination = paginate(all_units, page=page, per_page=50)
    context = build_template_context(request, units=pagination["items"], unit_label="Ground Control Systems (GCS)", pagination=pagination)
    return templates.TemplateResponse(request, "gcs_list.html", context)


@router.get("/admin/gcs/new")
def ground_control_system_new_page(request: Request):
    customers = _get_sample_customers()
    contracts = _get_sample_contracts()
    context = build_template_context(request, customers=customers, contracts=contracts)
    return templates.TemplateResponse(request, "ground_control_system.html", context)


@router.get("/admin/gcs/{unit_id}")
def ground_control_system_view_page(request: Request, unit_id: int):
    unit = next((item for item in _get_sample_units("GCS") if item["id"] == unit_id), None)
    customers = _get_sample_customers()
    contracts = _get_sample_contracts()
    context = build_template_context(request, unit=unit, customers=customers, contracts=contracts, mode="view")
    return templates.TemplateResponse(request, "ground_control_system.html", context)


@router.get("/admin/gcs/{unit_id}/edit")
def ground_control_system_edit_page(request: Request, unit_id: int):
    unit = next((item for item in _get_sample_units("GCS") if item["id"] == unit_id), None)
    customers = _get_sample_customers()
    contracts = _get_sample_contracts()
    context = build_template_context(request, unit=unit, customers=customers, contracts=contracts, mode="edit")
    return templates.TemplateResponse(request, "ground_control_system.html", context)


@router.get("/admin/gcs/{unit_id}/disable")
def ground_control_system_disable(request: Request, unit_id: int):
    return redirect_with_flash("/admin/gcs", request, "Unit disabled.", "success")


@router.get("/admin/tmv")
def tactical_mobility_vehicle_list_page(request: Request):
    page = int(request.query_params.get("page", 1))
    all_units = _get_sample_units("TMV")
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
def tactical_mobility_vehicle_view_page(request: Request, unit_id: int):
    unit = next((item for item in _get_sample_units("TMV") if item["id"] == unit_id), None)
    customers = _get_sample_customers()
    contracts = _get_sample_contracts()
    context = build_template_context(request, unit=unit, customers=customers, contracts=contracts, mode="view")
    return templates.TemplateResponse(request, "tactical_mobility_vehicle.html", context)


@router.get("/admin/tmv/{unit_id}/edit")
def tactical_mobility_vehicle_edit_page(request: Request, unit_id: int):
    unit = next((item for item in _get_sample_units("TMV") if item["id"] == unit_id), None)
    customers = _get_sample_customers()
    contracts = _get_sample_contracts()
    context = build_template_context(request, unit=unit, customers=customers, contracts=contracts, mode="edit")
    return templates.TemplateResponse(request, "tactical_mobility_vehicle.html", context)


@router.get("/admin/tmv/{unit_id}/disable")
def tactical_mobility_vehicle_disable(request: Request, unit_id: int):
    return redirect_with_flash("/admin/tmv", request, "Unit disabled.", "success")


@router.get("/admin/simulator")
def simulator_list_page(request: Request):
    page = int(request.query_params.get("page", 1))
    all_units = _get_sample_units("SIM")
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
def simulator_view_page(request: Request, unit_id: int):
    unit = next((item for item in _get_sample_units("SIM") if item["id"] == unit_id), None)
    customers = _get_sample_customers()
    contracts = _get_sample_contracts()
    context = build_template_context(request, unit=unit, customers=customers, contracts=contracts, mode="view")
    return templates.TemplateResponse(request, "simulator.html", context)


@router.get("/admin/simulator/{unit_id}/edit")
def simulator_edit_page(request: Request, unit_id: int):
    unit = next((item for item in _get_sample_units("SIM") if item["id"] == unit_id), None)
    customers = _get_sample_customers()
    contracts = _get_sample_contracts()
    context = build_template_context(request, unit=unit, customers=customers, contracts=contracts, mode="edit")
    return templates.TemplateResponse(request, "simulator.html", context)


@router.get("/admin/simulator/{unit_id}/disable")
def simulator_disable(request: Request, unit_id: int):
    return redirect_with_flash("/admin/simulator", request, "Unit disabled.", "success")


@router.get("/admin/rdv")
def rdv_list_page(request: Request):
    page = int(request.query_params.get("page", 1))
    all_units = _get_sample_units("RDV")
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
def rdv_view_page(request: Request, unit_id: int):
    unit = next((item for item in _get_sample_units("RDV") if item["id"] == unit_id), None)
    customers = _get_sample_customers()
    contracts = _get_sample_contracts()
    context = build_template_context(request, unit=unit, customers=customers, contracts=contracts, mode="view")
    return templates.TemplateResponse(request, "rapid_deployment_vehicle.html", context)


@router.get("/admin/rdv/{unit_id}/edit")
def rdv_edit_page(request: Request, unit_id: int):
    unit = next((item for item in _get_sample_units("RDV") if item["id"] == unit_id), None)
    customers = _get_sample_customers()
    contracts = _get_sample_contracts()
    context = build_template_context(request, unit=unit, customers=customers, contracts=contracts, mode="edit")
    return templates.TemplateResponse(request, "rapid_deployment_vehicle.html", context)


@router.get("/admin/rdv/{unit_id}/disable")
def rdv_disable(request: Request, unit_id: int):
    return redirect_with_flash("/admin/rdv", request, "Unit disabled.", "success")


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
def batteries_list_page(request: Request):
    page = int(request.query_params.get("page", 1))
    all_units = _get_sample_units("BATTERY")
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
def batteries_view_page(request: Request, unit_id: int):
    unit = next((item for item in _get_sample_units("BATTERY") if item["id"] == unit_id), None)
    customers = _get_sample_customers()
    contracts = _get_sample_contracts()
    context = build_template_context(request, unit=unit, customers=customers, contracts=contracts, battery_types=BATTERY_TYPES, mode="view")
    return templates.TemplateResponse(request, "battery_config.html", context)


@router.get("/admin/batteries/{unit_id}/edit")
def batteries_edit_page(request: Request, unit_id: int):
    unit = next((item for item in _get_sample_units("BATTERY") if item["id"] == unit_id), None)
    customers = _get_sample_customers()
    contracts = _get_sample_contracts()
    context = build_template_context(request, unit=unit, customers=customers, contracts=contracts, battery_types=BATTERY_TYPES, mode="edit")
    return templates.TemplateResponse(request, "battery_config.html", context)


@router.get("/admin/batteries/{unit_id}/disable")
def batteries_disable(request: Request, unit_id: int):
    return redirect_with_flash("/admin/batteries", request, "Unit disabled.", "success")


@router.get("/admin/warhead")
def warhead_list_page(request: Request):
    page = int(request.query_params.get("page", 1))
    all_units = _get_sample_units("WARHEAD")
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
def warhead_view_page(request: Request, unit_id: int):
    unit = next((item for item in _get_sample_units("WARHEAD") if item["id"] == unit_id), None)
    customers = _get_sample_customers()
    contracts = _get_sample_contracts()
    context = build_template_context(request, unit=unit, customers=customers, contracts=contracts, mode="view")
    return templates.TemplateResponse(request, "warhead_config.html", context)


@router.get("/admin/warhead/{unit_id}/edit")
def warhead_edit_page(request: Request, unit_id: int):
    unit = next((item for item in _get_sample_units("WARHEAD") if item["id"] == unit_id), None)
    customers = _get_sample_customers()
    contracts = _get_sample_contracts()
    context = build_template_context(request, unit=unit, customers=customers, contracts=contracts, mode="edit")
    return templates.TemplateResponse(request, "warhead_config.html", context)


@router.get("/admin/warhead/{unit_id}/disable")
def warhead_disable(request: Request, unit_id: int):
    return redirect_with_flash("/admin/warhead", request, "Unit disabled.", "success")


@router.get("/admin/mrls")
def mrls_list_page(request: Request):
    page = int(request.query_params.get("page", 1))
    all_units = _get_sample_units("MRLS")
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
def mrls_view_page(request: Request, unit_id: int):
    unit = next((item for item in _get_sample_units("MRLS") if item["id"] == unit_id), None)
    customers = _get_sample_customers()
    contracts = _get_sample_contracts()
    platform_variants = _get_sample_platform_variants()
    context = build_template_context(request, unit=unit, customers=customers, contracts=contracts, platform_variants=platform_variants, mode="view")
    return templates.TemplateResponse(request, "mrls_config.html", context)


@router.get("/admin/mrls/{unit_id}/edit")
def mrls_edit_page(request: Request, unit_id: int):
    unit = next((item for item in _get_sample_units("MRLS") if item["id"] == unit_id), None)
    customers = _get_sample_customers()
    contracts = _get_sample_contracts()
    platform_variants = _get_sample_platform_variants()
    context = build_template_context(request, unit=unit, customers=customers, contracts=contracts, platform_variants=platform_variants, mode="edit")
    return templates.TemplateResponse(request, "mrls_config.html", context)


@router.get("/admin/mrls/{unit_id}/disable")
def mrls_disable(request: Request, unit_id: int):
    return redirect_with_flash("/admin/mrls", request, "Unit disabled.", "success")


@router.get("/admin/smt-ste")
def smt_ste_list_page(request: Request):
    page = int(request.query_params.get("page", 1))
    all_units = _get_sample_units("SMT_STE")
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
def smt_ste_view_page(request: Request, unit_id: int):
    unit = next((item for item in _get_sample_units("SMT_STE") if item["id"] == unit_id), None)
    customers = _get_sample_customers()
    contracts = _get_sample_contracts()
    platform_variants = _get_sample_platform_variants()
    context = build_template_context(request, unit=unit, customers=customers, contracts=contracts, platform_variants=platform_variants, mode="view")
    return templates.TemplateResponse(request, "smt_ste_config.html", context)


@router.get("/admin/smt-ste/{unit_id}/edit")
def smt_ste_edit_page(request: Request, unit_id: int):
    unit = next((item for item in _get_sample_units("SMT_STE") if item["id"] == unit_id), None)
    customers = _get_sample_customers()
    contracts = _get_sample_contracts()
    platform_variants = _get_sample_platform_variants()
    context = build_template_context(request, unit=unit, customers=customers, contracts=contracts, platform_variants=platform_variants, mode="edit")
    return templates.TemplateResponse(request, "smt_ste_config.html", context)


@router.get("/admin/smt-ste/{unit_id}/disable")
def smt_ste_disable(request: Request, unit_id: int):
    return redirect_with_flash("/admin/smt-ste", request, "Unit disabled.", "success")


@router.get("/admin/sam")
def sam_list_page(request: Request):
    page = int(request.query_params.get("page", 1))
    all_units = _get_sample_units("SAM")
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
def sam_view_page(request: Request, unit_id: int):
    unit = next((item for item in _get_sample_units("SAM") if item["id"] == unit_id), None)
    customers = _get_sample_customers()
    contracts = _get_sample_contracts()
    context = build_template_context(request, unit=unit, customers=customers, contracts=contracts, mode="view")
    return templates.TemplateResponse(request, "sam_config.html", context)


@router.get("/admin/sam/{unit_id}/edit")
def sam_edit_page(request: Request, unit_id: int):
    unit = next((item for item in _get_sample_units("SAM") if item["id"] == unit_id), None)
    customers = _get_sample_customers()
    contracts = _get_sample_contracts()
    context = build_template_context(request, unit=unit, customers=customers, contracts=contracts, mode="edit")
    return templates.TemplateResponse(request, "sam_config.html", context)


@router.get("/admin/sam/{unit_id}/disable")
def sam_disable(request: Request, unit_id: int):
    return redirect_with_flash("/admin/sam", request, "Unit disabled.", "success")


@router.get("/admin/lru")
def lru_list_page(request: Request):
    page = int(request.query_params.get("page", 1))
    all_lrus = _get_sample_lrus()
    pagination = paginate(all_lrus, page=page, per_page=50)
    context = build_template_context(request, lrus=pagination["items"], pagination=pagination)
    return templates.TemplateResponse(request, "lru_list.html", context)


@router.get("/admin/lru/new")
def lru_new_page(request: Request):
    platform_variants = _get_sample_platform_variants()
    context = build_template_context(request, platform_variants=platform_variants)
    return templates.TemplateResponse(request, "lru_config.html", context)


@router.get("/admin/lru/{lru_id}")
def lru_view_page(request: Request, lru_id: int):
    lru = next((item for item in _get_sample_lrus() if item["id"] == lru_id), None)
    platform_variants = _get_sample_platform_variants()
    context = build_template_context(request, lru=lru, platform_variants=platform_variants, mode="view")
    return templates.TemplateResponse(request, "lru_config.html", context)


@router.get("/admin/lru/{lru_id}/edit")
def lru_edit_page(request: Request, lru_id: int):
    lru = next((item for item in _get_sample_lrus() if item["id"] == lru_id), None)
    platform_variants = _get_sample_platform_variants()
    context = build_template_context(request, lru=lru, platform_variants=platform_variants, mode="edit")
    return templates.TemplateResponse(request, "lru_config.html", context)


@router.get("/admin/lru/{lru_id}/disable")
def lru_disable(request: Request, lru_id: int):
    return redirect_with_flash("/admin/lru", request, "LRU disabled.", "success")


@router.get("/admin/sub-systems")
def sub_systems_list_page(request: Request):
    page = int(request.query_params.get("page", 1))
    all_sub_systems = _get_sample_sub_systems()
    pagination = paginate(all_sub_systems, page=page, per_page=50)
    context = build_template_context(request, sub_systems=pagination["items"], pagination=pagination)
    return templates.TemplateResponse(request, "sub_systems_list.html", context)


@router.get("/admin/sub-systems/new")
def sub_systems_new_page(request: Request):
    platform_variants = _get_sample_platform_variants()
    context = build_template_context(request, platform_variants=platform_variants)
    return templates.TemplateResponse(request, "sub_systems_config.html", context)


@router.get("/admin/sub-systems/{sub_system_id}")
def sub_systems_view_page(request: Request, sub_system_id: int):
    sub_system = next((item for item in _get_sample_sub_systems() if item["id"] == sub_system_id), None)
    platform_variants = _get_sample_platform_variants()
    context = build_template_context(
        request,
        sub_system=sub_system,
        platform_variants=platform_variants,
        mode="view",
    )
    return templates.TemplateResponse(request, "sub_systems_config.html", context)


@router.get("/admin/sub-systems/{sub_system_id}/edit")
def sub_systems_edit_page(request: Request, sub_system_id: int):
    sub_system = next((item for item in _get_sample_sub_systems() if item["id"] == sub_system_id), None)
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
    return redirect_with_flash("/admin/sub-systems", request, "Sub-system disabled.", "success")


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
def create_role(
    request: Request,
    name: str = Form(...),
    permissions: str = Form(""),
    db: Session = Depends(get_db),
):
    role = Role(name=name, permissions=[perm.strip() for perm in permissions.split(",") if perm.strip()])
    db.add(role)
    db.commit()
    return redirect_with_flash("/admin", request, "Role created.", "success")


@router.post("/admin/users")
def create_user_form(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    full_name: str = Form(""),
    role: str = Form("Field Agent"),
    license_type: str = Form("Standard License"),
    department: str = Form(""),
    location: str = Form(""),
    employee_id: str = Form(""),
    specialization: str = Form(""),
    phone: str = Form(""),
    hire_date: str = Form(""),
    password: str = Form("Welcome@123"),
    db: Session = Depends(get_db),
):
    # Create user with extended attributes
    create_user(
        db,
        username=username,
        email=email,
        password=password,
        full_name=full_name or username,
        role=role,
    )
    return redirect_with_flash("/admin/users", request, "User created successfully.", "success")


@router.post("/admin/lm")
def create_loitering_munition(request: Request):
    return redirect_with_flash("/admin/lm", request, "Unit saved.", "success")


@router.post("/admin/gcs")
def create_ground_control_system(request: Request):
    return redirect_with_flash("/admin/gcs", request, "Unit saved.", "success")


@router.post("/admin/tmv")
def create_tactical_mobility_vehicle(request: Request):
    return redirect_with_flash("/admin/tmv", request, "Unit saved.", "success")


@router.post("/admin/simulator")
def create_simulator(request: Request):
    return redirect_with_flash("/admin/simulator", request, "Unit saved.", "success")


@router.post("/admin/rdv")
def create_rdv(request: Request):
    return redirect_with_flash("/admin/rdv", request, "Unit saved.", "success")


@router.post("/admin/lru")
def create_lru(request: Request):
    return redirect_with_flash("/admin/lru", request, "LRU saved.", "success")


@router.post("/admin/sub-systems")
def create_sub_system(request: Request):
    return redirect_with_flash("/admin/sub-systems", request, "Sub-system saved.", "success")


@router.post("/admin/batteries")
def create_battery(request: Request):
    return redirect_with_flash("/admin/batteries", request, "Unit saved.", "success")


@router.post("/admin/warhead")
def create_warhead(request: Request):
    return redirect_with_flash("/admin/warhead", request, "Unit saved.", "success")


@router.post("/admin/mrls")
def create_mrls(request: Request):
    return redirect_with_flash("/admin/mrls", request, "Unit saved.", "success")


@router.post("/admin/smt-ste")
def create_smt_ste(request: Request):
    return redirect_with_flash("/admin/smt-ste", request, "Unit saved.", "success")


@router.post("/admin/sam")
def create_sam(request: Request):
    return redirect_with_flash("/admin/sam", request, "Unit saved.", "success")


