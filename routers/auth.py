from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from utils import add_flash, build_template_context, clear_session, set_session_user

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# Demo credentials for testing
DEMO_CREDENTIALS = {
    "admin": ("admin123", {"id": 1, "full_name": "Administrator", "role": "admin"}),
    "supervisor": ("super123", {"id": 2, "full_name": "Sarah Supervisor", "role": "supervisor"}),
    "technician": ("tech123", {"id": 3, "full_name": "John Technician", "role": "technician"}),
    "agent": ("agent123", {"id": 4, "full_name": "Alex Agent", "role": "agent"}),
    "demo": ("demo123", {"id": 5, "full_name": "Demo User", "role": "agent"}),
}


@router.get("/login")
def login_page(request: Request):
    # If already logged in, redirect to dashboard
    user_id = request.session.get("user_id")
    if user_id:
        return RedirectResponse(url="/", status_code=302)
    
    context = build_template_context(request)
    return templates.TemplateResponse(request, "login.html", context)


@router.post("/login")
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
):
    """Simple login endpoint with demo credentials"""
    
    # Check demo credentials
    if username in DEMO_CREDENTIALS:
        correct_password, user_info = DEMO_CREDENTIALS[username]
        if password == correct_password:
            # Create a simple user object for session
            class SimpleUser:
                def __init__(self, data):
                    self.id = data["id"]
                    self.full_name = data["full_name"]
                    self.role = data["role"]
            
            user = SimpleUser(user_info)
            set_session_user(request, user)
            return RedirectResponse(url="/", status_code=302)
    
    # Invalid credentials
    add_flash(request, "Invalid username or password.", "danger")
    return RedirectResponse(url="/login", status_code=302)


@router.get("/logout")
def logout(request: Request):
    clear_session(request)
    return RedirectResponse(url="/login", status_code=302)
