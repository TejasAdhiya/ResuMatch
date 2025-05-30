from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import List
from utils.resume_analyzer import ResumeAnalyzer
from utils.email_service import EmailService
import json

router = APIRouter()
resume_analyzer = ResumeAnalyzer()
email_service = EmailService()

@router.post("/analyze-bulk")
async def analyze_bulk_resumes(
    files: List[UploadFile] = File(...),
    job_description: str = Form(...)
):
    if len(files) > 10:
        raise HTTPException(status_code=400, detail="Maximum 10 resumes allowed")
    
    # Read all PDF files
    resume_bytes = []
    for file in files:
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail=f"File {file.filename} is not a PDF")
        content = await file.read()
        resume_bytes.append(content)
    
    # Analyze resumes
    results = await resume_analyzer.analyze_bulk_resumes(resume_bytes, job_description)
    return results

@router.post("/send-email")
async def send_email(
    email_type: str = Form(...),
    recipient_email: str = Form(...),
    candidate_name: str = Form(...),
    rejection_reason: str = Form(None)
):
    if email_type == "acceptance":
        success = await email_service.send_acceptance_email(recipient_email, candidate_name)
    elif email_type == "rejection":
        if not rejection_reason:
            raise HTTPException(status_code=400, detail="Rejection reason is required for rejection emails")
        success = await email_service.send_rejection_email(recipient_email, candidate_name, rejection_reason)
    else:
        raise HTTPException(status_code=400, detail="Invalid email type")
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to send email")
    
    return {"message": "Email sent successfully"} 