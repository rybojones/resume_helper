"""Load, validate, and filter the projects JSON database."""
import json
import re
from pathlib import Path

import jsonschema

ROLE_TAGS = [
    "data_scientist",
    "machine_learning_engineer",
    "analytics_engineer",
    "ai_engineer",
    "data_analyst",
    "data_engineer",
]

_PROJECT_SCHEMA = {
    "type": "object",
    "required": ["projects"],
    "properties": {
        "projects": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["id", "title", "summary", "skills", "role_tags", "impact"],
                "properties": {
                    "id":                  {"type": "string"},
                    "title":               {"type": "string"},
                    "organization":        {"type": "string"},
                    "dates": {
                        "type": "object",
                        "properties": {
                            "start": {"type": "string"},
                            "end":   {"type": "string"},
                        },
                    },
                    "summary":             {"type": "string"},
                    "description_long":    {"type": "string"},
                    "role":                {"type": "string"},
                    "skills":              {"type": "array", "items": {"type": "string"}},
                    "role_tags":           {
                        "type": "array",
                        "items": {"type": "string", "enum": ROLE_TAGS},
                        "minItems": 1,
                    },
                    "impact":              {"type": "array", "items": {"type": "string"}},
                    "keywords":            {"type": "array", "items": {"type": "string"}},
                    "include_by_default":  {"type": "boolean"},
                    "notes":               {"type": "string"},
                },
            },
        }
    },
}


def load_projects(path: str) -> list:
    """Load and validate projects.json. Returns the list of project dicts."""
    resolved = Path(path)
    if not resolved.exists():
        raise FileNotFoundError(f"Projects file not found: {resolved}")

    with resolved.open() as f:
        data = json.load(f)

    try:
        jsonschema.validate(data, _PROJECT_SCHEMA)
    except jsonschema.ValidationError as exc:
        raise ValueError(f"projects.json validation error: {exc.message}") from exc

    return data["projects"]


def merge_projects(existing: list, new_projects: list, projects_path: str) -> tuple[int, list]:
    """Deduplicate new_projects against existing and write the merged list to projects_path.

    Deduplication key: (title, organization) — case-insensitive.
    Auto-generates IDs for incoming projects that lack them.
    Returns (count_added, merged_list).
    """
    seen = {
        (_norm(p.get("title", "")), _norm(p.get("organization", "")))
        for p in existing
    }

    # Determine the next numeric suffix for ID generation
    next_id = _next_project_id(existing)

    added = 0
    merged = list(existing)
    for proj in new_projects:
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
