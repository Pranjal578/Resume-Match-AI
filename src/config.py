import os
from pathlib import Path

# Paths
SRC_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SRC_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
DB_DIR = DATA_DIR / "db"
LOG_DIR = PROJECT_ROOT / "logs"

# Ensure directories exist
for directory in [DATA_DIR, UPLOAD_DIR, DB_DIR, LOG_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# App configurations
try:
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env")
except ImportError:
    pass

APP_NAME = os.getenv("APP_NAME", "Resume Match AI")

# Embeddings & Matching configurations
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2")

# Ingestion settings
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1000"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "100"))

# Similarity threshold for matching
MATCH_THRESHOLD = float(os.getenv("MATCH_THRESHOLD", "0.3"))
