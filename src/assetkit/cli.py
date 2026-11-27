"""Deterministic JSON CLI over AssetKit bounded contexts (powered by Typer)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, Literal

import typer

from . import AssetModel, Workspace
from .build import BuildResult, plan_build, run_build, sync_manifest
from .errors import AssetKitError

app = typer.Typer(
    name="assetkit",
    help="DDD medical teaching asset management CLI.",
    no_args_is_help=True,
    add_completion=False,
)


@dataclass
class _State:
    repo: Path
    native_only: bool
    inspect_glb: bool

    def load(self) -> Workspace:
        return Workspace.load(
            self.repo,
            include_legacy_adapters=not self.native_only,
            inspect_glbs=self.inspect_glb,
        )


def _emit(payload: Any) -> None:
    if isinstance(payload, AssetModel):
        typer.echo(payload.to_json(indent=2))
        return
    typer.echo(json.dumps(payload, ensure_ascii=False, indent=2))


def _state(ctx: typer.Context) -> _State:
    return ctx.obj


def _run(fn) -> None:
    try:
        result = fn()
        _emit(result)
        if isinstance(result, BuildResult) and result.status == "failed":
            raise typer.Exit(code=1)
    except (AssetKitError, OSError, ValueError, KeyError, TypeError) as exc:
        typer.echo(f"assetkit: {exc}", err=True)
        raise typer.Exit(code=2) from exc


@app.callback()
def configure(
    ctx: typer.Context,
    repo: Annotated[Path, typer.Option("--repo", help="Repository root path")] = Path("."),
    native_only: Annotated[
        bool, typer.Option("--native-only", help="Read only native AssetKit manifests")
    ] = False,
    inspect_glb: Annotated[
        bool, typer.Option("--inspect-glb", help="Inspect hydrated GLB headers for mesh stats")
    ] = False,
) -> None:
    """Configure shared workspace options."""
    ctx.obj = _State(repo=repo, native_only=native_only, inspect_glb=inspect_glb)


@app.command()
def scan(ctx: typer.Context) -> None:
    """Emit the full workspace projection as JSON."""
    _run(lambda: _state(ctx).load().to_dict())


@app.command()
def validate(ctx: typer.Context) -> None:
    """Validate invariants across all bounded contexts."""

    def _op() -> dict[str, Any]:
        ws = _state(ctx).load()
        return {"status": "ok", "counts": ws.counts(), "warnings": ws.validate()}

    _run(_op)


@app.command()
def find(
    ctx: typer.Context,
    query: Annotated[str, typer.Argument(help="Search query across assets, parts, and consumers")],
) -> None:
    """Discover assets, parts, and consumers matching a query."""
    _run(lambda: _state(ctx).load().find(query))


@app.command()
def show(
    ctx: typer.Context,
    target: Annotated[str, typer.Argument(help="Asset ID, export key, path, or consumer ID")],
) -> None:
    """Inspect a maintained asset or consumer with its exports, assessments, and decisions."""
    _run(lambda: _state(ctx).load().show(target))


@app.command()
def economy(ctx: typer.Context) -> None:
    """Compute reuse, load counts, part/byte utilization, and budget advice."""
    _run(lambda: _state(ctx).load().economy())


@app.command()
def impact(
    ctx: typer.Context,
    target: Annotated[str, typer.Argument(help="Asset ID, export key, or repo-relative path")],
) -> None:
    """Trace consumers, reviews, and selections affected by a target."""
    _run(lambda: _state(ctx).load().impact(target))


@app.command()
def resolve(
    ctx: typer.Context,
    consumer_id: Annotated[str, typer.Argument(help="Consumer ID")],
    req: Annotated[str | None, typer.Option("--req", help="Specific requirement ID")] = None,
) -> None:
    """Resolve candidate assets/parts for a consumer's requirements."""
    _run(lambda: _state(ctx).load().resolve(consumer_id, req))


@app.command()
def bundle(
    ctx: typer.Context,
    consumer_id: Annotated[str, typer.Argument(help="Consumer ID")],
) -> None:
    """Plan a consumer load and report the storage status of each export."""
    _run(lambda: _state(ctx).load().bundle(consumer_id))


@app.command()
def gaps(
    ctx: typer.Context,
    prefix: Annotated[str | None, typer.Option("--prefix", help="Consumer ID prefix")] = None,
) -> None:
    """List open-gap and rebuild-required consumer requirements."""

    def _op() -> dict[str, Any]:
        ws = _state(ctx).load()
        return {"openGaps": [g.to_dict() for g in ws.delivery.open_gaps(prefix)]}

    _run(_op)


@app.command()
def build(
    ctx: typer.Context,
    asset_id: Annotated[str, typer.Argument(help="Asset ID")],
    revision_id: Annotated[str, typer.Argument(help="Revision ID")],
    apply: Annotated[
        bool, typer.Option("--apply", help="Execute recipe (dry-run default)")
    ] = False,
) -> None:
    """Plan or execute an Asset Revision recipe."""

    def _op() -> Any:
        ws = _state(ctx).load()
        spec = plan_build(ws.repository, ws.registry, asset_id, revision_id)
        return run_build(ws.repository, spec, apply=apply)

    _run(_op)


@app.command()
def sync(
    ctx: typer.Context,
    manifest: Annotated[str, typer.Argument(help="Repo-relative path to assets.json")],
    apply: Annotated[bool, typer.Option("--apply", help="Write changes to manifest")] = False,
) -> None:
    """Refresh sha256, bytes, and GLB stats in an assets.json manifest."""

    def _op() -> Any:
        ws = _state(ctx).load()
        return sync_manifest(ws.repository, manifest, apply=apply)

    _run(_op)


@app.command("compile")
def compile_target(
    ctx: typer.Context,
    target: Annotated[
        Literal["gallery", "r2"], typer.Option("--target", help="Projection target")
    ] = "gallery",
) -> None:
    """Compile downstream projections (gallery index or r2 sync plan)."""

    def _op() -> Any:
        ws = _state(ctx).load()
        if target == "gallery":
            return ws.compile_gallery()
        return {"items": [item.to_dict() for item in ws.plan_r2_sync()]}

    _run(_op)


def main() -> None:
    app()
