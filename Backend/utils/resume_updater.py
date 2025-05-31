from docx import Document
import io
import re
from typing import List, Tuple
import tempfile
import os
from utils.openai_client import get_openai_response

def find_section_paragraphs(doc: Document, section_name: str) -> List[int]:
    """Find paragraphs that might be section headers."""
    section_indices = []
    for i, para in enumerate(doc.paragraphs):
        if section_name.lower() in para.text.lower():
            section_indices.append(i)
    return section_indices

def extract_section_text(doc: Document, section_name: str) -> str:
    indices = find_section_paragraphs(doc, section_name)
    if not indices:
        return ""
    idx = indices[0]
    # Collect text until next section or empty line
    section_text = []
    for para in doc.paragraphs[idx+1:]:
        if para.text.strip() == "" or re.match(r"^[A-Z][A-Za-z ]{2,}$", para.text.strip()):
            break
        section_text.append(para.text)
    return "\n".join(section_text).strip()

def replace_section_text(doc: Document, section_name: str, new_text: str):
    indices = find_section_paragraphs(doc, section_name)
    if not indices:
        return
    idx = indices[0]
    # Remove old section content (until next section or empty line)
    remove_indices = []
    for i, para in enumerate(doc.paragraphs[idx+1:], start=idx+1):
        if para.text.strip() == "" or re.match(r"^[A-Z][A-Za-z ]{2,}$", para.text.strip()):
            break
        remove_indices.append(i)
    for i in reversed(remove_indices):
        p = doc.paragraphs[i]._element
        p.getparent().remove(p)
    # Insert new text after section header
    header_idx = idx
    # If there is a paragraph after the header, use it; else, add one
    if header_idx + 1 < len(doc.paragraphs):
        first_para = doc.paragraphs[header_idx + 1]
        lines = new_text.split('\n')
        if lines:
            first_para.text = lines[0]
            for line in lines[1:]:
                new_para = doc.add_paragraph(line)
                # Move the new paragraph to the correct position
                p = new_para._element
                header_elem = doc.paragraphs[header_idx]._element
                header_elem.addnext(p)
    else:
        # No paragraph after header, just add all lines
        for line in new_text.split('\n'):
            doc.add_paragraph(line)

def parse_suggestions(suggestions: str):
    """Parse the AI suggestions into strengths, improvements, and pro tip."""
    strengths, improvements, pro_tip = [], [], ""
    current = None
    for line in suggestions.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.lower().startswith('✨') or 'strength' in line.lower():
            current = 'strengths'
            continue
        if line.lower().startswith('🔍') or 'improvement' in line.lower():
            current = 'improvements'
            continue
        if line.lower().startswith('💡') or 'pro tip' in line.lower():
            current = 'pro_tip'
            continue
        if current == 'strengths':
            strengths.append(line.lstrip('•- '))
        elif current == 'improvements':
            improvements.append(line.lstrip('•- '))
        elif current == 'pro_tip':
            pro_tip += line + ' '
    return strengths, improvements, pro_tip.strip()

def ai_rewrite_summary(original_text: str, job_description: str, missing_keywords: List[str], improvements: List[str]) -> str:
    prompt = f"""
You are a world-class resume writer. Rewrite the following summary as a compelling personal branding statement for a Data Analyst targeting this job description:
---
{job_description}
---
Integrate these keywords naturally: {', '.join(missing_keywords) if missing_keywords else 'None'}
Apply these improvements: {', '.join(improvements) if improvements else 'None'}
Focus on value, impact, and unique strengths. No generic phrases. No section header. Keep it concise and powerful.
Original summary:
{original_text.strip() if original_text else '(empty)'}
"""
    return get_openai_response(prompt)

def ai_rewrite_skills(original_text: str, job_description: str, missing_keywords: List[str], improvements: List[str]) -> str:
    prompt = f"""
You are a world-class resume writer. Rewrite the following skills section for a Data Analyst targeting this job description:
---
{job_description}
---
Group skills by category (e.g., Technical, Analytical, Tools). Integrate these missing keywords naturally: {', '.join(missing_keywords) if missing_keywords else 'None'}
Format for both ATS and human readability. No section header. No empty bullets. No duplication. Keep it concise and modern.
Original skills section:
{original_text.strip() if original_text else '(empty)'}
"""
    return get_openai_response(prompt)

def ai_rewrite_experience(original_text: str, job_description: str, missing_keywords: List[str], improvements: List[str]) -> str:
    prompt = f"""
You are a world-class resume writer. Rewrite the following experience section for a Data Analyst targeting this job description:
---
{job_description}
---
For each job/role, rewrite the bullets using the STAR method (Situation, Task, Action, Result). Integrate these missing keywords and quantifiable achievements. Make each bullet concise, impactful, and tailored to the job description. No section header. No duplication. No empty bullets.
Original experience section:
{original_text.strip() if original_text else '(empty)'}
"""
    return get_openai_response(prompt)

def update_resume_with_suggestions(
    file_content: bytes,
    missing_keywords: List[str],
    suggestions: str,
    job_description: str
) -> str:
    """
    Update the resume with missing keywords and suggestions while preserving formatting.
    Returns the path to the updated file.
    """
    try:
        # Create a temporary file to store the updated resume
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.docx')
        temp_path = temp_file.name
        temp_file.close()

        # Load the original document
        doc = Document(io.BytesIO(file_content))

        # Parse suggestions
        strengths, improvements, pro_tip = parse_suggestions(suggestions)

        # --- Summary ---
        summary_text = extract_section_text(doc, "summary")
        if summary_text:
            improved_summary = ai_rewrite_summary(summary_text, job_description, missing_keywords, improvements)
            replace_section_text(doc, "summary", improved_summary)
        # --- Skills ---
        skills_text = extract_section_text(doc, "skills")
        if skills_text:
            improved_skills = ai_rewrite_skills(skills_text, job_description, missing_keywords, improvements)
            replace_section_text(doc, "skills", improved_skills)
        # --- Experience ---
        exp_text = extract_section_text(doc, "experience")
        if exp_text:
            improved_exp = ai_rewrite_experience(exp_text, job_description, missing_keywords, improvements)
            replace_section_text(doc, "experience", improved_exp)

        # Save the updated document
        doc.save(temp_path)
        return temp_path

    except Exception as e:
        raise Exception(f"Error updating resume: {str(e)}")

def cleanup_temp_file(file_path: str):
    """Clean up temporary files."""
    try:
        if os.path.exists(file_path):
            os.unlink(file_path)
    except Exception as e:
        print(f"Error cleaning up temporary file: {str(e)}") 