import json
import os
import shutil
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, Form, Request, UploadFile, File
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from database import get_db
from models.knowledge import KnowledgeDocument, KnowledgeArticle
from utils import build_template_context, redirect_with_flash

router = APIRouter()
templates = Jinja2Templates(directory="templates")

UPLOAD_DIR = "static/uploads"

DOC_LABELS = {
    "manual": "Manuals",
    "service_bulletin": "Service Bulletins",
    "operator_bulletin": "Operator Bulletins",
    "amendments_leaflet": "Amendments leaflets",
    "incoming_letter": "In-coming Letters",
    "outgoing_letter": "Out-going Letters",
}


@router.get("/knowledge")
def knowledge_dashboard(request: Request, db: Session = Depends(get_db)):
    counts = {}
    for doc_type in DOC_LABELS.keys():
        counts[doc_type] = db.query(KnowledgeDocument).filter(KnowledgeDocument.doc_type == doc_type).count()
    counts["knowledge_article"] = db.query(KnowledgeArticle).count()
    context = build_template_context(request, counts=counts)
    return templates.TemplateResponse(request, "knowledge_dashboard.html", context)


@router.get("/knowledge/list/{doc_type}")
def list_documents(doc_type: str, request: Request, db: Session = Depends(get_db)):
    if doc_type not in DOC_LABELS:
        return redirect_with_flash("/knowledge", request, "Invalid document category.", "error")
    
    documents = db.query(KnowledgeDocument).filter(KnowledgeDocument.doc_type == doc_type).order_by(KnowledgeDocument.created_at.desc()).all()
    label = DOC_LABELS[doc_type]
    context = build_template_context(request, documents=documents, doc_type=doc_type, label=label)
    return templates.TemplateResponse(request, "knowledge_list.html", context)


@router.get("/knowledge/document/new")
def new_document_form(request: Request):
    doc_type = request.query_params.get("type", "manual")
    if doc_type not in DOC_LABELS:
        doc_type = "manual"
    
    context = build_template_context(request, doc_type=doc_type, mode="create")
    return templates.TemplateResponse(request, "knowledge_form.html", context)


@router.post("/knowledge/document/new")
def save_new_document(
    request: Request,
    doc_type: str = Form(...),
    version: str = Form(...),
    date_of_issue: str = Form(...),
    file_reference_number: str = Form(...),
    subject_line: str = Form(...),
    description: str = Form("Please refer to the attached document"),
    files: List[UploadFile] = File([]),
    db: Session = Depends(get_db),
):
    attachments = []
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    for upload_file in files:
        if upload_file.filename:
            filename = os.path.basename(upload_file.filename)
            dest_path = os.path.join(UPLOAD_DIR, filename)
            if os.path.exists(dest_path):
                base_name, ext = os.path.splitext(filename)
                filename = f"{base_name}_{int(datetime.now().timestamp())}{ext}"
                dest_path = os.path.join(UPLOAD_DIR, filename)
            
            with open(dest_path, "wb") as f:
                shutil.copyfileobj(upload_file.file, f)
            attachments.append(filename)
            
    doc = KnowledgeDocument(
        doc_type=doc_type,
        file_reference_number=file_reference_number,
        version=version,
        date_of_issue=date_of_issue,
        subject_line=subject_line,
        description=description,
        attachments=attachments,
        created_at=datetime.utcnow(),
        last_accessed=datetime.utcnow()
    )
    db.add(doc)
    db.commit()
    return redirect_with_flash(f"/knowledge/list/{doc_type}", request, "Document uploaded successfully.", "success")


@router.get("/knowledge/document/{doc_id}")
def view_document_details(doc_id: int, request: Request, db: Session = Depends(get_db)):
    doc = db.query(KnowledgeDocument).filter(KnowledgeDocument.id == doc_id).first()
    if not doc:
        return redirect_with_flash("/knowledge", request, "Document not found.", "error")
    
    doc.last_accessed = datetime.utcnow()
    db.commit()
    
    edit_mode = request.query_params.get("edit", "").lower() == "true"
    context = build_template_context(request, doc=doc, doc_type=doc.doc_type, mode="edit" if edit_mode else "view")
    return templates.TemplateResponse(request, "knowledge_form.html", context)


@router.post("/knowledge/document/{doc_id}")
def update_document_details(
    doc_id: int,
    request: Request,
    version: str = Form(...),
    date_of_issue: str = Form(...),
    file_reference_number: str = Form(...),
    subject_line: str = Form(...),
    description: str = Form(...),
    deleted_attachments: str = Form(""),
    files: List[UploadFile] = File([]),
    db: Session = Depends(get_db),
):
    doc = db.query(KnowledgeDocument).filter(KnowledgeDocument.id == doc_id).first()
    if not doc:
        return redirect_with_flash("/knowledge", request, "Document not found.", "error")
    
    current_attachments = list(doc.attachments)
    if deleted_attachments:
        try:
            to_delete = json.loads(deleted_attachments)
            for f in to_delete:
                if f in current_attachments:
                    current_attachments.remove(f)
        except Exception:
            pass
            
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    for upload_file in files:
        if upload_file.filename:
            filename = os.path.basename(upload_file.filename)
            dest_path = os.path.join(UPLOAD_DIR, filename)
            if os.path.exists(dest_path):
                base_name, ext = os.path.splitext(filename)
                filename = f"{base_name}_{int(datetime.now().timestamp())}{ext}"
                dest_path = os.path.join(UPLOAD_DIR, filename)
            with open(dest_path, "wb") as f:
                shutil.copyfileobj(upload_file.file, f)
            current_attachments.append(filename)
            
    doc.version = version
    doc.date_of_issue = date_of_issue
    doc.file_reference_number = file_reference_number
    doc.subject_line = subject_line
    doc.description = description
    doc.attachments = current_attachments
    doc.last_accessed = datetime.utcnow()
    
    db.commit()
    return redirect_with_flash(f"/knowledge/document/{doc.id}", request, "Document updated successfully.", "success")


# --- Knowledge Articles Routes ---

@router.get("/knowledge/articles")
def list_articles(request: Request, search: str = "", db: Session = Depends(get_db)):
    query = db.query(KnowledgeArticle)
    if search:
        query = query.filter(
            (KnowledgeArticle.title.like(f"%{search}%")) |
            (KnowledgeArticle.reference_number.like(f"%{search}%")) |
            (KnowledgeArticle.content.like(f"%{search}%"))
        )
    articles = query.order_by(KnowledgeArticle.created_at.desc()).all()
    context = build_template_context(request, articles=articles, search=search)
    return templates.TemplateResponse(request, "knowledge_articles_list.html", context)


@router.get("/knowledge/article/new")
def new_article_form(request: Request, db: Session = Depends(get_db)):
    # Auto-generate next KM reference number
    latest_art = db.query(KnowledgeArticle).filter(
        KnowledgeArticle.reference_number.like("KM%")
    ).order_by(KnowledgeArticle.id.desc()).first()
    
    ref_num = "KM001"
    if latest_art:
        try:
            num_str = latest_art.reference_number[2:]
            next_num = int(num_str) + 1
            ref_num = f"KM{next_num:03d}"
        except ValueError:
            pass
            
    context = build_template_context(request, ref_num=ref_num, mode="create")
    return templates.TemplateResponse(request, "knowledge_article_form.html", context)


@router.post("/knowledge/article/new")
def save_new_article(
    request: Request,
    reference_number: str = Form(...),
    title: str = Form(...),
    content: str = Form(...),
    tags_str: str = Form("", alias="tags"),
    db: Session = Depends(get_db),
):
    # Parse tags
    tags = [t.strip() for t in tags_str.split(",") if t.strip()] if tags_str else []
    
    # Check duplicate ref number
    existing = db.query(KnowledgeArticle).filter(KnowledgeArticle.reference_number == reference_number).first()
    if existing:
        context = build_template_context(request, ref_num=reference_number, title=title, content=content, tags=tags, mode="create", flash_messages=[{"category": "error", "message": f"Reference number {reference_number} already exists."}])
        return templates.TemplateResponse(request, "knowledge_article_form.html", context)
        
    art = KnowledgeArticle(
        reference_number=reference_number,
        title=title,
        content=content,
        tags=tags,
        created_at=datetime.utcnow()
    )
    db.add(art)
    db.commit()
    return redirect_with_flash("/knowledge/articles", request, "Knowledge Article published successfully.", "success")


@router.get("/knowledge/article/{article_id}")
def view_article_details(article_id: int, request: Request, db: Session = Depends(get_db)):
    article = db.query(KnowledgeArticle).filter(KnowledgeArticle.id == article_id).first()
    if not article:
        return redirect_with_flash("/knowledge/articles", request, "Article not found.", "error")
    context = build_template_context(request, article=article)
    return templates.TemplateResponse(request, "knowledge_article_detail.html", context)


@router.get("/knowledge/article/{article_id}/edit")
def edit_article_form(article_id: int, request: Request, db: Session = Depends(get_db)):
    article = db.query(KnowledgeArticle).filter(KnowledgeArticle.id == article_id).first()
    if not article:
        return redirect_with_flash("/knowledge/articles", request, "Article not found.", "error")
    context = build_template_context(request, article=article, ref_num=article.reference_number, mode="edit")
    return templates.TemplateResponse(request, "knowledge_article_form.html", context)


@router.post("/knowledge/article/{article_id}/edit")
def update_article_details(
    article_id: int,
    request: Request,
    title: str = Form(...),
    content: str = Form(...),
    tags_str: str = Form("", alias="tags"),
    db: Session = Depends(get_db),
):
    article = db.query(KnowledgeArticle).filter(KnowledgeArticle.id == article_id).first()
    if not article:
        return redirect_with_flash("/knowledge/articles", request, "Article not found.", "error")
        
    tags = [t.strip() for t in tags_str.split(",") if t.strip()] if tags_str else []
    
    article.title = title
    article.content = content
    article.tags = tags
    db.commit()
    return redirect_with_flash(f"/knowledge/article/{article.id}", request, "Article updated successfully.", "success")


@router.get("/knowledge/article/{article_id}/delete")
def delete_article(article_id: int, request: Request, db: Session = Depends(get_db)):
    article = db.query(KnowledgeArticle).filter(KnowledgeArticle.id == article_id).first()
    if not article:
        return redirect_with_flash("/knowledge/articles", request, "Article not found.", "error")
    db.delete(article)
    db.commit()
    return redirect_with_flash("/knowledge/articles", request, "Article deleted successfully.", "success")
