from pathlib import Path

# Base directory of the project (root of the workspace)
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Data paths
PROCESSED_DATA_PATH = BASE_DIR / "processed_data.json"
CHROMA_DB_PATH = BASE_DIR / "chroma_db"

# RAG configuration
MAX_CONTEXT_TOKENS = 3000
MAX_RESULTS = 10
MIN_RELEVANCE_SCORE = 0.5
