#!/usr/bin/env python3
"""PreToolUse guard for Bash commands.

Four rails, enforced before the command runs:
  1. git commit  -> scan pending changes + untracked files for secret material.
  2. git push    -> full test suite must pass (pytest tests/ -q).
  3. git push --force to main -> always blocked.
  4. git merge   -> full test suite must pass (pytest tests/ -q).

Exit 0 = allow. Exit 2 = block (stderr is shown to the agent).
Infrastructure errors fail OPEN (exit 0) so a broken guard cannot brick the
session; rule hits always fail CLOSED (exit 2).
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys

PROJECT_DIR = os.environ.get("CLAUDE_PROJECT_DIR", ".")

# Assignment of a long literal to a secret-shaped name, or well-known key shapes.
SECRET_PATTERNS = [
    # no leading \b: must catch prefixed names like BYBIT_API_KEY, TELEGRAM_BOT_TOKEN
    re.compile(
        r"(?i)(api[_-]?key|secret|token|passw(?:or)?d|private[_-]?key|"
        r"access[_-]?key)\b\s*[:=]\s*[\"'][A-Za-z0-9_\-/+=.:]{12,}[\"']"
    ),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),                # AWS access key
    re.compile(r"\bsk-[A-Za-z0-9_\-]{20,}\b"),          # OpenAI/Anthropic-style
    re.compile(r"\bghp_[A-Za-z0-9]{36}\b"),             # GitHub PAT
    re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}\b"),    # Slack
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |PGP )?PRIVATE KEY-----"),
]

ALLOWLIST = re.compile(r"(?i)(example|placeholder|your[_-]|dummy|changeme|xxxx)")


def run(cmd: list[str]) -> str:
    out = subprocess.run(
        cmd, cwd=PROJECT_DIR, capture_output=True, text=True, timeout=90
    )
    return out.stdout


def scan_text(text: str, origin: str) -> list[str]:
    hits = []
    for line in text.splitlines():
        if ALLOWLIST.search(line):
            continue
        for pat in SECRET_PATTERNS:
            if pat.search(line):
                hits.append(f"{origin}: {line.strip()[:120]}")
                break
    return hits


def check_secrets() -> list[str]:
    """Scan diff-vs-HEAD plus untracked (non-ignored) files.

    The hook fires BEFORE the bash command runs, so `git add && git commit`
    has not staged anything yet — scan the working tree, not the index.
    """
    hits = []
    diff = run(["git", "diff", "HEAD", "-U0"])
    added = "\n".join(ln[1:] for ln in diff.splitlines() if ln.startswith("+"))
    hits += scan_text(added, "tracked change")

    untracked = run(["git", "ls-files", "--others", "--exclude-standard"])
    for path in untracked.splitlines():
        full = os.path.join(PROJECT_DIR, path)
        try:
            if os.path.getsize(full) > 1_000_000:
                continue
            with open(full, errors="ignore") as f:
                hits += scan_text(f.read(), path)
        except OSError:
            continue
    return hits


def main() -> None:
    try:
        payload = json.load(sys.stdin)
        command = payload.get("tool_input", {}).get("command", "") or ""
    except Exception:
        sys.exit(0)

    is_commit = re.search(r"\bgit\b[^|;&]*\bcommit\b", command)
    is_push = re.search(r"\bgit\b[^|;&]*\bpush\b", command)
    is_merge = re.search(r"\bgit\b[^|;&]*\bmerge\b", command)

    if is_push and re.search(r"(--force\b|--force-with-lease\b|\s-f\b)", command) \
            and re.search(r"\b(main|master)\b", command):
        print("BLOCKED: force-push to main is not allowed in this repo.", file=sys.stderr)
        sys.exit(2)

    if is_commit:
        try:
            hits = check_secrets()
        except Exception:
            sys.exit(0)  # guard infra failed — do not brick commits
        if hits:
            print(
                "BLOCKED: possible secret material in pending changes "
                "(rule: never commit secrets — GROUND_TRUTH.md):\n  "
                + "\n  ".join(hits[:10])
                + "\nRemove the secret (use env vars / .env, which is gitignored) and retry.",
                file=sys.stderr,
            )
            sys.exit(2)

    if is_push or is_merge:
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", "tests/", "-q", "-x"],
                cwd=PROJECT_DIR, capture_output=True, text=True, timeout=300,
            )
        except FileNotFoundError:
            action = "pushing" if is_push else "merging"
            print(f"BLOCKED: pytest unavailable — run the session-start hook "
                  f"(pip install -e '.[dev]') before {action}.", file=sys.stderr)
            sys.exit(2)
        except Exception:
            sys.exit(0)
        if result.returncode != 0:
            tail = (result.stdout + result.stderr)[-1500:]
            action = "push" if is_push else "merge"
            print(
                f"BLOCKED: test suite must pass before {action} (rule: tests before {action}).\n"
                + tail,
                file=sys.stderr,
            )
            sys.exit(2)

    sys.exit(0)


if __name__ == "__main__":
    main()
