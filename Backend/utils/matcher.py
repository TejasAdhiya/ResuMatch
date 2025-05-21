from sklearn.feature_extraction.text import TfidfVectorizer, ENGLISH_STOP_WORDS
from sklearn.metrics.pairwise import cosine_similarity
import re

# Enhanced denylist and scoring parameters
GENERIC_KEYWORDS_DENYLIST = {
    "ability", "apply", "business", "candidate", "career", "communication",
    "company", "environment", "experience", "teamwork", "skills", "role",
    "work", "see", "use", "field", "tools", "interested", "knowledge",
    "make", "take", "give", "think", "need", "want", "show", "ensure",
    "team", "location", "fundamentals", "performance", "control",
    "help", "learn", "understanding", "working", "multiple"
}

TECH_KEYWORDS = {
    "python", "react", "javascript", "html", "css", "figma", "aws",
    "sql", "node", "angular", "vue", "docker", "kubernetes", "git",
    "typescript", "java", "c++", "php", "ruby", "swift", "kotlin"
}

def clean_text(text):
    text = text.lower()
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    return text

def extract_keywords(text):
    tokens = clean_text(text).split()
    keywords = [
        word for word in tokens
        if (word not in ENGLISH_STOP_WORDS
            and word not in GENERIC_KEYWORDS_DENYLIST
            and len(word) > 3)
    ]
    return set(keywords)

def calculate_keyword_importance(keywords, job_text):
    word_counts = {}
    for word in clean_text(job_text).split():
        if word in keywords:
            word_counts[word] = word_counts.get(word, 0) + 1
    return word_counts

def generate_ai_suggestion(matched_keywords, missing_keywords):
    sections = []
    
    if matched_keywords:
        tech_matched = [kw for kw in matched_keywords if kw in TECH_KEYWORDS]
        other_matched = [kw for kw in matched_keywords if kw not in TECH_KEYWORDS]
        
        strength_content = []
        if tech_matched:
            strength_content.append(f"Technical skills: {', '.join(tech_matched)}")
        if other_matched:
            strength_content.append(f"Other relevant terms: {', '.join(other_matched)}")
        
        if strength_content:
            sections.append("✨ STRENGTHS")
            sections.extend([f"• {item}" for item in strength_content])
            sections.append("")  # Empty line for spacing

    if missing_keywords:
        tech_missing = [kw for kw in missing_keywords if kw in TECH_KEYWORDS]
        other_missing = [kw for kw in missing_keywords if kw not in TECH_KEYWORDS]
        
        sections.append("🔍 IMPROVEMENTS")
        if tech_missing:
            sections.append(f"• Add technical skills: {', '.join(tech_missing[:5])}")
            sections.append("  Demonstrate through projects/certifications")
        if other_missing:
            sections.append(f"• Incorporate terms: {', '.join(other_missing[:3])}")
            sections.append("  Use naturally in experience bullet points")
        sections.append("")  # Empty line for spacing
    
    sections.append("💡 PRO TIP")
    sections.append("Use the STAR method (Situation-Task-Action-Result)")
    sections.append("to showcase keywords contextually")
    
    return '\n'.join(sections)

def calculate_match(resume_text: str, job_description: str):
    # Text processing
    resume_clean = clean_text(resume_text)
    jd_clean = clean_text(job_description)
    
    # Keyword extraction
    resume_keywords = extract_keywords(resume_text)
    job_keywords = extract_keywords(job_description)
    
    # Calculate keyword importance
    keyword_importance = calculate_keyword_importance(job_keywords, job_description)
    
    # Enhanced TF-IDF with tech keyword boost
    custom_stop_words = ENGLISH_STOP_WORDS.union(GENERIC_KEYWORDS_DENYLIST)
    vectorizer = TfidfVectorizer(stop_words=list(custom_stop_words))
    vectors = vectorizer.fit_transform([resume_clean, jd_clean])
    
    # Boost scores for technical keywords
    feature_names = vectorizer.get_feature_names_out()
    tech_boost = 1.5  # 50% score boost for technical terms
    
    for i, word in enumerate(feature_names):
        if word in TECH_KEYWORDS:
            vectors[1, i] *= tech_boost
    
    similarity_score = cosine_similarity(vectors[0:1], vectors[1:2])[0][0]
    
    # Adjust score based on important matches
    important_matches = [kw for kw in (resume_keywords & job_keywords) if kw in TECH_KEYWORDS]
    if important_matches:
        similarity_score = min(similarity_score * 1.3, 1.0)  # 30% boost for tech matches
    
    # Prepare keyword lists
    matched = sorted(list(resume_keywords & job_keywords))
    missing = sorted(
        list(job_keywords - resume_keywords),
        key=lambda x: keyword_importance.get(x, 0),
        reverse=True
    )
    
    return {
        "similarity_score": round(similarity_score * 100, 2),
        "matched_keywords": matched,
        "missing_keywords": missing[:15],
        "suggestion": generate_ai_suggestion(matched, missing)
    }