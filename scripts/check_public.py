"""Block private data from reaching this public repo. Run before every push:
    python scripts/check_public.py
Also runs in CI. Exits 1 if anything private is found."""
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ALLOWED = {"index.html", "Eagle_Kuo_Resume.pdf", ".gitignore", "README.md",
           "scripts/check_public.py", ".github/workflows/check.yml"}
FORBIDDEN_NAMES = re.compile(r"tracker|answers|profile\.md|CONSOLE|Resume_[AB]\.pdf|CV_original", re.I)
PHONE = re.compile(r"(\+?886[\s-]?9\d{2}|09\d{2})[\s-]?\d{3}[\s-]?\d{3}")
SECRETS = re.compile(r"salary|visa|passport|password", re.I)


def tracked_files():
    out = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True)
    files = out.stdout.split() if out.returncode == 0 and out.stdout.strip() else []
    return files or [str(p.relative_to(ROOT)).replace("\\", "/") for p in ROOT.rglob("*")
                     if p.is_file() and ".git" not in p.parts]


def text_of(path: Path) -> str:
    if path.suffix == ".pdf":
        from pypdf import PdfReader
        return "\n".join(page.extract_text() or "" for page in PdfReader(path).pages)
    return path.read_text(encoding="utf-8", errors="ignore")


def main() -> int:
    errors = []
    for f in tracked_files():
        if f not in ALLOWED:
            errors.append(f"not on the allow-list: {f}")
        if FORBIDDEN_NAMES.search(f):
            errors.append(f"private file name: {f}")
        p = ROOT / f
        if p.suffix in {".html", ".pdf", ".md"}:
            body = text_of(p)
            if PHONE.search(body):
                errors.append(f"phone number in {f}")
            if p.suffix != ".py" and f != "scripts/check_public.py" and SECRETS.search(body):
                errors.append(f"private keyword in {f}")
    if errors:
        print("BLOCKED\n" + "\n".join(errors))
        return 1
    print("OK: nothing private found")
    return 0


if __name__ == "__main__":
    sys.exit(main())
