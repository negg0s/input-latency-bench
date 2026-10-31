"""Check repository text for banned punctuation and filler phrases."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEXT_SUFFIXES = {
    ".py",
    ".md",
    ".toml",
    ".yml",
    ".yaml",
    ".txt",
    ".json",
    ".jsonl",
    ".cfg",
    ".ini",
}
SKIP_DIRS = {
    ".git",
    ".pytest_cache",
    "__pycache__",
    ".venv",
    "venv",
    "build",
    "dist",
    "node_modules",
}
DASHES = {chr(0x2014): "em dash", chr(0x2013): "en dash"}
BANNED = [
    "compre" + "hensive",
    "sea" + "mless",
    "rob" + "ust",
    "lever" + "age",
    "de" + "lve",
    "cutting" + "-edge",
    "state" + "-of-the-art",
    "game" + "-changer",
    "un" + "lock",
    "ele" + "vate",
    "effort" + "less",
    "stream" + "line",
    "har" + "ness",
    "em" + "power",
    "revo" + "lutionize",
    "in to" + "day's",
    "it's impor" + "tant to note",
    "fur" + "thermore",
    "more" + "over",
]


def text_files(root):
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.suffix.lower() in TEXT_SUFFIXES or path.name == ".gitignore":
            yield path


def check_file(path):
    problems = []
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return [(path, 0, f"read error: {exc}")]
    for line_number, line in enumerate(text.splitlines(), 1):
        for char, label in DASHES.items():
            if char in line:
                problems.append((path, line_number, label))
        lowered = line.lower()
        for phrase in BANNED:
            if phrase in lowered:
                problems.append((path, line_number, f"banned phrase: {phrase}"))
    return problems


def main():
    problems = []
    for path in text_files(ROOT):
        problems.extend(check_file(path))
    for path, line_number, reason in problems:
        try:
            shown = path.relative_to(ROOT)
        except ValueError:
            shown = path
        print(f"{shown}:{line_number}: {reason}")
    if problems:
        print(f"{len(problems)} problem(s) found")
        return 1
    print("text check passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
