from pathlib import Path
from typing import Dict, Any, List, Optional
import uuid
import numpy as np
from src.logger import logger
from src.ingestion import DocumentParser, clean_text, extract_metadata
from src.vector_store import LocalVectorStore
from src.matcher import ResumeMatcher
from src.config import UPLOAD_DIR

class ResumeMatchPipeline:
    """Orchestrates document ingestion, indexing, and matching against job descriptions."""

    def __init__(self, vector_store: Optional[LocalVectorStore] = None):
        self.parser = DocumentParser()
        self.vector_store = vector_store or LocalVectorStore()
        self.matcher = ResumeMatcher()

    def ingest_resume(self, file_path: str | Path) -> str:
        """Parses a resume, cleans it, extracts metadata, indexes it, and returns the document ID."""
        path = Path(file_path)
        logger.info(f"Ingesting resume file: {path.name}")
        
        # 1. Parse text
        raw_text = self.parser.parse(path)
        cleaned = clean_text(raw_text)
        
        # 2. Extract metadata
        metadata = extract_metadata(cleaned)
        metadata["filename"] = path.name
        
        # Determine candidate name from filename or default
        candidate_name = path.stem.replace("_", " ").replace("-", " ").title()
        metadata["candidate_name"] = candidate_name
        
        # 3. Save copy of uploaded resume to config uploads folder (if not already there)
        destination = UPLOAD_DIR / path.name
        if path.resolve() != destination.resolve():
            try:
                import shutil
                shutil.copy2(path, destination)
                metadata["stored_path"] = str(destination)
            except Exception as e:
                logger.warning(f"Could not copy file to storage directory: {e}")
                metadata["stored_path"] = str(path)
        else:
            metadata["stored_path"] = str(path)

        # Generate doc id or use filename
        doc_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, path.name))
        
        # 4. Add to Vector Store
        self.vector_store.add_documents(
            texts=[cleaned],
            metadatas=[metadata],
            ids=[doc_id]
        )
        
        logger.info(f"Successfully ingested resume: {candidate_name} (ID: {doc_id})")
        return doc_id

    def match_resumes(self, jd_text: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Matches all ingested resumes against the provided Job Description text."""
        logger.info("Starting matching pipeline.")
        cleaned_jd = clean_text(jd_text)
        
        if not self.vector_store.documents:
            logger.warning("No resumes found in the vector store. Ingest some resumes first.")
            return []
            
        # Search vector store for top candidates based on cosine similarity
        raw_search_results = self.vector_store.search(cleaned_jd, top_k=top_k)
        
        match_results = []
        for resume_text, metadata, similarity in raw_search_results:
            # Analyze match details
            analysis = self.matcher.analyze_match(resume_text, cleaned_jd, similarity)
            
            # Combine information
            match_results.append({
                "candidate_name": metadata.get("candidate_name", "Unknown Candidate"),
                "email": metadata.get("email"),
                "phone": metadata.get("phone"),
                "filename": metadata.get("filename"),
                "stored_path": metadata.get("stored_path"),
                "analysis": analysis
            })
            
        # Sort match results by overall match score descending
        match_results.sort(key=lambda x: x["analysis"]["match_score"], reverse=True)
        return match_results

    def delete_resume(self, doc_id: str) -> bool:
        """Deletes a resume from the vector store by ID."""
        if doc_id in self.vector_store.ids:
            idx = self.vector_store.ids.index(doc_id)
            
            # Delete stored file if it exists
            stored_path = self.vector_store.metadatas[idx].get("stored_path")
            if stored_path:
                try:
                    p = Path(stored_path)
                    if p.exists():
                        p.unlink()
                except Exception as e:
                    logger.error(f"Error deleting stored file {stored_path}: {e}")

            # Remove from vector store
            self.vector_store.documents.pop(idx)
            self.vector_store.metadatas.pop(idx)
            self.vector_store.ids.pop(idx)
            if self.vector_store.embeddings is not None:
                # Remove row from embeddings numpy array
                self.vector_store.embeddings = np.delete(self.vector_store.embeddings, idx, axis=0)
                if len(self.vector_store.embeddings) == 0:
                    self.vector_store.embeddings = None
                    
            self.vector_store.save()
            logger.info(f"Deleted resume ID {doc_id} from database.")
            return True
        return False
