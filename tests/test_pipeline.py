import sys
import unittest
import tempfile
from pathlib import Path

# Add project root to python search path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.ingestion import clean_text, chunk_text, extract_metadata, DocumentParser
from src.vector_store import LocalVectorStore
from src.matcher import ResumeMatcher
from src.pipeline import ResumeMatchPipeline

class TestResumeMatchPipeline(unittest.TestCase):

    def test_clean_text(self):
        text = "Hello    World!   \n New Line\x00"
        cleaned = clean_text(text)
        self.assertEqual(cleaned, "Hello World! New Line")

    def test_chunk_text(self):
        text = "one two three four five six"
        chunks = chunk_text(text, chunk_size=3, chunk_overlap=1)
        self.assertEqual(len(chunks), 3)
        self.assertEqual(chunks[0], "one two three")
        self.assertEqual(chunks[1], "three four five")
        self.assertEqual(chunks[2], "five six")

    def test_extract_metadata(self):
        text = "My email is test@example.com and contact is 123-456-7890."
        meta = extract_metadata(text)
        self.assertEqual(meta["email"], "test@example.com")
        self.assertEqual(meta["phone"], "123-456-7890")

    def test_skill_extraction(self):
        text = "Experienced with Python, SQL, Docker, and AWS."
        skills = ResumeMatcher.extract_skills(text)
        self.assertTrue("python" in skills)
        self.assertTrue("sql" in skills)
        self.assertTrue("docker" in skills)
        self.assertTrue("aws" in skills)
        self.assertFalse("java" in skills)

    def test_end_to_end_pipeline(self):
        # Setup temporary store
        with tempfile.NamedTemporaryFile(suffix=".pkl", delete=False) as tmp_db:
            db_path = Path(tmp_db.name)
        
        try:
            store = LocalVectorStore(db_path=db_path)
            pipeline = ResumeMatchPipeline(vector_store=store)
            
            # Create a mock resume file
            resume_content = (
                "John Doe\njohn.doe@email.com\n"
                "Software Developer with 5 years experience in Python, Django, PostgreSQL, and AWS."
            )
            with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="w", encoding="utf-8") as tmp_resume:
                tmp_resume.write(resume_content)
                resume_path = Path(tmp_resume.name)
                
            try:
                # 1. Ingest Resume
                doc_id = pipeline.ingest_resume(resume_path)
                self.assertIsNotNone(doc_id)
                self.assertEqual(len(store.documents), 1)
                self.assertTrue(store.documents[0].startswith("John Doe"))
                
                # 2. Match Resumes
                jd = "Looking for a Python Developer who knows Django and AWS."
                results = pipeline.match_resumes(jd, top_k=1)
                
                self.assertEqual(len(results), 1)
                match = results[0]
                self.assertIsNotNone(match["candidate_name"])
                self.assertEqual(match["email"], "john.doe@email.com")
                self.assertTrue("python" in match["analysis"]["matched_skills"])
                self.assertTrue("django" in match["analysis"]["matched_skills"])
                self.assertGreater(match["analysis"]["match_score"], 0)
                
                # 3. Delete Resume
                deleted = pipeline.delete_resume(doc_id)
                self.assertTrue(deleted)
                self.assertEqual(len(store.documents), 0)
                
            finally:
                if resume_path.exists():
                    resume_path.unlink()
        finally:
            if db_path.exists():
                db_path.unlink()

if __name__ == '__main__':
    unittest.main()
