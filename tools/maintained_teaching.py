#!/usr/bin/env python3
"""Validate, render and promote local accepted teaching assessments."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "lib"))
from med_assets.teaching import CurrentTeaching, render_register, validate_current
from med_assets.teaching_promotion import Promotion, promote, recover


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
    writer.add_argument("--new-family-label", help="Label for the first maintained export of a new family")
    writer.add_argument("--apply", action="store_true", help="Apply the plan locally after a dry run")
    writer.add_argument("--expect-state", help="planSha256 from the reviewed dry run")
    commands.add_parser("recover", help="Complete an interrupted local promotion")
    args = parser.parse_args()
    if args.command and args.check:
        parser.error("--check cannot be combined with a promotion command")
    repo = args.repo.resolve()
    try:
        if args.command == "promote":
            promotion = Promotion(args.review, args.reviewed_sha256, args.export, args.task_id,
                                  args.collection_id, args.family_id, args.disposition, args.replaces,
                                  args.new_family_label)
            output = promote(repo, promotion, apply=args.apply, expect_state=args.expect_state)
            print(json.dumps(output, ensure_ascii=False, indent=2))
        elif args.command == "recover":
            print("Recovered teaching promotion." if recover(repo) else "No teaching promotion to recover.")
        elif args.check:
            count = validate_current(repo)
            print(f"Validated {count} accepted teaching assessments, the maintained register and scorecard.")
        else:
            current = CurrentTeaching(repo)
            sys.stdout.write(render_register(current.selections))
    except (OSError, ValueError, KeyError, TypeError, RuntimeError) as error:
        parser.exit(1, f"Maintained teaching failed: {error}\n")


if __name__ == "__main__":
    main()
