"""Load, validate, and filter the projects JSON database."""
import json
import re
from pathlib import Path

from pydantic import ValidationError

from resume_helper.models import ROLE_TAGS, ProjectsFile


def load_projects(path: str) -> list:
    """Load and validate projects.json. Returns the list of project dicts."""
    resolved = Path(path)
    if not resolved.exists():
        raise FileNotFoundError(f"Projects file not found: {resolved}")

    with resolved.open() as f:
        data = json.load(f)

    try:
        validated = ProjectsFile.model_validate(data)
    except ValidationError as exc:
        raise ValueError(f"projects.json validation error: {exc}") from exc

    return [p.model_dump() for p in validated.projects]


def merge_projects(existing: list, new_projects: list, projects_path: str) -> tuple[int, list]:
    """Deduplicate new_projects against existing and write the merged list to projects_path.

    Deduplication key: (title, organization) — case-insensitive.
    Auto-generates IDs for incoming projects that lack them.
    Accepts new_projects as dicts or ProjectRecord instances.
    Returns (count_added, merged_list).
    """
    # Normalize ProjectRecord instances to dicts
    normalized = [
        p.model_dump() if hasattr(p, "model_dump") else p
        for p in new_projects
    ]

    seen = {
        (_norm(p.get("title", "")), _norm(p.get("organization", "")))
        for p in existing
    }

    # Determine the next numeric suffix for ID generation
    next_id = _next_project_id(existing)

    added = 0
    merged = list(existing)
    for proj in normalized:
        key = (_norm(proj.get("title", "")), _norm(proj.get("organization", "")))
        if key in seen:
            continue
        # Assign an ID if the LLM didn't provide one
        if not proj.get("id"):
            proj["id"] = f"proj_{next_id:03d}"
            next_id += 1
        # Ensure required fields have at least an empty default so schema passes
        proj.setdefault("summary", "")
        proj.setdefault("skills", [])
        proj.setdefault("role_tags", [])
        proj.setdefault("impact", [])
        merged.append(proj)
        seen.add(key)
        added += 1

    resolved = Path(projects_path)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    with resolved.open("w", encoding="utf-8") as f:
        json.dump({"projects": merged}, f, indent=2, ensure_ascii=False)
        f.write("\n")

    return added, merged


def _norm(s: str) -> str:
    return s.strip().lower()


def _next_project_id(projects: list) -> int:
    """Return the next integer suffix to use for auto-generated project IDs."""
    max_n = 0
    for p in projects:
        pid = p.get("id", "")
        m = re.search(r"(\d+)$", pid)
        if m:
            max_n = max(max_n, int(m.group(1)))
    return max_n + 1


def filter_by_role_tag(projects: list, role_tag: str) -> list:
    """Return projects whose role_tags include role_tag.

    Raises ValueError if role_tag is not a recognised tag.
    """
    if role_tag not in ROLE_TAGS:
        valid = ", ".join(ROLE_TAGS)
        raise ValueError(f"Unknown role tag '{role_tag}'. Valid tags: {valid}")
    return [p for p in projects if role_tag in p.get("role_tags", [])]
