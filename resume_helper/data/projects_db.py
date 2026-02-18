"""Load, validate, and filter the projects JSON database."""
import json
from pathlib import Path

import jsonschema

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
                    "role_tags":           {"type": "array", "items": {"type": "string"}},
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


def filter_by_role_tag(projects: list, role_tag: str) -> list:
    """Return projects whose role_tags include role_tag."""
    return [p for p in projects if role_tag in p.get("role_tags", [])]
