from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
TEMPLATES_DIR = BASE_DIR / "app" / "templates"
STATIC_DIR = BASE_DIR / "app" / "static"
SYSTEM_PROMPT_FILE = BASE_DIR / "system prompt.txt"
