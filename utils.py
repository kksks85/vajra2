from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import Request
from starlette.responses import RedirectResponse


def add_flash(request: Request, message: str, category: str = "info") -> None:
    messages: list = request.session.get("flash_messages", [])
    messages.append({"message": message, "category": category})
    request.session["flash_messages"] = messages


def get_flash_messages(request: Request) -> list[dict]:
    messages = request.session.get("flash_messages", [])
    request.session["flash_messages"] = []
    return messages


def get_session_user_id(request: Request) -> Optional[int]:
    return request.session.get("user_id")


def set_session_user(request: Request, user) -> None:
    request.session["user_id"] = user.id
    request.session["user_role"] = user.role
    request.session["user_name"] = user.full_name
    request.session["last_activity"] = datetime.utcnow().isoformat()


def clear_session(request: Request) -> None:
    request.session.clear()


def redirect_with_flash(url: str, request: Request, message: str, category: str = "info"):
    add_flash(request, message, category)
    return RedirectResponse(url=url, status_code=302)


def paginate(items: list, page: int = 1, per_page: int = 50) -> dict:
    """Paginate a list of items and return pagination metadata."""
    total = len(items)
    total_pages = (total + per_page - 1) // per_page
    page = max(1, min(page, total_pages if total_pages > 0 else 1))
    
    start = (page - 1) * per_page
    end = start + per_page
    paginated_items = items[start:end]
    
    return {
        "items": paginated_items,
        "page": page,
        "per_page": per_page,
        "total": total,
        "total_pages": total_pages,
        "has_previous": page > 1,
        "has_next": page < total_pages,
        "previous_page": page - 1 if page > 1 else None,
        "next_page": page + 1 if page < total_pages else None,
        "start_index": start + 1,
        "end_index": min(end, total),
    }


def build_template_context(request: Request, **kwargs) -> dict:
    def build_initials(value: str) -> str:
        parts = [part for part in value.split() if part]
        if not parts:
            return "U"
        initials = "".join(part[0].upper() for part in parts[:2])
        return initials or "U"

    def format_utc(value: datetime | None, fmt: str = "%d %b %Y %H:%M") -> str:
        if not value:
            return "-"
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.strftime(fmt)

    user_name = request.session.get("user_name")
    user_role = request.session.get("user_role")
    current_user = None
    if user_name or user_role:
        display_name = user_name or "User"
        display_role = (user_role or "User").title()
        current_user = {
            "name": display_name,
            "role": display_role,
            "initials": build_initials(display_name),
        }

    context = {
        "request": request,
        "flash_messages": get_flash_messages(request),
        "format_utc": format_utc,
        "current_user": current_user,
    }
    context.update(kwargs)
    return context
