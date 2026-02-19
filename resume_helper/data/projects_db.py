"""Load, validate, and filter the projects JSON database."""
import json
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


def filter_by_role_tag(projects: list, role_tag: str) -> list:
    """Return projects whose role_tags include role_tag.

    Raises ValueError if role_tag is not a recognised tag.
    """
    if role_tag not in ROLE_TAGS:
        valid = ", ".join(ROLE_TAGS)
        raise ValueError(f"Unknown role tag '{role_tag}'. Valid tags: {valid}")
    return [p for p in projects if role_tag in p.get("role_tags", [])]
