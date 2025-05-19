from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from utils.resume_parser import extract_resume_text
from utils.matcher import calculate_match

router = APIRouter()

@router.post("/upload-resume")
async def upload_resume(
    file: UploadFile = File(...),
    job_description: str = Form(...)
):
    try:
        contents = await file.read()
        resume_text = extract_resume_text(contents, file.filename)
        result = calculate_match(resume_text, job_description)
        return result
    except Exception as e:
        print("ERROR:", str(e))  # prints in terminal
        raise HTTPException(status_code=500, detail=str(e))









