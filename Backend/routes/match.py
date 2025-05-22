from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from utils.matcher import calculate_match
from utils.resume_parser import extract_resume_text

router = APIRouter()

@router.post("/upload-resume")
async def upload_resume(
    file: UploadFile = File(...),
    job_description: str = Form(...)
):
    """
    Endpoint to handle resume and job description, and calculate match results.
    """
    try:
        contents = await file.read()
        resume_text = extract_resume_text(contents, file.filename)
        
        # Await the calculate_match function and ensure proper handling of the result
        result = await calculate_match(resume_text, job_description)

        response = {
            "similarity_score": result["similarity_score"],
            "matched_keywords": result["matched_keywords"],
            "missing_keywords": result["missing_keywords"],
        }

        return response

    except Exception as e:
        print(f"Error in processing: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
