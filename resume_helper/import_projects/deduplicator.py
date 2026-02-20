"""LLM-based duplicate detection and merging for import_projects."""
import json

from resume_helper.models import DuplicateMatch, MergedProjectText, ProjectRecord

_MATCH_SYSTEM_PROMPT = """\
You are a deduplication assistant for a projects database. Given a new project and a list of \
existing projects (each with an id, title, and summary), determine whether the new project \
describes the same real-world work as any existing project.

Two projects are the same if they refer to the same initiative, system, or body of work — \
even if the title is worded differently, the organization differs, or the description emphasises \
different aspects.

Return:
  - matched_id: the id of the matching existing project, or an empty string if there is no match
  - reason: a brief explanation of your decision
"""

_MERGE_SYSTEM_PROMPT = """\
You are merging two descriptions of the same project into a single, richer record.
Given the existing summary and description, and a new summary and description for the same project, \
write a consolidated version that captures the best detail from both without inventing new facts.

Return:
  - summary: a 1-2 sentence summary (concise, clear)
  - description_long: a comprehensive paragraph combining the strongest details from both versions
"""


def resolve_duplicates(
    existing: list[dict],
    new_projects: list[ProjectRecord],
    llm,
) -> tuple[list, list[dict]]:
    """Compare each new project against all existing ones using the LLM.

    For each new project:
      - One LLM call checks for a match among all existing projects.
      - On confirmed match: a second LLM call synthesizes a merged summary and description_long.
      - Unmatched projects are returned as truly_new.

    Returns:
        truly_new        — ProjectRecords with no match (pass to merge_projects as-is)
        updated_existing — existing list with matched records merged in-place
    """
    if not existing:
        return list(new_projects), []

    # Compact reference sent to the LLM on every comparison call
    existing_refs = [
        {"id": p["id"], "title": p["title"], "summary": p["summary"]}
        for p in existing
    ]
    existing_by_id = {p["id"]: p for p in existing}

    truly_new: list[ProjectRecord] = []
    merged_ids: set[str] = set()

    for new_proj in new_projects:
        user_prompt = (
            f"New project:\n{json.dumps(_project_ref(new_proj), indent=2)}\n\n"
            f"Existing projects:\n{json.dumps(existing_refs, indent=2)}"
        )
        match: DuplicateMatch = llm.complete_structured_one(
            _MATCH_SYSTEM_PROMPT, user_prompt, DuplicateMatch
        )

        if not match.matched_id or match.matched_id not in existing_by_id:
            truly_new.append(new_proj)
            continue

        # Confirmed duplicate — synthesize merged text then merge fields
        existing_proj = existing_by_id[match.matched_id]
        merged_text = _synthesize_text(existing_proj, new_proj, llm)
        _merge_into(existing_proj, new_proj, merged_text)
        merged_ids.add(match.matched_id)

    updated_existing = list(existing_by_id.values())
    return truly_new, updated_existing


def _project_ref(proj: ProjectRecord) -> dict:
    return {"title": proj.title, "summary": proj.summary}


def _synthesize_text(existing: dict, new_proj: ProjectRecord, llm) -> MergedProjectText:
    user_prompt = (
        f"Existing summary: {existing.get('summary', '')}\n"
        f"Existing description: {existing.get('description_long', '')}\n\n"
        f"New summary: {new_proj.summary}\n"
        f"New description: {new_proj.description_long}"
    )
    return llm.complete_structured_one(_MERGE_SYSTEM_PROMPT, user_prompt, MergedProjectText)


def _merge_into(existing: dict, new_proj: ProjectRecord, merged_text: MergedProjectText) -> None:
    """Merge new_proj fields into existing in-place."""
    existing["summary"] = merged_text.summary
    existing["description_long"] = merged_text.description_long

    for field in ("skills", "keywords", "impact", "role_tags"):
        existing_vals = existing.get(field) or []
        new_vals = getattr(new_proj, field, []) or []
        # Union preserving order: existing first, then any new additions
        seen: set = set()
        merged: list = []
        for v in existing_vals + new_vals:
            if v not in seen:
                seen.add(v)
                merged.append(v)
        existing[field] = merged

    if new_proj.notes:
        existing["notes"] = (
            f"{existing['notes']}\n{new_proj.notes}".strip()
            if existing.get("notes")
            else new_proj.notes
        )
