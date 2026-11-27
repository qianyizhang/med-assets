#!/usr/bin/env python3
"""Inspect, backfill and hydrate med-assets governance records."""

import argparse
import json
import sys
from pathlib import Path

from med_assets.governance import GovernanceError, find, impact, show
from med_assets.governance_lifecycle import ACTIONS, apply_lifecycle_plan, create_lifecycle_plan
from med_assets.governance_migration import apply_backfill_plan, hydrate_lfs, write_backfill_plan
from med_assets.governance_resolution import resolve_detailed
from med_assets.governance_ultrasound import build_catalog

ROOT = Path(__file__).resolve().parents[1]


def emit(value):
    print(json.dumps(value, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=ROOT)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("scan", help="Build a disposable catalog")
    query = commands.add_parser("find")
    query.add_argument("query")
    query.add_argument(
        "--domain",
        choices=("ultrasound-anatomy", "body-systems", "teaching-assessments", "lessons"),
    )
    inspect = commands.add_parser("show")
    inspect.add_argument("identity")
    affected = commands.add_parser("impact")
    affected.add_argument("identity")
    resolver = commands.add_parser(
        "resolve", help="Resolve explicit consumer part selectors to package-owned candidates"
    )
    resolver.add_argument("consumer_id")
    resolver.add_argument("--part")
    backfill = commands.add_parser("backfill")
    backfill.add_argument("action", choices=("plan", "apply"))
    backfill.add_argument(
        "--output", type=Path, default=Path(".artifacts/asset-backfill.plan.json")
    )
    backfill.add_argument("--plan", type=Path)
    hydrate = commands.add_parser("hydrate")
    hydrate.add_argument("paths", nargs="+")
    hydrate.add_argument("--apply", action="store_true")
    lifecycle = commands.add_parser("lifecycle")
    actions = lifecycle.add_subparsers(dest="lifecycle_action", required=True)
    plan = actions.add_parser("plan")
    plan.add_argument("--action", choices=sorted(ACTIONS), required=True)
    plan.add_argument("--asset", required=True)
    plan.add_argument("--payload", type=Path, required=True)
    plan.add_argument("--output", type=Path, default=Path(".artifacts/asset-lifecycle.plan.json"))
    apply = actions.add_parser("apply")
    apply.add_argument("--plan", type=Path, required=True)
    args = parser.parse_args()
    repo = args.repo.resolve()
    try:
        if args.command == "scan":
            emit(build_catalog(repo).to_dict())
        elif args.command == "find":
            emit(find(build_catalog(repo), args.query, args.domain))
        elif args.command == "show":
            emit(show(build_catalog(repo), args.identity))
        elif args.command == "impact":
            emit(impact(build_catalog(repo), args.identity))
        elif args.command == "resolve":
            emit(resolve_detailed(build_catalog(repo), args.consumer_id, args.part))
        elif args.command == "backfill" and args.action == "plan":
            output = args.output if args.output.is_absolute() else repo / args.output
            plan = write_backfill_plan(repo, output)
            emit(
                {
                    "status": "planned",
                    "output": output.relative_to(repo).as_posix(),
                    "proposals": len(plan["proposals"]),
                    "consumerCoverage": plan["consumerCoverage"],
                }
            )
        elif args.command == "backfill" and args.action == "apply":
            if not args.plan:
                parser.error("backfill apply requires --plan")
            path = args.plan if args.plan.is_absolute() else repo / args.plan
            emit({"status": "applied", "records": apply_backfill_plan(repo, path)})
        elif args.command == "hydrate":
            emit(hydrate_lfs(repo, args.paths, args.apply))
        elif args.command == "lifecycle" and args.lifecycle_action == "plan":
            payload = args.payload if args.payload.is_absolute() else repo / args.payload
            output = args.output if args.output.is_absolute() else repo / args.output
            plan = create_lifecycle_plan(repo, args.asset, args.action, payload)
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(
                json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )
            emit(
                {
                    "status": "planned",
                    "action": args.action,
                    "assetId": args.asset,
                    "output": output.relative_to(repo).as_posix(),
                    "affectedConsumers": len(plan["affectedConsumers"]),
                    "requiredChecks": plan["requiredChecks"],
                }
            )
        elif args.command == "lifecycle" and args.lifecycle_action == "apply":
            path = args.plan if args.plan.is_absolute() else repo / args.plan
            emit(apply_lifecycle_plan(repo, path))
        return 0
    except (GovernanceError, OSError, ValueError, KeyError, TypeError) as exc:
        print(f"asset-governance: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
