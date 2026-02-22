"""CLI to initialise a new user profile."""
import shutil
import sys

from resume_helper.config import PROJECT_ROOT, resolve_user_paths, ensure_user_dirs


def main() -> None:
    name = input("Enter profile name: ").strip()
    if not name:
        print("[init] ERROR: Profile name cannot be empty.")
        sys.exit(1)

    user_paths = resolve_user_paths(name)
    user_root = PROJECT_ROOT / "users" / name

    if user_root.exists():
        print(f"[init] User profile '{name}' already exists at {user_root}.")
        sys.exit(0)

    ensure_user_dirs(user_paths)
    shutil.copy(PROJECT_ROOT / "shared" / "projects_empty.json", user_paths.projects)

    print(f"[init] Created user profile '{name}'.")
    print(f"[init] Drop your resume PDF at:")
    print(f"         {user_paths.resume}")
    print(f"[init] See README.md → 'Getting started' for next steps.")
