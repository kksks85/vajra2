# Vajra Service Management (Python-Only)

Enterprise-grade service management for drone operations. Includes incident management, knowledge management, admin/RBAC, and a low-code/no-code workflow builder.

## Architecture
- Backend: FastAPI + SQLAlchemy
- Templates: Jinja2 (server-rendered)
- Database: SQLite (local file)

## Setup

### 1) Install dependencies
```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

### 2) Initialize database
```bash
python init_db.py
```

### 3) Run the app
```bash
uvicorn main:app --reload
```

## Environment
Copy `.env.example` to `.env` and update values as needed.

## Modules (v1)
- Incident management (task-driven stages)
- Knowledge management
- Administration and RBAC
- Low-code/no-code workflow builder
