"""CLI to list all user profiles."""
import os
from pathlib import Path
from resume_helper.config import PROJECT_ROOT


def main() -> None:
    users_dir = PROJECT_ROOT / "users"
    active = os.getenv("RESUME_HELPER_USER", "").strip()

    profiles = sorted(
        p.name for p in users_dir.iterdir()
        if p.is_dir() and not p.name.startswith(".")
    ) if users_dir.exists() else []

    if not profiles:
        print("No user profiles found. Run: resume-helper-init --user <name>")
        return

    print("User profiles:")
    for name in profiles:
        if name == active:
            print(f"  * {name}  (active)")
        elif name == "jayne_dough" and not active:
            print(f"    {name}  (default)")
        else:
            print(f"    {name}")

    if active and active not in profiles:
        print(f"\n  WARNING: RESUME_HELPER_USER='{active}' profile not found.")
        print(f"  Run: resume-helper-init --user {active}")
