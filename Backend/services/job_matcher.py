import logging
import re
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class JobMatcher:
    def __init__(self, openai_service):
        self.openai_service = openai_service
    
    def rank_jobs(self, resume_text: str, jobs: List[Dict], top_n: int = 5) -> List[Dict]:
        """
        Rank jobs based on resume match using OpenAI and simple text matching
        """
        if not jobs:
            return []
        
        try:
            # Extract key info from resume
            resume_keywords = self._extract_keywords(resume_text.lower())
            
            scored_jobs = []
            
            for job in jobs:
                try:
                    # Calculate match score
                    match_score = self._calculate_match_score(resume_text, job, resume_keywords)
                    
                    # Add score to job
                    job_with_score = job.copy()
                    job_with_score['match_score'] = match_score
                    job_with_score['match_percentage'] = f"{match_score}%"
                    
                    # Only include jobs with decent match (above 30%)
                    if match_score >= 30:
                        scored_jobs.append(job_with_score)
                    
                except Exception as e:
                    logger.warning(f"Error scoring job {job.get('title', 'Unknown')}: {e}")
                    continue
            
            # Sort by match score (highest first)
            scored_jobs.sort(key=lambda x: x['match_score'], reverse=True)
            
            # Return top N jobs
            return scored_jobs[:top_n]
            
        except Exception as e:
            logger.error(f"Error ranking jobs: {e}")
            return jobs[:top_n]  # Return first N jobs as fallback
    
    def _calculate_match_score(self, resume_text: str, job: Dict, resume_keywords: set) -> int:
        """
        Calculate match score between resume and job (0-100)
        """
        try:
            job_text = f"{job.get('title', '')} {job.get('description', '')} {job.get('requirements', '')}".lower()
            job_keywords = self._extract_keywords(job_text)
            
            # Basic keyword matching
            common_keywords = resume_keywords.intersection(job_keywords)
            keyword_score = min(len(common_keywords) * 10, 50)  # Max 50 points
            
            # Title matching
            title_score = self._calculate_title_match(resume_text, job.get('title', ''))
            
            # Skills matching
            skills_score = self._calculate_skills_match(resume_text, job_text)
            
            # Experience level matching
            exp_score = self._calculate_experience_match(resume_text, job_text)
            
            # Combine scores
            total_score = min(keyword_score + title_score + skills_score + exp_score, 100)
            
            return max(total_score, 1)  # Minimum score of 1
            
        except Exception as e:
            logger.warning(f"Error calculating match score: {e}")
            return 50  # Default moderate score
    
    def _extract_keywords(self, text: str) -> set:
        """
        Extract relevant keywords from text
        """
        # Common tech skills and job-related keywords
        tech_keywords = {
            'python', 'java', 'javascript', 'react', 'angular', 'vue', 'node', 'django',
            'flask', 'spring', 'hibernate', 'sql', 'mysql', 'postgresql', 'mongodb',
            'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'jenkins', 'git', 'github',
            'html', 'css', 'bootstrap', 'jquery', 'typescript', 'php', 'laravel',
            'c++', 'c#', 'golang', 'rust', 'swift', 'kotlin', 'dart', 'flutter',
            'machine learning', 'ai', 'data science', 'analytics', 'tableau', 'powerbi',
            'excel', 'pandas', 'numpy', 'tensorflow', 'pytorch', 'scikit-learn',
            'api', 'rest', 'graphql', 'microservices', 'devops', 'ci/cd', 'testing',
            'agile', 'scrum', 'project management', 'leadership', 'communication'
        }
        
        # Extract words from text
        words = re.findall(r'\b[a-z]+\b', text.lower())
        
        # Filter relevant keywords
        found_keywords = set()
        for word in words:
            if word in tech_keywords or len(word) > 3:
                found_keywords.add(word)
        
        # Also look for multi-word skills
        for skill in tech_keywords:
            if skill in text:
                found_keywords.add(skill.replace(' ', '_'))
        
        return found_keywords
    
    def _calculate_title_match(self, resume_text: str, job_title: str) -> int:
        """
        Calculate how well job title matches resume (0-25 points)
        """
        if not job_title:
            return 0
        
        resume_lower = resume_text.lower()
        title_lower = job_title.lower()
        
        # Common job titles
        job_titles = [
            'developer', 'engineer', 'analyst', 'manager', 'consultant',
            'specialist', 'coordinator', 'associate', 'senior', 'junior',
            'lead', 'principal', 'architect', 'designer', 'tester'
        ]
        
        score = 0
        title_words = title_lower.split()
        
        for word in title_words:
            if word in resume_lower:
                score += 5
                
        for title in job_titles:
            if title in title_lower and title in resume_lower:
                score += 10
                
        return min(score, 25)
    
    def _calculate_skills_match(self, resume_text: str, job_text: str) -> int:
        """
        Calculate skills matching (0-15 points)
        """
        common_skills = [
            'communication', 'teamwork', 'leadership', 'problem solving',
            'analytical', 'creative', 'detail oriented', 'time management',
            'customer service', 'sales', 'marketing', 'finance', 'accounting'
        ]
        
        score = 0
        resume_lower = resume_text.lower()
        job_lower = job_text.lower()
        
        for skill in common_skills:
            if skill in resume_lower and skill in job_lower:
                score += 3
                
        return min(score, 15)
    
    def _calculate_experience_match(self, resume_text: str, job_text: str) -> int:
        """
        Calculate experience level matching (0-10 points)
        """
        exp_levels = {
            'entry': ['entry', 'junior', 'associate', 'fresher', 'graduate'],
            'mid': ['mid', 'intermediate', 'experienced', '2-5 years'],
            'senior': ['senior', 'lead', 'principal', 'manager', '5+ years']
        }
        
        resume_lower = resume_text.lower()
        job_lower = job_text.lower()
        
        resume_level = None
        job_level = None
        
        # Determine resume experience level
        for level, keywords in exp_levels.items():
            if any(keyword in resume_lower for keyword in keywords):
                resume_level = level
                break
        
        # Determine job experience level
        for level, keywords in exp_levels.items():
            if any(keyword in job_lower for keyword in keywords):
                job_level = level
                break
        
        # Match levels
        if resume_level and job_level:
            if resume_level == job_level:
                return 10
            elif abs(['entry', 'mid', 'senior'].index(resume_level) - 
                    ['entry', 'mid', 'senior'].index(job_level)) == 1:
                return 5
        
        return 3  # Default small score