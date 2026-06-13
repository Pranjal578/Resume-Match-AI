import re
from typing import Dict, Any, List, Set
from src.logger import logger

# A curated set of common professional skills for comparison
COMMON_SKILLS = {
    # Programming Languages
    "python", "javascript", "typescript", "java", "c++", "c#", "ruby", "php", "go", "rust", "scala", "kotlin", "swift", "r", "sql", "html", "css",
    # Frameworks & Libraries
    "react", "angular", "vue", "django", "flask", "fastapi", "spring boot", "node.js", "next.js", "express", "rails", "numpy", "pandas", "scikit-learn", "tensorflow", "pytorch", "keras",
    # Cloud & DevOps
    "aws", "azure", "gcp", "docker", "kubernetes", "jenkins", "terraform", "ansible", "ci/cd", "git", "github", "gitlab", "linux", "bash",
    # Databases
    "postgresql", "mysql", "mongodb", "redis", "elasticsearch", "sqlite", "mariadb", "dynamodb", "cassandra", "oracle",
    # Concepts & Fields
    "machine learning", "deep learning", "natural language processing", "computer vision", "artificial intelligence", "data science", "data analysis", "software engineering", "web development", "devops", "cloud computing", "system design", "microservices", "agile", "scrum",
    # Tools & Soft Skills
    "jira", "confluence", "slack", "excel", "tableau", "power bi", "communication", "leadership", "mentoring", "problem solving", "collaboration", "project management"
}

class ResumeMatcher:
    """Compares a resume against a job description, computing matching metrics and skill gaps."""

    def __init__(self):
        pass

    @staticmethod
    def extract_skills(text: str) -> Set[str]:
        """Extracts known professional skills from a text using word boundary matching."""
        extracted = set()
        clean_text = text.lower()
        
        for skill in COMMON_SKILLS:
            # Match word boundary. Handle special cases like c++, c#, .net, node.js
            pattern = rf"\b{re.escape(skill)}\b"
            if "++" in skill or "#" in skill:
                pattern = rf"\b{re.escape(skill)}"
            
            if re.search(pattern, clean_text):
                extracted.add(skill)
                
        return extracted

    def analyze_match(self, resume_text: str, jd_text: str, semantic_similarity: float) -> Dict[str, Any]:
        """Analyzes matching elements between resume and JD, producing metrics and feedback."""
        logger.info("Analyzing match between resume and job description.")
        
        resume_skills = self.extract_skills(resume_text)
        jd_skills = self.extract_skills(jd_text)
        
        # Match/Gap computation
        matched_skills = resume_skills.intersection(jd_skills)
        missing_skills = jd_skills.difference(resume_skills)
        additional_skills = resume_skills.difference(jd_skills)
        
        # Scoring calculations
        skill_match_ratio = len(matched_skills) / len(jd_skills) if jd_skills else 1.0
        
        # Combined match score (weighting semantic similarity and skill overlap)
        # Scale to 0-100
        combined_score = (semantic_similarity * 0.6 + skill_match_ratio * 0.4) * 100
        combined_score = min(max(combined_score, 0.0), 100.0) # Ensure range is [0, 100]
        
        # Generate feedback comments
        strengths = []
        gaps = []
        recommendations = []
        
        # Strengths
        if matched_skills:
            strengths.append(f"Strong match for core skills: {', '.join(list(matched_skills)[:5])}.")
        if semantic_similarity > 0.6:
            strengths.append("High semantic alignment between your experiences and the job requirements.")
            
        # Gaps
        if missing_skills:
            gaps.append(f"Missing key skills listed in the JD: {', '.join(list(missing_skills)[:5])}.")
        else:
            strengths.append("Excellent alignment! You possess almost all identified key skills.")
            
        # Recommendations
        for skill in list(missing_skills)[:4]:
            recommendations.append(f"Consider highlighting your experience with or learning '{skill}'.")
        if len(resume_text.split()) < 150:
            recommendations.append("The resume seems brief. Expand on projects and work details.")
            
        return {
            "match_score": round(combined_score, 1),
            "semantic_similarity": round(semantic_similarity * 100, 1),
            "skill_match_ratio": round(skill_match_ratio * 100, 1),
            "matched_skills": sorted(list(matched_skills)),
            "missing_skills": sorted(list(missing_skills)),
            "additional_skills": sorted(list(additional_skills)),
            "strengths": strengths,
            "gaps": gaps,
            "recommendations": recommendations
        }
