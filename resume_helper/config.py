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

TEMPLATES_DIR = PROJECT_ROOT / "shared" / "templates"
DEFAULT_TEMPLATE = "project_focused_long"

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
    job_reqs_dir: Path


def resolve_user_paths(user: str | None = None) -> UserPaths:
    effective_user = user or os.getenv("RESUME_HELPER_USER", "").strip() or "jayne_dough"
    root = PROJECT_ROOT / "users" / effective_user
    return UserPaths(
        resume=root / "resumes" / "legacy" / "resume_default.pdf",
        projects=root / "projects.json",
        output_dir_md=root / "resumes" / "enhanced" / "md",
        output_dir_docx=root / "resumes" / "enhanced" / "docx",
        job_reqs_dir=root / "job_reqs",
    )


def resolve_template(name: str | None = None) -> tuple[str, Path]:
    """Return (system_prompt_text, pandoc_template_path) for the named template.

    Falls back to DEFAULT_TEMPLATE if name is None.
    Raises FileNotFoundError if the template directory or its required files are missing.
    """
    template_name = name or DEFAULT_TEMPLATE
    template_dir = TEMPLATES_DIR / template_name
    prompt_path = template_dir / "system_prompt.md"
    pandoc_path = template_dir / "pandoc_template.docx"

    if not template_dir.exists():
        raise FileNotFoundError(f"Template not found: '{template_name}' (looked in {TEMPLATES_DIR})")
    if not prompt_path.exists():
        raise FileNotFoundError(f"Template '{template_name}' is missing system_prompt.md")
    if not pandoc_path.exists():
        raise FileNotFoundError(f"Template '{template_name}' is missing pandoc_template.docx")

    return prompt_path.read_text(encoding="utf-8"), pandoc_path


def list_templates() -> list[str]:
    """Return sorted list of available template names."""
    if not TEMPLATES_DIR.exists():
        return []
    return sorted(p.name for p in TEMPLATES_DIR.iterdir() if p.is_dir())


def ensure_user_dirs(paths: UserPaths) -> None:
    """Create per-user output directories if they don't exist. Does not create projects.json."""
    paths.resume.parent.mkdir(parents=True, exist_ok=True)   # resumes/legacy/
    paths.output_dir_md.mkdir(parents=True, exist_ok=True)
    paths.output_dir_docx.mkdir(parents=True, exist_ok=True)
    paths.job_reqs_dir.mkdir(parents=True, exist_ok=True)
