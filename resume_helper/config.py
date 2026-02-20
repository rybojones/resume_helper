"""Central defaults and environment variable loading."""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Resolve project root as the directory two levels up from this file
PROJECT_ROOT = Path(__file__).parent.parent

DEFAULT_RESUME_PATH = PROJECT_ROOT / "resumes" / "legacy" / "resume_default.pdf"
DEFAULT_PROJECTS_PATH = PROJECT_ROOT / "data" / "projects.json"
OUTPUT_DIR = PROJECT_ROOT / "resumes" / "enhanced"
OUTPUT_DIR_MD   = OUTPUT_DIR / "md"
OUTPUT_DIR_DOCX = OUTPUT_DIR / "docx"
DEFAULT_REFERENCE_DOCX = PROJECT_ROOT / "resumes" / "legacy" / "resume_template.docx"

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
DEFAULT_PROVIDER = "gemini"

# Default maximum number of tokens
MAX_TOKENS = 4096