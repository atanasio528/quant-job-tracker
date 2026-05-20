from pathlib import Path


def load_policy_bundle(policy_dir: Path, role: str) -> str:
    shared_path = policy_dir / "shared.md"
    role_path = policy_dir / f"{role}.md"

    shared = shared_path.read_text(encoding="utf-8")
    role_text = role_path.read_text(encoding="utf-8")

    return f"{shared.rstrip()}\n\n---\n\n{role_text.rstrip()}\n"
