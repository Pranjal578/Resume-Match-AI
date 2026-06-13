import pickle
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import numpy as np
from src.logger import logger
from src.config import DB_DIR, EMBEDDING_MODEL_NAME

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    logger.warning("sentence-transformers not installed. Falling back to TF-IDF representations.")

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.warning("scikit-learn not installed. Will use basic token-overlap matching if TF-IDF is needed.")


class TextEmbedder:
    """Computes embeddings using SentenceTransformers, or falls back to TF-IDF."""

    def __init__(self, model_name: str = EMBEDDING_MODEL_NAME):
        self.model_name = model_name
        self.model = None
        self.vectorizer = None
        self.is_semantic = False
        
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                logger.info(f"Loading SentenceTransformer model: {model_name}...")
                self.model = SentenceTransformer(model_name)
                self.is_semantic = True
                logger.info("SentenceTransformer loaded successfully.")
            except Exception as e:
                logger.error(f"Failed to load SentenceTransformer: {e}. Falling back to TF-IDF.")
        
        if not self.is_semantic:
            if SKLEARN_AVAILABLE:
                logger.info("Initializing TF-IDF Vectorizer...")
                self.vectorizer = TfidfVectorizer(stop_words="english")
            else:
                logger.warning("Neither SentenceTransformers nor scikit-learn is available. "
                               "Similarity matching will be extremely basic.")

    def embed_documents(self, texts: List[str]) -> np.ndarray:
        """Embeds a list of texts. Returns a numpy array of vectors."""
        if self.is_semantic and self.model:
            return self.model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
        elif self.vectorizer:
            # For TF-IDF, fit_transform needs to be done. We store representations differently.
            # However, for consistent API, we return the sparse matrix as array if fitted.
            # To handle dynamic queries later, we will handle TF-IDF logic in the store.
            return np.array([])
        else:
            return np.array([])


class LocalVectorStore:
    """Simple in-memory vector store that persists items to disk."""

    def __init__(self, db_path: Path = DB_DIR / "vector_store.pkl"):
        self.db_path = db_path
        self.embedder = TextEmbedder()
        
        # Internal storage
        self.documents: List[str] = []
        self.metadatas: List[Dict[str, Any]] = []
        self.ids: List[str] = []
        self.embeddings: Optional[np.ndarray] = None
        
        # Load existing store if available
        self.load()

    def add_documents(self, texts: List[str], metadatas: List[Dict[str, Any]], ids: List[str]):
        """Adds documents, computes their embeddings, and saves the database."""
        if not texts:
            return
            
        logger.info(f"Adding {len(texts)} documents to vector store.")
        
        # Validate input lengths
        assert len(texts) == len(metadatas) == len(ids), "Inputs must have the same length."
        
        new_embeddings = None
        if self.embedder.is_semantic:
            new_embeddings = self.embedder.embed_documents(texts)
        
        for idx, (text, metadata, doc_id) in enumerate(zip(texts, metadatas, ids)):
            if doc_id in self.ids:
                # Replace existing
                existing_idx = self.ids.index(doc_id)
                self.documents[existing_idx] = text
                self.metadatas[existing_idx] = metadata
                if new_embeddings is not None and self.embeddings is not None:
                    self.embeddings[existing_idx] = new_embeddings[idx]
            else:
                # Append new
                self.documents.append(text)
                self.metadatas.append(metadata)
                self.ids.append(doc_id)
                if new_embeddings is not None:
                    if self.embeddings is None:
                        self.embeddings = np.array([new_embeddings[idx]])
                    else:
                        self.embeddings = np.vstack([self.embeddings, new_embeddings[idx]])
        
        # Re-fit TF-IDF if using TF-IDF
        if not self.embedder.is_semantic and self.embedder.vectorizer:
            try:
                self.embedder.vectorizer.fit(self.documents)
            except Exception as e:
                logger.error(f"Error fitting TF-IDF: {e}")
                
        self.save()

    def search(self, query: str, top_k: int = 5) -> List[Tuple[str, Dict[str, Any], float]]:
        """Searches for documents similar to the query."""
        if not self.documents:
            return []
            
        top_k = min(top_k, len(self.documents))
        
        if self.embedder.is_semantic and self.embeddings is not None:
            # Compute query embedding
            query_vector = self.embedder.embed_documents([query])[0]
            
            # Normalize vectors
            query_norm = query_vector / (np.linalg.norm(query_vector) + 1e-9)
            doc_norms = self.embeddings / (np.linalg.norm(self.embeddings, axis=1, keepdims=True) + 1e-9)
            
            # Cosine similarity
            similarities = np.dot(doc_norms, query_norm)
            
            # Get top indices
            top_indices = np.argsort(similarities)[::-1][:top_k]
            
            results = []
            for idx in top_indices:
                results.append((
                    self.documents[idx],
                    self.metadatas[idx],
                    float(similarities[idx])
                ))
            return results
            
        elif self.embedder.vectorizer:
            # TF-IDF Cosine Similarity
            query_tfidf = self.embedder.vectorizer.transform([query])
            docs_tfidf = self.embedder.vectorizer.transform(self.documents)
            
            similarities = cosine_similarity(docs_tfidf, query_tfidf).flatten()
            top_indices = np.argsort(similarities)[::-1][:top_k]
            
            results = []
            for idx in top_indices:
                results.append((
                    self.documents[idx],
                    self.metadatas[idx],
                    float(similarities[idx])
                ))
            return results
        else:
            # Standard Jaccard / word overlap fallback
            logger.warning("Using basic word overlap similarity search.")
            query_words = set(query.lower().split())
            results = []
            
            for idx, doc in enumerate(self.documents):
                doc_words = set(doc.lower().split())
                intersection = query_words.intersection(doc_words)
                union = query_words.union(doc_words)
                similarity = len(intersection) / len(union) if union else 0.0
                results.append((doc, self.metadatas[idx], similarity))
                
            # Sort by similarity
            results.sort(key=lambda x: x[2], reverse=True)
            return results[:top_k]

    def save(self):
        """Saves store data to db_path."""
        try:
            # Custom pickling of state
            data = {
                "documents": self.documents,
                "metadatas": self.metadatas,
                "ids": self.ids,
                "embeddings": self.embeddings,
            }
            with open(self.db_path, "wb") as f:
                pickle.dump(data, f)
            logger.info(f"Vector store saved successfully to {self.db_path}.")
        except Exception as e:
            logger.error(f"Failed to save vector store: {e}")

    def load(self):
        """Loads store data from db_path."""
        if not self.db_path.exists():
            logger.info("No existing vector store found. Starting with an empty database.")
            return
            
        try:
            with open(self.db_path, "rb") as f:
                data = pickle.load(f)
            self.documents = data.get("documents", [])
            self.metadatas = data.get("metadatas", [])
            self.ids = data.get("ids", [])
            self.embeddings = data.get("embeddings", None)
            
            # Re-fit TF-IDF vectorizer if relevant
            if not self.embedder.is_semantic and self.embedder.vectorizer and self.documents:
                self.embedder.vectorizer.fit(self.documents)
                
            logger.info(f"Loaded {len(self.documents)} documents from vector store.")
        except Exception as e:
            logger.error(f"Error loading vector store: {e}. Starting fresh.")
