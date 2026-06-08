from fastapi import APIRouter, Depends, Form, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from database import get_db
from models.knowledge import KnowledgeArticle
from utils import build_template_context, redirect_with_flash

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/knowledge")
def knowledge_page(request: Request, db: Session = Depends(get_db)):
    articles = db.query(KnowledgeArticle).order_by(KnowledgeArticle.created_at.desc()).all()
    context = build_template_context(request, articles=articles)
    return templates.TemplateResponse(request, "knowledge.html", context)


@router.post("/knowledge")
def create_article(
    request: Request,
    title: str = Form(...),
    content: str = Form(...),
    tags: str = Form(""),
    db: Session = Depends(get_db),
):
    tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]
    article = KnowledgeArticle(title=title, content=content, tags=tag_list)
    db.add(article)
    db.commit()
    return redirect_with_flash("/knowledge", request, "Article published.", "success")
