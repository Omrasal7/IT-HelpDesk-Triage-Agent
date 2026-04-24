from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
TICKETS_FILE = DATA_DIR / "tickets.json"
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.2"
REQUEST_TIMEOUT = 60
MAX_DESCRIPTION_CHARS = 4000
