#!/usr/bin/env python3
"""Validate, render and promote local accepted teaching assessments."""
import argparse
import sys
from pathlib import Path

from med_assets.teaching_cli import (
    REVIEW_ERRORS, REVIEW_FAILURE, check_teaching, promote_teaching, recover_teaching, render_teaching,
)
from med_assets.teaching_promotion import Promotion

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=ROOT, help="Repository checkout to validate or update")
    parser.add_argument("--check", action="store_true", help="Validate every accepted task and check both tracked views")
    commands = parser.add_subparsers(dest="command")
    writer = commands.add_parser("promote", help="Plan or apply a promotion from a pinned reviewed assessment")
    for field in ("review", "export", "task-id", "collection-id", "family-id"):
        writer.add_argument("--" + field, required=True)
    writer.add_argument("--reviewed-sha256", help="Exact reviewed row pin when review selection is ambiguous")
    writer.add_argument("--disposition", choices=("maintained", "alternative"), required=True)
    writer.add_argument("--replaces", help="Exact maintained export replaced within this collection and family")
    writer.add_argument("--new-family-label", help="Label for a new register entry")
    writer.add_argument("--apply", action="store_true", help="Apply the plan locally after a dry run")
    writer.add_argument("--expect-state", help="planSha256 from the reviewed dry run")
    commands.add_parser("recover", help="Complete an interrupted local promotion")
    args = parser.parse_args()
    if args.command and args.check:
        parser.error("--check cannot be combined with a promotion command")
    repo = args.repo.resolve()
    try:
        match args.command:
            case "promote":
                instruction = Promotion(
                    review=args.review,
                    reviewed_sha256=args.reviewed_sha256,
                    export=args.export,
                    task_id=args.task_id,
                    collection_id=args.collection_id,
                    family_id=args.family_id,
                    disposition=args.disposition,
                    replaces=args.replaces,
                    new_family_label=args.new_family_label,
                )
                output = promote_teaching(
                    repo, instruction, apply=args.apply, expect_state=args.expect_state
                )
            case "recover":
                output = recover_teaching(repo)
            case _:
                output = check_teaching(repo) if args.check else render_teaching(repo)
        sys.stdout.write(output)
    except REVIEW_ERRORS as error:
        parser.exit(1, f"{REVIEW_FAILURE}: {error}\n")


if __name__ == "__main__":
    main()
