from sklearn.feature_extraction.text import TfidfVectorizer, ENGLISH_STOP_WORDS
from sklearn.metrics.pairwise import cosine_similarity
import re

# Clean and normalize text
def clean_text(text):
    text = text.lower()
    text = re.sub(r'[^a-zA-Z\s]', '', text)  # Remove punctuation/numbers
    return text

# Extract keywords by removing stopwords and short words
def extract_keywords(text):
    tokens = clean_text(text).split()
    keywords = [word for word in tokens if word not in ENGLISH_STOP_WORDS and len(word) > 2]
    return set(keywords)

# Calculate similarity and keyword match
def calculate_match(resume_text: str, job_description: str):
    resume_text_clean = clean_text(resume_text)
    job_description_clean = clean_text(job_description)

    # TF-IDF + Cosine Similarity
    vectorizer = TfidfVectorizer()
    vectors = vectorizer.fit_transform([resume_text_clean, job_description_clean])
    similarity_score = cosine_similarity(vectors[0:1], vectors[1:2])[0][0]

    # Extract filtered keywords
    resume_keywords = extract_keywords(resume_text)
    job_keywords = extract_keywords(job_description)

    matched = sorted(list(resume_keywords & job_keywords))
    missing = sorted(list(job_keywords - resume_keywords))

    return {
        "similarity_score": round(similarity_score * 100, 2),
        "matched_keywords": matched,
        "missing_keywords": missing,
        "suggestion": f"Consider including keywords like: {', '.join(missing[:5])}" if missing else "Resume looks good!"
    }

