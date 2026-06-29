import json
import os
import shutil
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, Form, Request, UploadFile, File
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from database import get_db
from models.knowledge import KnowledgeDocument, KnowledgeArticle, ApprovalRequest, KnowledgeDocumentVersion
from utils import build_template_context, redirect_with_flash

router = APIRouter()
templates = Jinja2Templates(directory="templates")

UPLOAD_DIR = "static/uploads"

import re

def parse_version(v_str):
    if not v_str:
        return (0,)
    # Remove leading 'v' or 'V'
    clean = re.sub(r'^[vV]', '', v_str.strip())
    # Find all groups of digits
    nums = re.findall(r'\d+', clean)
    if not nums:
        return (0,)
    return tuple(int(x) for x in nums)

def archive_older_versions(db: Session, doc: KnowledgeDocument):
    if doc.doc_type not in ["manual", "service_bulletin", "operator_bulletin", "amendments_leaflet"]:
        return

    # Find other active published documents of the same type and file reference number
    other_docs = db.query(KnowledgeDocument).filter(
        KnowledgeDocument.doc_type == doc.doc_type,
        KnowledgeDocument.file_reference_number == doc.file_reference_number,
        KnowledgeDocument.id != doc.id,
        KnowledgeDocument.status == "published"
    ).all()

    for other in other_docs:
        # Compare versions. If new doc is newer or equal, move existing to history
        if parse_version(doc.version) >= parse_version(other.version):
            archived = KnowledgeDocumentVersion(
                doc_id=doc.id,
                doc_type=other.doc_type,
                file_reference_number=other.file_reference_number,
                version=other.version,
                date_of_issue=other.date_of_issue,
                subject_line=other.subject_line,
                description=other.description,
                attachments=other.attachments,
                data=other.data,
                status="published",
                created_at=other.created_at,
                retired=datetime.now(),
                change_notes=other.change_notes
            )
            db.add(archived)
            db.delete(other)
        else:
            # If the existing one is newer than the newly approved one,
            # the newly approved one goes directly to history!
            archived = KnowledgeDocumentVersion(
                doc_id=other.id,
                doc_type=doc.doc_type,
                file_reference_number=doc.file_reference_number,
                version=doc.version,
                date_of_issue=doc.date_of_issue,
                subject_line=doc.subject_line,
                description=doc.description,
                attachments=doc.attachments,
                data=doc.data,
                status="published",
                created_at=doc.created_at,
                retired=datetime.now(),
                change_notes=doc.change_notes
            )
            db.add(archived)
            db.delete(doc)
            break

    db.commit()


def check_is_approver(request: Request, db: Session) -> bool:
    user_role = request.session.get("user_role")
    user_id = request.session.get("user_id")
    if user_role == "admin":
        return True
    if user_id:
        from models.admin import Group
        group = db.query(Group).filter(Group.name == "knowledge_management_approver").first()
        if group and group.user_ids and user_id in group.user_ids:
            return True
    return False

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
    
    is_approver = check_is_approver(request, db)
    query = db.query(KnowledgeDocument).filter(KnowledgeDocument.doc_type == doc_type)
    if not is_approver:
        query = query.filter(KnowledgeDocument.status == "published")
        
    documents = query.order_by(KnowledgeDocument.created_at.desc()).all()
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
    change_notes: str = Form(""),
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
            
    # Check if this is a version controlled doc type and there is an existing published document
    if doc_type in ["manual", "service_bulletin", "operator_bulletin", "amendments_leaflet"]:
        existing = db.query(KnowledgeDocument).filter(
            KnowledgeDocument.doc_type == doc_type,
            KnowledgeDocument.file_reference_number == file_reference_number,
            KnowledgeDocument.status == "published"
        ).first()
        if existing and parse_version(version) < parse_version(existing.version):
            # Save directly to version table
            version_doc = KnowledgeDocumentVersion(
                doc_id=existing.id,
                doc_type=doc_type,
                file_reference_number=file_reference_number,
                version=version,
                date_of_issue=date_of_issue,
                subject_line=subject_line,
                description=description,
                attachments=attachments,
                status="published",
                created_at=datetime.utcnow(),
                retired=datetime.now(),
                change_notes=change_notes
            )
            db.add(version_doc)
            db.commit()
            return redirect_with_flash(
                f"/knowledge/document/{existing.id}",
                request,
                "Document version uploaded as an older version and saved directly to the version history.",
                "success"
            )

    doc = KnowledgeDocument(
        doc_type=doc_type,
        file_reference_number=file_reference_number,
        version=version,
        date_of_issue=date_of_issue,
        subject_line=subject_line,
        description=description,
        attachments=attachments,
        status="draft",
        created_at=datetime.utcnow(),
        last_accessed=datetime.utcnow(),
        change_notes=change_notes
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    
    req_name = request.session.get("user_name") or "System User"
    approval_req = ApprovalRequest(
        item_type="document",
        item_id=doc.id,
        title=doc.subject_line,
        requested_by=req_name,
        status="pending"
    )
    db.add(approval_req)
    db.commit()
    
    return redirect_with_flash(f"/knowledge/list/{doc_type}", request, "Document submitted for approval. It is currently in draft mode.", "success")


@router.get("/knowledge/document/{doc_id}")
def view_document_details(doc_id: int, request: Request, db: Session = Depends(get_db)):
    doc = db.query(KnowledgeDocument).filter(KnowledgeDocument.id == doc_id).first()
    if not doc:
        return redirect_with_flash("/knowledge", request, "Document not found.", "error")
    
    is_approver = check_is_approver(request, db)
    if doc.status != "published" and not is_approver:
        return redirect_with_flash("/knowledge", request, "You do not have permission to view this draft document.", "error")
        
    doc.last_accessed = datetime.utcnow()
    db.commit()
    
    versions = []
    if doc.doc_type in ["manual", "service_bulletin", "operator_bulletin", "amendments_leaflet"]:
        versions = db.query(KnowledgeDocumentVersion).filter(
            KnowledgeDocumentVersion.doc_type == doc.doc_type,
            KnowledgeDocumentVersion.file_reference_number == doc.file_reference_number
        ).order_by(KnowledgeDocumentVersion.retired.desc()).all()
    
    edit_mode = request.query_params.get("edit", "").lower() == "true"
    context = build_template_context(
        request, 
        doc=doc, 
        doc_type=doc.doc_type, 
        mode="edit" if edit_mode else "view",
        versions=versions
    )
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
    change_notes: str = Form(""),
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
            
    if doc.doc_type in ["manual", "service_bulletin", "operator_bulletin", "amendments_leaflet"] and doc.status == "published":
        if doc.version != version:
            # Archive the old state before updating
            archived = KnowledgeDocumentVersion(
                doc_id=doc.id,
                doc_type=doc.doc_type,
                file_reference_number=doc.file_reference_number,
                version=doc.version,
                date_of_issue=doc.date_of_issue,
                subject_line=doc.subject_line,
                description=doc.description,
                attachments=doc.attachments,
                data=doc.data,
                status="published",
                created_at=doc.created_at,
                retired=datetime.now(),
                change_notes=doc.change_notes
            )
            db.add(archived)

    doc.version = version
    doc.date_of_issue = date_of_issue
    doc.file_reference_number = file_reference_number
    doc.subject_line = subject_line
    doc.description = description
    doc.attachments = current_attachments
    doc.last_accessed = datetime.utcnow()
    doc.change_notes = change_notes
    
    db.commit()
    
    if doc.status == "published":
        archive_older_versions(db, doc)
        
    return redirect_with_flash(f"/knowledge/document/{doc.id}", request, "Document updated successfully.", "success")


# --- Knowledge Articles Routes ---

@router.get("/knowledge/articles")
def list_articles(request: Request, search: str = "", db: Session = Depends(get_db)):
    is_approver = check_is_approver(request, db)
    query = db.query(KnowledgeArticle)
    if not is_approver:
        query = query.filter(KnowledgeArticle.status == "published")
        
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
        status="draft",
        created_at=datetime.utcnow()
    )
    db.add(art)
    db.commit()
    db.refresh(art)
    
    req_name = request.session.get("user_name") or "System User"
    approval_req = ApprovalRequest(
        item_type="article",
        item_id=art.id,
        title=art.title,
        requested_by=req_name,
        status="pending"
    )
    db.add(approval_req)
    db.commit()
    
    return redirect_with_flash("/knowledge/articles", request, "Knowledge Article submitted for approval. It is currently in draft mode.", "success")


@router.get("/knowledge/article/{article_id}")
def view_article_details(article_id: int, request: Request, db: Session = Depends(get_db)):
    article = db.query(KnowledgeArticle).filter(KnowledgeArticle.id == article_id).first()
    if not article:
        return redirect_with_flash("/knowledge/articles", request, "Article not found.", "error")
        
    is_approver = check_is_approver(request, db)
    if article.status != "published" and not is_approver:
        return redirect_with_flash("/knowledge/articles", request, "You do not have permission to view this draft article.", "error")
        
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


# --- Knowledge Approvals Routing ---

@router.get("/knowledge/approvals")
def list_pending_approvals(request: Request, db: Session = Depends(get_db)):
    is_approver = check_is_approver(request, db)
    if not is_approver:
        return redirect_with_flash("/knowledge", request, "Access denied. Only knowledge approvers can view this page.", "error")
        
    requests = db.query(ApprovalRequest).filter(ApprovalRequest.status == "pending").order_by(ApprovalRequest.created_at.desc()).all()
    context = build_template_context(request, requests=requests)
    return templates.TemplateResponse(request, "knowledge_approvals.html", context)


@router.post("/knowledge/approvals/{request_id}/approve")
def approve_request(request_id: int, request: Request, db: Session = Depends(get_db)):
    is_approver = check_is_approver(request, db)
    if not is_approver:
        return redirect_with_flash("/knowledge", request, "Access denied.", "error")
        
    approval_req = db.query(ApprovalRequest).filter(ApprovalRequest.id == request_id).first()
    if not approval_req:
        return redirect_with_flash("/knowledge/approvals", request, "Approval request not found.", "error")
        
    approval_req.status = "approved"
    
    # Update target item status
    if approval_req.item_type == "document":
        doc = db.query(KnowledgeDocument).filter(KnowledgeDocument.id == approval_req.item_id).first()
        if doc:
            doc.status = "published"
            db.commit()
            archive_older_versions(db, doc)
    elif approval_req.item_type == "article":
        art = db.query(KnowledgeArticle).filter(KnowledgeArticle.id == approval_req.item_id).first()
        if art:
            art.status = "published"
            db.commit()
            
    return redirect_with_flash("/knowledge/approvals", request, "Item approved and published successfully.", "success")


@router.post("/knowledge/approvals/{request_id}/reject")
def reject_request(request_id: int, request: Request, db: Session = Depends(get_db)):
    is_approver = check_is_approver(request, db)
    if not is_approver:
        return redirect_with_flash("/knowledge", request, "Access denied.", "error")
        
    approval_req = db.query(ApprovalRequest).filter(ApprovalRequest.id == request_id).first()
    if not approval_req:
        return redirect_with_flash("/knowledge/approvals", request, "Approval request not found.", "error")
        
    approval_req.status = "rejected"
    # Keep item status as draft, but complete the request as rejected
    db.commit()
    return redirect_with_flash("/knowledge/approvals", request, "Item approval request rejected.", "success")


@router.post("/knowledge/document/{doc_id}/approve")
def approve_document_direct(doc_id: int, request: Request, db: Session = Depends(get_db)):
    is_approver = check_is_approver(request, db)
    if not is_approver:
        return redirect_with_flash("/knowledge", request, "Access denied.", "error")
        
    doc = db.query(KnowledgeDocument).filter(KnowledgeDocument.id == doc_id).first()
    if not doc:
        return redirect_with_flash("/knowledge", request, "Document not found.", "error")
        
    doc.status = "published"
    
    # Update any pending approval request
    approval_req = db.query(ApprovalRequest).filter(
        ApprovalRequest.item_type == "document",
        ApprovalRequest.item_id == doc_id,
        ApprovalRequest.status == "pending"
    ).first()
    if approval_req:
        approval_req.status = "approved"
        
    db.commit()
    archive_older_versions(db, doc)
    return redirect_with_flash(f"/knowledge/document/{doc_id}", request, "Document approved and published successfully.", "success")


@router.post("/knowledge/document/{doc_id}/reject")
def reject_document_direct(doc_id: int, request: Request, db: Session = Depends(get_db)):
    is_approver = check_is_approver(request, db)
    if not is_approver:
        return redirect_with_flash("/knowledge", request, "Access denied.", "error")
        
    doc = db.query(KnowledgeDocument).filter(KnowledgeDocument.id == doc_id).first()
    if not doc:
        return redirect_with_flash("/knowledge", request, "Document not found.", "error")
        
    # Document status remains draft, update approval request
    approval_req = db.query(ApprovalRequest).filter(
        ApprovalRequest.item_type == "document",
        ApprovalRequest.item_id == doc_id,
        ApprovalRequest.status == "pending"
    ).first()
    if approval_req:
        approval_req.status = "rejected"
        
    db.commit()
    return redirect_with_flash(f"/knowledge/document/{doc_id}", request, "Document approval request rejected.", "success")


@router.post("/knowledge/article/{article_id}/approve")
def approve_article_direct(article_id: int, request: Request, db: Session = Depends(get_db)):
    is_approver = check_is_approver(request, db)
    if not is_approver:
        return redirect_with_flash("/knowledge", request, "Access denied.", "error")
        
    article = db.query(KnowledgeArticle).filter(KnowledgeArticle.id == article_id).first()
    if not article:
        return redirect_with_flash("/knowledge/articles", request, "Article not found.", "error")
        
    article.status = "published"
    
    # Update any pending approval request
    approval_req = db.query(ApprovalRequest).filter(
        ApprovalRequest.item_type == "article",
        ApprovalRequest.item_id == article_id,
        ApprovalRequest.status == "pending"
    ).first()
    if approval_req:
        approval_req.status = "approved"
        
    db.commit()
    return redirect_with_flash(f"/knowledge/article/{article_id}", request, "Article approved and published successfully.", "success")


@router.post("/knowledge/article/{article_id}/reject")
def reject_article_direct(article_id: int, request: Request, db: Session = Depends(get_db)):
    is_approver = check_is_approver(request, db)
    if not is_approver:
        return redirect_with_flash("/knowledge", request, "Access denied.", "error")
        
    article = db.query(KnowledgeArticle).filter(KnowledgeArticle.id == article_id).first()
    if not article:
        return redirect_with_flash("/knowledge/articles", request, "Article not found.", "error")
        
    # Article status remains draft, update approval request
    approval_req = db.query(ApprovalRequest).filter(
        ApprovalRequest.item_type == "article",
        ApprovalRequest.item_id == article_id,
        ApprovalRequest.status == "pending"
    ).first()
    if approval_req:
        approval_req.status = "rejected"
        
    db.commit()
    return redirect_with_flash(f"/knowledge/article/{article_id}", request, "Article approval request rejected.", "success")

