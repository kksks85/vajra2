#!/usr/bin/env python
"""
Seed script to create 50+ varied incident records for the ALS - 50 Customer Service Management Portal.
Creates incidents with various statuses, priorities, issue types, and product categories.
Run this to populate the database with sample incidents.
"""

import sys
from datetime import datetime, timedelta
import random

# Set output encoding to UTF-8 to prevent console issues on Windows
if sys.platform.startswith('win'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from database import SessionLocal
from models.incident import Incident


# Data for generating varied incidents
CUSTOMERS = [
    "Indian Air Force",
    "Indian Army",
    "Indian Navy"
]

PRODUCT_CATEGORIES = [
    "Loitering Munition (LM)",
    "Ground Control System (GCS)",
    "Tactical Mobility Vehicle (TMV)",
    "Simulator",
    "Gimbal",
    "Tracker",
    "RDV",
    "Warhead + ESAM"
]

SUBSYSTEMS = [
    "Airframe",
    "Propulsion",
    "Avionics & Flight Control",
    "Communication",
    "Payload",
    "Computing",
    "Display",
    "Control Interface",
    "Power"
]

STATUSES = [
    "new",
    "diagnosis",
    "in_progress",
    "on_hold",
    "repair_completed",
    "quality_check",
    "closure"
]

PRIORITIES = [
    "critical",
    "high",
    "medium",
    "low"
]

ISSUE_TYPES = [
    "electrical",
    "mechanical",
    "electronics",
    "software",
    "communication",
    "sensors",
    "camera_imaging",
    "payload",
    "maintenance",
    "physical_damage",
    "general_enquiry",
    "other"
]

STAGES = [
    "triage",
    "investigation",
    "resolution",
    "closure"
]

# Sample incident titles and descriptions by issue type
INCIDENT_TEMPLATES = {
    "electrical": [
        ("Electrical circuit failure in gimbal", "The gimbal is experiencing intermittent power loss affecting stabilization."),
        ("Power distribution fault", "Power not reaching payload module. Needs troubleshooting on main bus."),
        ("Battery connector corrosion", "Oxidation detected on battery terminals affecting voltage delivery."),
        ("Voltage regulator malfunction", "Unstable voltage output from regulator unit causing sensor issues."),
    ],
    "mechanical": [
        ("Wing mounting bracket stress fracture", "Micro-cracks detected on left wing mounting bracket after flight."),
        ("Landing gear alignment issue", "Wheels not properly aligned during landing causing uneven wear."),
        ("Fuselage dent from hard landing", "Minor structural damage on fuselage requiring inspection."),
        ("Servo actuator wear", "Servo arm shows signs of excessive wear and needs replacement."),
    ],
    "electronics": [
        ("IMU calibration drift", "Inertial measurement unit showing incorrect heading data."),
        ("Sensor fusion algorithm fault", "Multiple sensors providing conflicting data causing navigation errors."),
        ("Flight controller board malfunction", "Erratic behavior from flight controller, possible firmware issue."),
        ("Signal processing unit failure", "Video/data processing showing artifacts and dropout."),
    ],
    "software": [
        ("Firmware version incompatibility", "Old firmware version causing conflicts with new GCS software."),
        ("Navigation algorithm error", "Route planning generating invalid waypoints in certain conditions."),
        ("Telemetry data corruption", "Intermittent data loss during long duration flights."),
        ("Control loop oscillation", "Unstable PID parameters causing pitch oscillation."),
    ],
    "communication": [
        ("Radio link dropout", "Losing connection beyond 5km line of sight."),
        ("Data transmission delay", "Increased latency affecting real-time control."),
        ("Antenna connection loose", "RF connector loosening causing signal degradation."),
        ("Frequency interference", "External RF interference affecting communication range."),
    ],
    "sensors": [
        ("GPS signal loss", "Unable to acquire satellite fix after 30 seconds of flight."),
        ("Barometric pressure sensor drift", "Altitude reading shows 50m error from known reference."),
        ("Accelerometer noise", "Excessive vibration noise in acceleration data."),
        ("Magnetic compass interference", "Local magnetic field affecting compass calibration."),
    ],
    "camera_imaging": [
        ("Camera lens fogging", "Condensation inside camera lens affecting image quality."),
        ("Image stabilization EIS failure", "Video playback shows jerky motion compensation."),
        ("Thermal imaging non-responsive", "Thermal camera not initializing during power-on."),
        ("Gimbal roll drift", "Camera roll axis drifting during stationary hover."),
    ],
    "payload": [
        ("Payload release mechanism jammed", "Payload unable to detach during delivery."),
        ("Warhead arming circuit fault", "Safety interlock preventing arming sequence."),
        ("Sensor payload power connection", "Inconsistent power to IR sensor module."),
        ("Data link to payload unit", "Command signal not reaching payload controller."),
    ],
    "maintenance": [
        ("Scheduled 500-hour inspection due", "Aircraft approaching next maintenance interval."),
        ("Filter replacement overdue", "Intake filter showing clogging signs."),
        ("Oil level check required", "Hydraulic fluid level below minimum."),
        ("Component calibration drift", "Routine calibration affecting accuracy."),
    ],
    "physical_damage": [
        ("Propeller blade damaged", "Impact damage during ground handling."),
        ("Control surface hinge wear", "Excessive play in aileron hinge joint."),
        ("Canopy crack from pressure", "Hairline crack in clear acrylic canopy."),
        ("Wire bundle abrasion", "Protective shielding worn through friction."),
    ],
    "general_enquiry": [
        ("Operating condition clarification", "Customer asking about maximum altitude capability."),
        ("Maintenance procedure inquiry", "Questions about recommended service intervals."),
        ("Spare parts availability", "Requesting information on part lead times."),
        ("Performance specification verification", "Confirming range and endurance numbers."),
    ],
}


def generate_title_and_description(issue_type):
    """Generate title and description based on issue type."""
    if issue_type in INCIDENT_TEMPLATES:
        template = random.choice(INCIDENT_TEMPLATES[issue_type])
        return template[0], template[1]
    return f"Issue with {issue_type} system", f"Problem reported with {issue_type} subsystem requiring investigation."


def generate_random_date():
    """Generate a random date within the last 30 days."""
    days_back = random.randint(0, 29)
    return datetime.now() - timedelta(days=days_back)


def seed_incidents():
    """Create 50+ varied incident records."""
    db = SessionLocal()
    
    # Check if incidents already exist
    existing = db.query(Incident).count()
    if existing > 0:
        print(f"[INFO] Database already has {existing} incident(s). Skipping seeding.")
        return
    
    incidents = []
    incident_count = 0
    
    # Generate diverse incidents
    for i in range(50):
        customer = random.choice(CUSTOMERS)
        product = random.choice(PRODUCT_CATEGORIES)
        subsystem = random.choice(SUBSYSTEMS)
        status = random.choice(STATUSES)
        priority = random.choice(PRIORITIES)
        issue_type = random.choice(ISSUE_TYPES)
        stage = random.choice(STAGES)
        created_date = generate_random_date()
        
        # Generate title and description
        title, description = generate_title_and_description(issue_type)
        
        # Enhance title with customer and product info
        title = f"[{customer[:3].upper()}] {product} - {title}"
        
        # Create comprehensive description with all relevant information
        contact_name = random.choice([
            "Squadron Leader Priya Sharma",
            "Flight Lieutenant Vikram Singh", 
            "Lieutenant Colonel Deepak Verma",
            "Major Neha Chopra",
            "Captain Sanjay Mishra",
            "Captain Manish Kumar",
            "Commander Anita Gupta",
            "Wing Commander Rajesh Kumar",
            "Colonel Arun Patel",
            "Commodore Suresh Desai"
        ])
        
        assignment_group = random.choice([
            "Technical Support",
            "Field Engineering",
            "Quality Assurance",
            "Operations Support",
            "Maintenance Team"
        ])
        
        assigned_to = random.choice([
            "John Smith",
            "Sarah Johnson",
            "Michael Chen",
            "Priya Verma",
            "Rajesh Kumar",
            "Anita Desai",
            "Vikram Singh",
            "Deepak Patel"
        ])
        
        sla = random.choice([
            "4 hours",
            "8 hours", 
            "24 hours",
            "48 hours",
            "1 week"
        ])
        
        warranty_status = random.choice([
            "Under Warranty",
            "Out of Warranty",
            "Warranty Expiring Soon",
            "Extended Warranty"
        ])
        
        # Enhance description with comprehensive details
        full_description = f"{description}\n\n📋 INCIDENT DETAILS:\nCustomer: {customer}\nRequestor: {contact_name}\nProduct: {product}\nSerial No: {random.choice(['LM-SN-001-01', 'LM-SN-002-03', 'GCS-SN-001-01', 'TMV-SN-001-02', 'SIM-SN-001-01'])}\nSub-system: {subsystem}\n\n⚙️ ASSIGNMENT:\nAssignment Group: {assignment_group}\nAssigned To: {assigned_to}\nSLA: {sla}\n\n📅 SERVICE:\nWarranty Status: {warranty_status}\nLast Serviced: {(created_date - timedelta(days=random.randint(5, 60))).strftime('%Y-%m-%d')}\n\n🔍 CLASSIFICATION:\nIssue Type: {issue_type.replace('_', ' ').title()}\nPriority: {priority.capitalize()}\nStage: {stage.capitalize()}\nStatus: {status.replace('_', ' ').title()}"
        
        incident = Incident(
            title=title,
            description=full_description,
            status=status,
            priority=priority,
            issue_type=issue_type,
            stage=stage,
            created_at=created_date,
            # Customer & Requestor
            caller=customer,
            requestor_name=random.choice([
                "Squadron Leader Priya Sharma",
                "Flight Lieutenant Vikram Singh",
                "Lieutenant Colonel Deepak Verma",
                "Major Neha Chopra",
                "Captain Sanjay Mishra",
                "Captain Manish Kumar",
                "Commander Anita Gupta",
            ]),
            customer_contract=f"Contract-{random.randint(2024, 2025)}-{random.randint(1000, 9999)}",
            requestor_contact=f"+91 {random.randint(100, 999)} {random.randint(1000000, 9999999)}",
            # Product Information
            srlm_system=random.choice(["SRLM", "ERLM"]),
            platform_variant=product,
            line_replaceable_unit=f"{product.split()[0]}-SN-{random.randint(1000, 9999)}-{random.randint(1, 99):02d}",
            sub_system=subsystem,
            # Issue Classification
            assignment_group=random.choice(["Technical Support", "Engineering", "Field Operations", "Quality Assurance"]),
            assigned_to=random.choice(["Rajesh Kumar", "Priya Sharma", "Vikram Singh", "Deepak Verma", "Neha Chopra"]),
            sla=random.choice(["2 hours", "4 hours", "8 hours", "24 hours", "48 hours"]),
            # Service History
            warranty_status=random.choice(["Active", "Expired", "Expiring Soon", "Not Applicable"]),
            last_serviced_date=(created_date - timedelta(days=random.randint(1, 60))).strftime("%Y-%m-%d"),
        )
        
        incidents.append(incident)
        incident_count += 1
    
    # Add some edge cases and specific combinations for better testing
    edge_cases = [
        ("Critical AOG incident", "Aircraft grounded - complete system failure requiring immediate resolution.", "Indian Air Force", "new", "critical", "software"),
        ("Routine maintenance check", "Standard post-flight inspection and component verification.", "Indian Navy", "in_progress", "low", "maintenance"),
        ("Warranty claim investigation", "Premature component failure within warranty period being investigated.", "Indian Army", "diagnosis", "high", "electronics"),
        ("Test flight anomaly", "Unexpected behavior during acceptance test requiring root cause analysis.", "Indian Air Force", "investigation", "high", "sensors"),
        ("Spare part availability issue", "Specific component out of stock affecting repair timeline.", "Indian Navy", "on_hold", "medium", "general_enquiry"),
    ]
    
    for title, description, customer, status, priority, issue_type in edge_cases:
        stage_map = {
            "new": "triage",
            "diagnosis": "investigation",
            "in_progress": "resolution",
            "on_hold": "investigation",
            "repair_completed": "closure",
            "quality_check": "closure",
            "closure": "closure"
        }
        stage = stage_map.get(status, "triage")
        created = generate_random_date()
        
        incident = Incident(
            title=f"[{customer[:3].upper()}] {title}",
            description=f"{description}\n\nCustomer: {customer}",
            status=status,
            priority=priority,
            issue_type=issue_type,
            stage=stage,
            created_at=created,
            # Customer & Requestor
            caller=customer,
            requestor_name=random.choice([
                "Squadron Leader Priya Sharma",
                "Flight Lieutenant Vikram Singh",
                "Lieutenant Colonel Deepak Verma",
                "Major Neha Chopra",
                "Captain Sanjay Mishra",
                "Captain Manish Kumar",
                "Commander Anita Gupta",
            ]),
            customer_contract=f"Contract-{random.randint(2024, 2025)}-{random.randint(1000, 9999)}",
            requestor_contact=f"+91 {random.randint(100, 999)} {random.randint(1000000, 9999999)}",
            # Product Information
            srlm_system=random.choice(["SRLM", "ERLM"]),
            platform_variant=random.choice(PRODUCT_CATEGORIES),
            line_replaceable_unit=f"LRU-{random.randint(1000, 9999)}-{random.randint(1, 99):02d}",
            sub_system=random.choice(SUBSYSTEMS),
            # Issue Classification
            assignment_group=random.choice(["Technical Support", "Engineering", "Field Operations", "Quality Assurance"]),
            assigned_to=random.choice(["Rajesh Kumar", "Priya Sharma", "Vikram Singh", "Deepak Verma", "Neha Chopra"]),
            sla=random.choice(["2 hours", "4 hours", "8 hours", "24 hours", "48 hours"]),
            # Service History
            warranty_status=random.choice(["Active", "Expired", "Expiring Soon", "Not Applicable"]),
            last_serviced_date=(created - timedelta(days=random.randint(1, 60))).strftime("%Y-%m-%d"),
        )
        incidents.append(incident)
        incident_count += 1
    
    try:
        db.add_all(incidents)
        db.commit()
        print(f"✅ Successfully created {incident_count} incident records:")
        print(f"   - Customers: {', '.join(set(CUSTOMERS))}")
        print(f"   - Product Categories: {len(PRODUCT_CATEGORIES)}")
        print(f"   - Statuses: {len(STATUSES)}")
        print(f"   - Priorities: {len(PRIORITIES)}")
        print(f"   - Issue Types: {len(ISSUE_TYPES)}")
        print(f"   - Date Range: Last 30 days")
        print("\n📊 Incident Summary:")
        
        # Print summary by status
        status_counts = {}
        priority_counts = {}
        for incident in incidents:
            status_counts[incident.status] = status_counts.get(incident.status, 0) + 1
            priority_counts[incident.priority] = priority_counts.get(incident.priority, 0) + 1
        
        print("   By Status:")
        for status, count in sorted(status_counts.items()):
            print(f"     - {status}: {count}")
        
        print("   By Priority:")
        for priority, count in sorted(priority_counts.items()):
            print(f"     - {priority}: {count}")
            
    except Exception as e:
        db.rollback()
        print(f"❌ Error seeding incidents: {str(e)}")
    finally:
        db.close()


if __name__ == "__main__":
    seed_incidents()
