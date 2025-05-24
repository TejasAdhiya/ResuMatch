import openai
import json
import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

class OpenAIService:
    def __init__(self, api_key: str):
        openai.api_key = api_key
        self.client = openai.OpenAI(api_key=api_key)
    
    def analyze_resume(self, resume_text: str) -> Dict[str, Any]:
        """
        Analyze resume and extract key information for job matching
        """
        try:
            prompt = f"""
            Analyze this resume and provide a JSON response with the following structure:
            {{
                "predicted_job_title": "Most likely job title this person is looking for",
                "key_skills": ["skill1", "skill2", "skill3", ...],
                "experience_level": "Entry/Mid/Senior",
                "job_keywords": ["keyword1", "keyword2", ...],
                "industry": "Primary industry",
                "summary": "Brief professional summary"
            }}
            
            Resume text:
            {resume_text}
            
            Focus on:
            1. Technical skills mentioned
            2. Years of experience
            3. Previous job titles
            4. Education background
            5. Industry keywords
            
            Return only valid JSON, no additional text.
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert resume analyzer. Always respond with valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            result = json.loads(response.choices[0].message.content)
            logger.info(f"Resume analysis completed: {result['predicted_job_title']}")
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing resume: {str(e)}")
            return self._get_default_analysis()
    
    def score_job_relevance(self, resume_text: str, job_description: str, job_title: str) -> Dict[str, Any]:
        """
        Score how relevant a job is to the resume (0-100)
        """
        try:
            prompt = f"""
            Score how relevant this job is to the candidate's resume on a scale of 0-100.
            Also provide reasoning and missing requirements.
            
            Respond with JSON:
            {{
                "relevance_score": 85,
                "reasoning": "Why this job matches/doesn't match",
                "matched_skills": ["skill1", "skill2"],
                "missing_requirements": ["requirement1", "requirement2"],
                "recommendation": "Strong match/Good fit/Consider applying/Not recommended"
            }}
            
            Resume:
            {resume_text[:2000]}...
            
            Job Title: {job_title}
            Job Description:
            {job_description[:1500]}...
            
            Return only valid JSON.
            """
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert job matching AI. Always respond with valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=500
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            logger.error(f"Error scoring job relevance: {str(e)}")
            return {
                "relevance_score": 50,
                "reasoning": "Unable to analyze compatibility",
                "matched_skills": [],
                "missing_requirements": [],
                "recommendation": "Review manually"
            }
    
    def generate_job_insights(self, resume_analysis: Dict, jobs: List[Dict]) -> str:
        """
        Generate insights about the job search results
        """
        try:
            prompt = f"""
            Based on the resume analysis and job results, provide a brief insight message for the user.
            
            Resume Analysis: {json.dumps(resume_analysis)}
            Number of jobs found: {len(jobs)}
            
            Generate a professional, encouraging message (2-3 sentences) that:
            1. Acknowledges their background
            2. Highlights the relevance of found jobs
            3. Provides motivation
            
            Example: "Based on your background in [field], I've found [X] highly relevant opportunities that match your [skill] expertise. These positions align well with your [experience level] experience and could be excellent next steps in your career."
            """
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a career advisor providing encouraging insights."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=150
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error generating insights: {str(e)}")
            return "I've found several relevant job opportunities that match your profile!"
    
    def _get_default_analysis(self) -> Dict[str, Any]:
        """
        Fallback analysis if OpenAI fails
        """
        return {
            "predicted_job_title": "Software Developer",
            "key_skills": ["Programming", "Problem Solving"],
            "experience_level": "Mid",
            "job_keywords": ["developer", "software", "programming"],
            "industry": "Technology",
            "summary": "Experienced professional"
        }