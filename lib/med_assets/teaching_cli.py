"""Shared command output for the maintained teaching register."""

from __future__ import annotations

import json
from pathlib import Path

from .teaching import CurrentTeaching, render_register, validate_current
from .teaching_promotion import Promotion, promote, recover

REVIEW_ERRORS = (OSError, ValueError, KeyError, TypeError, RuntimeError)
REVIEW_FAILURE = "Maintained teaching failed"


def render_teaching(repo: Path) -> str:
    return render_register(CurrentTeaching(repo).selections)


def check_teaching(repo: Path) -> str:
    count = validate_current(repo)
    return (
        f"Validated {count} accepted teaching assessments, the teaching register and scorecard.\n"
    )


def promote_teaching(
    repo: Path, promotion: Promotion, *, apply: bool, expect_state: str | None
) -> str:
    result = promote(repo, promotion, apply=apply, expect_state=expect_state)
    return json.dumps(result, ensure_ascii=False, indent=2) + "\n"


def recover_teaching(repo: Path) -> str:
    if recover(repo):
        return "Recovered teaching promotion.\n"
    return "No teaching promotion to recover.\n"
