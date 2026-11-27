"""Deterministic JSON CLI over AssetKit bounded contexts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from . import Workspace
from .build import plan_build, run_build, sync_manifest
from .errors import AssetKitError


def _emit(payload: Any) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="assetkit",
        description="Standalone DDD medical teaching asset management CLI.",
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
    sub.add_parser("scan", help="Emit the full workspace projection as JSON")
    sub.add_parser("validate", help="Validate invariants across all bounded contexts")
    sub.add_parser("economy", help="Compute reuse, load counts, utilization, and budget advice")

    imp = sub.add_parser("impact", help="Trace consumers, reviews, and selections for a target")
    imp.add_argument(
        "target", help="Asset ID, export key (asset@rev:export), or repo-relative path"
    )

    res = sub.add_parser("resolve", help="Resolve candidate assets/parts for a consumer")
    res.add_argument("consumer_id", help="Consumer ID")
    res.add_argument("--req", dest="requirement_id", default=None, help="Specific requirement ID")

    bnd = sub.add_parser("bundle", help="Resolve exact runtime load bundle for a consumer")
    bnd.add_argument("consumer_id", help="Consumer ID")

    gaps = sub.add_parser("gaps", help="List open-gap and rebuild-required consumer requirements")
    gaps.add_argument("--prefix", default=None, help="Filter by consumer ID prefix")

    bld = sub.add_parser("build", help="Plan or execute an Asset Revision recipe")
    bld.add_argument("asset_id", help="Asset ID")
    bld.add_argument("revision_id", help="Revision ID")
    bld.add_argument("--apply", action="store_true", help="Execute recipe (dry-run by default)")

    snc = sub.add_parser("sync", help="Refresh hashes, bytes, and GLB stats in an assets.json")
    snc.add_argument("manifest", help="Repo-relative path to assets.json")
    snc.add_argument("--apply", action="store_true", help="Write changes to manifest")

    cmp = sub.add_parser("compile", help="Compile downstream projections (gallery or r2)")
    cmp.add_argument("--target", choices=("gallery", "r2"), default="gallery")

    args = parser.parse_args(argv)
    try:
        ws = Workspace.load(
            args.repo,
            include_legacy_adapters=not args.native_only,
            inspect_glbs=args.inspect_glb,
        )
        if args.command == "scan":
            _emit(ws.to_dict())
        elif args.command == "validate":
            warnings = ws.validate()
            _emit({"status": "ok", "counts": ws.counts(), "warnings": warnings})
        elif args.command == "economy":
            _emit(ws.delivery.economy(ws.registry).to_dict())
        elif args.command == "impact":
            _emit(ws.delivery.impact(args.target, ws.registry, ws.curation))
        elif args.command == "resolve":
            _emit(
                ws.delivery.resolve(
                    args.consumer_id, ws.registry, ws.vocab, ws.curation, args.requirement_id
                )
            )
        elif args.command == "bundle":
            _emit(ws.delivery.bundle_for(args.consumer_id, ws.registry).to_dict())
        elif args.command == "gaps":
            _emit({"openGaps": ws.delivery.open_gaps(args.prefix)})
        elif args.command == "build":
            spec = plan_build(ws.repository, ws.registry, args.asset_id, args.revision_id)
            _emit(run_build(ws.repository, spec, apply=args.apply).to_dict())
        elif args.command == "sync":
            _emit(sync_manifest(ws.repository, args.manifest, apply=args.apply).to_dict())
        elif args.command == "compile":
            if args.target == "gallery":
                _emit(ws.curation.compile_gallery(ws.registry, ws.delivery))
            else:
                _emit({"items": ws.curation.plan_r2_sync(ws.registry, ws.delivery)})
        return 0
    except (AssetKitError, OSError, ValueError, KeyError, TypeError) as exc:
        print(f"assetkit: {exc}", file=sys.stderr)
        return 2
