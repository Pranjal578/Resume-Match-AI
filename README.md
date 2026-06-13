# Resume Match AI

An intelligent resume parser, semantic search index, and job matching analyzer application. Upload resumes, paste a Job Description, and view alignment scores, skill classifications, key strengths, and recommendations in an elegant web interface.

---

## Features

- **Multi-Format Ingestion:** Extracts and normalizes text from PDF, DOCX, and TXT resume formats.
- **Dual Similarity Engines:** Computes semantic matching using localized SentenceTransformers (`all-MiniLM-L6-v2`) with a robust fallback to TF-IDF cosine similarity or token overlap matching if deep learning packages are absent.
- **Skill Gap & Alignment Analysis:** Identifies matching keywords/skills, highlights missing requirements, and lists additional related skills from candidates.
- **Granular Recommendations:** Provides custom bulleted reports highlighting candidates' key strengths, critical skill gaps, and CV expansion tips.
- **Stunning Frontend UI:** Clean dark-themed, glassmorphic Streamlit application containing interactive resume cataloging, delete actions, dynamic alignment metrics, and expandable breakdowns.
- **Robust Environmental Configuration:** Managed through a localized `.env` configuration template.

---

## Project Structure

```text
resume-match-ai/
│
├── data/                      # Local file database (git-ignored)
│   ├── db/                    # Persisted local vector store
│   └── uploads/               # Extracted and copied resume files
│
├── src/
│   ├── __init__.py            # Module initialization
│   ├── app.py                 # Streamlit UI application
│   ├── config.py              # Environment and path configurations
│   ├── ingestion.py           # File readers, cleansers, and detail extractors
│   ├── logger.py              # Rotating file and stdout logger setups
│   ├── matcher.py             # Keyword checks and feedback generator
│   ├── pipeline.py            # Workflow controller (Ingest -> Vectorize -> Match)
│   └── vector_store.py        # Local vector DB (Semantic / TF-IDF representations)
│
├── tests/
│   ├── __init__.py
│   └── test_pipeline.py       # Built-in verification test suite
│
├── .env                       # Local configurations (git-ignored)
├── .gitignore                 # Version control rules
├── requirements.txt           # Required python dependencies
└── README.md                  # Project documentation
```

---

## 🚀 Getting Started

Follow these steps to run the application on your local machine:

### 1. Set Up Your Environment

Ensure Python 3.8+ is installed on your system. Navigate to the project root and set up a virtual environment:

```bash
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows (Command Prompt)
venv\Scripts\activate
# On Windows (PowerShell)
.\venv\Scripts\activate
# On Linux / macOS
source venv/bin/activate
```

### 2. Install Project Dependencies

Install the required packages listed in `requirements.txt`:

```bash
pip install -r requirements.txt
```

### 3. Initialize Configurations

A local `.env` configuration file has been created at the root level of the project. You can edit this file to configure the application (e.g. changing the chunk size or adjusting the similarity thresholds):

```ini
APP_NAME="Resume Match AI"
EMBEDDING_MODEL_NAME="all-MiniLM-L6-v2"
CHUNK_SIZE=1000
CHUNK_OVERLAP=100
MATCH_THRESHOLD=0.3
```

### 4. Running the Tests

Verify the pipeline and components are working correctly using Python's standard `unittest` library:

```bash
python -m unittest tests/test_pipeline.py
```

### 5. Running the Streamlit Web App

Launch the Streamlit web dashboard:

```bash
streamlit run src/app.py
```

Open `http://localhost:8501` in your browser to start matching resumes!
