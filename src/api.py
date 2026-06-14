"""FastAPI backend for Resume Match AI."""

import sys
from pathlib import Path
from typing import List, Optional
import tempfile
import os
from datetime import datetime

# Add project root to python search path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn
from src.pipeline import ResumeMatchPipeline
from src.vector_store import LocalVectorStore
from src.config import UPLOAD_DIR, LOG_DIR
from src.logger import setup_logger

# Initialize logger
logger = setup_logger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Resume Match AI API",
    description="AI-powered resume parsing and job matching service",
    version="1.0.0"
)

# Add CORS middleware to allow mobile app connections
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize pipeline and vector store
pipeline = ResumeMatchPipeline()
vector_store = LocalVectorStore()

# ==================== Pydantic Models ====================

class SkillAnalysis(BaseModel):
    """Skill analysis for a resume."""
    matching_skills: List[str] = Field(..., description="Skills that match the job description")
    missing_skills: List[str] = Field(..., description="Skills required but missing from resume")
    additional_skills: List[str] = Field(..., description="Additional relevant skills found in resume")


class ResumeMatchResult(BaseModel):
    """Result of matching a resume against a job description."""
    resume_name: str = Field(..., description="Name of the uploaded resume")
    match_score: float = Field(..., ge=0, le=100, description="Match score as percentage (0-100)")
    skill_analysis: SkillAnalysis
    key_strengths: List[str] = Field(..., description="Key strengths of the candidate")
    recommendations: List[str] = Field(..., description="Recommendations for improvement")
    timestamp: str = Field(..., description="ISO format timestamp")


class BatchMatchResults(BaseModel):
    """Results of matching multiple resumes."""
    job_description: str = Field(..., description="The job description used for matching")
    matches: List[ResumeMatchResult]
    top_match: Optional[ResumeMatchResult] = Field(None, description="The highest scoring match")


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")


# ==================== Health & Info Endpoints ====================

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Check if the API is running."""
    return {
        "status": "healthy",
        "version": "1.0.0"
    }


@app.get("/info")
async def get_info():
    """Get information about the service capabilities."""
    return {
        "service": "Resume Match AI API",
        "capabilities": [
            "Resume ingestion (PDF, DOCX, TXT)",
            "Semantic similarity matching",
            "Skill gap analysis",
            "Resume batch processing",
            "Vector store management"
        ],
        "supported_formats": ["pdf", "docx", "txt"],
        "max_file_size_mb": 10
    }


# ==================== Resume Ingestion Endpoints ====================

@app.post("/resumes/upload")
async def upload_resume(file: UploadFile = File(...)) -> dict:
    """
    Upload and ingest a resume file.
    
    Supported formats: PDF, DOCX, TXT
    """
    try:
        # Validate file extension
        allowed_extensions = {".pdf", ".docx", ".txt", ".doc"}
        file_ext = Path(file.filename).suffix.lower()
        
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file format: {file_ext}. Allowed: {', '.join(allowed_extensions)}"
            )
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_file:
            contents = await file.read()
            tmp_file.write(contents)
            tmp_path = tmp_file.name
        
        try:
            # Ingest resume using pipeline
            resume_text = pipeline.ingest_resume(tmp_path)
            
            # Add to vector store
            resume_id = pipeline.vectorize_resume(resume_text, file.filename)
            
            logger.info(f"Successfully ingested resume: {file.filename}")
            
            return {
                "status": "success",
                "resume_name": file.filename,
                "resume_id": resume_id,
                "characters": len(resume_text),
                "message": "Resume uploaded and indexed successfully"
            }
        
        finally:
            # Clean up temporary file
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading resume: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing resume: {str(e)}")


@app.get("/resumes/list")
async def list_resumes() -> dict:
    """Get list of all ingested resumes."""
    try:
        resumes = vector_store.list_resumes()
        return {
            "total": len(resumes),
            "resumes": resumes
        }
    except Exception as e:
        logger.error(f"Error listing resumes: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error listing resumes: {str(e)}")


@app.delete("/resumes/{resume_id}")
async def delete_resume(resume_id: str) -> dict:
    """Delete a resume from the vector store."""
    try:
        vector_store.delete_resume(resume_id)
        logger.info(f"Deleted resume: {resume_id}")
        return {
            "status": "success",
            "message": f"Resume {resume_id} deleted successfully"
        }
    except Exception as e:
        logger.error(f"Error deleting resume: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting resume: {str(e)}")


# ==================== Matching Endpoints ====================

@app.post("/match/single", response_model=ResumeMatchResult)
async def match_single_resume(
    resume_id: str,
    job_description: str
) -> ResumeMatchResult:
    """
    Match a single resume against a job description.
    
    Args:
        resume_id: ID of the resume to match
        job_description: The job description to match against
    
    Returns:
        ResumeMatchResult with match score and analysis
    """
    try:
        # Get resume from vector store
        resume_data = vector_store.get_resume(resume_id)
        if not resume_data:
            raise HTTPException(status_code=404, detail=f"Resume not found: {resume_id}")
        
        # Perform matching
        result = pipeline.match_resume_to_job(
            resume_data["text"],
            job_description,
            resume_data["filename"]
        )
        
        logger.info(f"Matched resume {resume_id} against job description")
        
        return ResumeMatchResult(
            resume_name=resume_data["filename"],
            match_score=result["match_score"],
            skill_analysis=SkillAnalysis(
                matching_skills=result["matching_skills"],
                missing_skills=result["missing_skills"],
                additional_skills=result["additional_skills"]
            ),
            key_strengths=result["key_strengths"],
            recommendations=result["recommendations"],
            timestamp=datetime.now().isoformat()
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error matching resume: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error matching resume: {str(e)}")


@app.post("/match/batch", response_model=BatchMatchResults)
async def match_batch_resumes(job_description: str) -> BatchMatchResults:
    """
    Match all resumes in the vector store against a job description.
    
    Args:
        job_description: The job description to match against
    
    Returns:
        BatchMatchResults with all matches sorted by score
    """
    try:
        resumes = vector_store.list_resumes()
        
        if not resumes:
            raise HTTPException(status_code=400, detail="No resumes in the vector store")
        
        matches = []
        
        for resume_id, resume_data in resumes.items():
            try:
                result = pipeline.match_resume_to_job(
                    resume_data["text"],
                    job_description,
                    resume_data["filename"]
                )
                
                match_result = ResumeMatchResult(
                    resume_name=resume_data["filename"],
                    match_score=result["match_score"],
                    skill_analysis=SkillAnalysis(
                        matching_skills=result["matching_skills"],
                        missing_skills=result["missing_skills"],
                        additional_skills=result["additional_skills"]
                    ),
                    key_strengths=result["key_strengths"],
                    recommendations=result["recommendations"],
                    timestamp=datetime.now().isoformat()
                )
                matches.append(match_result)
            
            except Exception as e:
                logger.warning(f"Error matching resume {resume_id}: {str(e)}")
                continue
        
        # Sort by match score (descending)
        matches.sort(key=lambda x: x.match_score, reverse=True)
        
        logger.info(f"Batch matched {len(matches)} resumes against job description")
        
        return BatchMatchResults(
            job_description=job_description,
            matches=matches,
            top_match=matches[0] if matches else None
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in batch matching: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in batch matching: {str(e)}")


# ==================== Vector Store Management ====================

@app.post("/vector-store/rebuild")
async def rebuild_vector_store(background_tasks: BackgroundTasks) -> dict:
    """
    Rebuild the vector store. This is a long-running operation.
    """
    try:
        background_tasks.add_task(vector_store.rebuild)
        logger.info("Vector store rebuild initiated")
        return {
            "status": "rebuilding",
            "message": "Vector store rebuild started in background"
        }
    except Exception as e:
        logger.error(f"Error rebuilding vector store: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error rebuilding vector store: {str(e)}")


@app.get("/vector-store/stats")
async def get_vector_store_stats() -> dict:
    """Get statistics about the vector store."""
    try:
        stats = vector_store.get_stats()
        return stats
    except Exception as e:
        logger.error(f"Error getting vector store stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting stats: {str(e)}")


# ==================== Server Startup ====================

if __name__ == "__main__":
    uvicorn.run(
        "src.api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
