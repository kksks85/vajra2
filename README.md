# ALS - 50 Customer Service Management Portal (Python-Only)

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

## Containerization
Build the Docker image:
```bash
docker build -t vajra-service-management .
```

Run the app locally using Docker:
```bash
docker run -p 8000:8000 --env DATABASE_URL=sqlite:///./vajra.db vajra-service-management
```

Run with Docker Compose and a MySQL database:
```bash
docker compose up --build
```

Push the container to a registry for cloud deployment:
```bash
docker tag vajra-service-management <registry>/<repo>/vajra-service-management:latest
docker push <registry>/<repo>/vajra-service-management:latest
```

In cloud deployments, set `DATABASE_URL` to your managed database connection string.

## Modules (v1)
- Incident management (task-driven stages)
- Knowledge management
- Administration and RBAC
- Low-code/no-code workflow builder
