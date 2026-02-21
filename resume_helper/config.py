"""Central defaults and environment variable loading."""
import os
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Resolve project root as the directory two levels up from this file
PROJECT_ROOT = Path(__file__).parent.parent

DEFAULT_RESUME_PATH = PROJECT_ROOT / "users" / "jayne_dough" / "resumes" / "legacy" / "resume_default.pdf"
DEFAULT_PROJECTS_PATH = PROJECT_ROOT / "users" / "jayne_dough" / "projects.json"
OUTPUT_DIR = PROJECT_ROOT / "users" / "jayne_dough" / "resumes" / "enhanced"
OUTPUT_DIR_MD   = OUTPUT_DIR / "md"
OUTPUT_DIR_DOCX = OUTPUT_DIR / "docx"
DEFAULT_REFERENCE_DOCX = PROJECT_ROOT / "shared" / "pandoc_template.docx"

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
DEFAULT_PROVIDER = "gemini"

# Default maximum number of tokens
MAX_TOKENS = 4096


@dataclass
class UserPaths:
    resume: Path
    projects: Path
    output_dir_md: Path
    output_dir_docx: Path


def resolve_user_paths(user: str | None = None) -> UserPaths:
    effective_user = user or os.getenv("RESUME_HELPER_USER", "").strip() or "jayne_dough"
    root = PROJECT_ROOT / "users" / effective_user
    return UserPaths(
        resume=root / "resumes" / "legacy" / "resume_default.pdf",
        projects=root / "projects.json",
        output_dir_md=root / "resumes" / "enhanced" / "md",
        output_dir_docx=root / "resumes" / "enhanced" / "docx",
    )
