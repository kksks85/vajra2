import sys
# Set output encoding to UTF-8 to prevent console issues on Windows
if sys.platform.startswith('win'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

# Apply compatibility monkey-patch for Starlette/FastAPI Jinja2Templates.TemplateResponse
import inspect
from fastapi.templating import Jinja2Templates

original_template_response = Jinja2Templates.TemplateResponse
sig = inspect.signature(original_template_response)
params = list(sig.parameters.keys())
expects_request_first = len(params) > 1 and params[1] == 'request'

def patched_template_response(self, *args, **kwargs):
    request_val = None
    name_val = None
    context_val = None
    
    if len(args) == 3:
        request_val, name_val, context_val = args
    elif len(args) == 2:
        if isinstance(args[0], str):
            name_val, context_val = args
        else:
            request_val, name_val = args
            context_val = kwargs.pop('context', None)
    elif len(args) == 1:
        if isinstance(args[0], str):
            name_val = args[0]
        else:
            request_val = args[0]
            name_val = kwargs.pop('name', None)
            context_val = kwargs.pop('context', None)
            
    request_val = kwargs.pop('request', request_val)
    name_val = kwargs.pop('name', name_val)
    context_val = kwargs.pop('context', context_val)
    
    if context_val is None:
        context_val = {}
    elif not isinstance(context_val, dict):
        try:
            context_val = dict(context_val)
        except Exception:
            context_val = {}
            
    if 'request' not in context_val and request_val is not None:
        context_val['request'] = request_val

    if expects_request_first:
        return original_template_response(self, request_val, name_val, context_val, **kwargs)
    else:
        return original_template_response(self, name_val, context_val, **kwargs)

Jinja2Templates.TemplateResponse = patched_template_response


from config import settings
from database import Base, engine
import models.entities  # Ensure all entity models are loaded into metadata
from models.query_request import QueryRequest  # Load QueryRequest model for database table creation
from routers.auth import router as auth_router
from routers.admin import router as admin_router
from routers.incidents import router as incidents_router
from routers.knowledge import router as knowledge_router
from routers.builder import router as builder_router
from routers.dashboard import router as dashboard_router
from routers.email_config import router as email_config_router
from routers.email_rules import router as email_rules_router
from routers.repair_execution import router as repair_execution_router
from routers.query_request import router as query_request_router

app = FastAPI(title=settings.APP_NAME)
app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(dashboard_router)
app.include_router(auth_router)
app.include_router(incidents_router)
app.include_router(query_request_router)
app.include_router(knowledge_router)
app.include_router(builder_router)
app.include_router(admin_router)
app.include_router(repair_execution_router)
app.include_router(email_config_router)
app.include_router(email_rules_router)


@app.on_event("startup")
def on_startup():
    print("[STARTUP] Starting up ALS - 50 Customer Service Management Portal...")
    try:
        Base.metadata.create_all(bind=engine)
        print("[OK] Database schema initialized")
    except Exception as e:
        print(f"[ERROR] Error creating tables: {e}")
