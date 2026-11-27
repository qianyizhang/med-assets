"""Deterministic JSON CLI for AssetKit."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .economy import analyze_economy, impact, resolve
from .model import AssetKitError
from .workspace import load_catalog


def _emit(payload: Any) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="assetkit",
        description="Standalone medical teaching asset management CLI.",
    )
    parser.add_argument("--repo", type=Path, default=Path.cwd(), help="Repository root path")
    parser.add_argument(
        "--native-only",
        action="store_true",
        help="Read only native AssetKit manifests (skip legacy repo adapters)",
    )
    parser.add_argument(
        "--inspect-glb",
        action="store_true",
        help="Inspect hydrated GLB headers for triangle and node statistics",
    )

    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("scan", help="Emit the full catalog projection as JSON")
    sub.add_parser("validate", help="Validate catalog invariants and report warnings")
    sub.add_parser("economy", help="Compute reuse, load counts, utilization, and budget advice")

    imp = sub.add_parser("impact", help="Trace consumers, reviews, and selections for a target")
    imp.add_argument(
        "target", help="Asset ID, export key (asset@rev:export), or repo-relative path"
    )

    res = sub.add_parser("resolve", help="Resolve candidate assets/parts for a consumer")
    res.add_argument("consumer_id", help="Consumer ID")
    res.add_argument("--req", dest="requirement_id", default=None, help="Specific requirement ID")

    args = parser.parse_args(argv)
    try:
        catalog = load_catalog(
            args.repo,
            include_legacy_adapters=not args.native_only,
            inspect_glbs=args.inspect_glb,
        )
        if args.command == "scan":
            _emit(catalog.to_dict())
        elif args.command == "validate":
            warnings = catalog.validate()
            _emit(
                {
                    "status": "ok",
                    "counts": catalog.summary_counts(),
                    "warnings": warnings,
                }
            )
        elif args.command == "economy":
            _emit(analyze_economy(catalog).to_dict())
        elif args.command == "impact":
            _emit(impact(catalog, args.target))
        elif args.command == "resolve":
            _emit(resolve(catalog, args.consumer_id, args.requirement_id))
        return 0
    except (AssetKitError, OSError, ValueError, KeyError, TypeError) as exc:
        print(f"assetkit: {exc}", file=sys.stderr)
        return 2
