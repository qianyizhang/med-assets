#!/usr/bin/env python3
"""Check the known maintained rebuild graph without Blender or hydrated LFS media."""

import ast
import json
from pathlib import Path, PurePosixPath
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "lib"))
from med_assets.artifacts import declared_identity, repo_file

FORBIDDEN = {"reviews", "experiments", "sites"}
REPOSITORY_ROOTS = {"assemblies", "body", "heart", "lessons", "lib", "models", "sources", "tools"}
ENTRY_POINTS = (
    "tools/rebuild_asset.py",
    "tools/rebuild_mesh.py",
    "assemblies/hra-female-pelvis/build.py",
    "assemblies/hra-female-pelvis/check.py",
    "body/breathing/recipes/dome-motion-r01/build.py",
    "models/blood_cell_study/recipes/replay.py",
    "models/bronchial_tree/recipes/distal-simplification-trial/compare.py",
    "models/bronchial_tree/recipes/first-fork-fairing-r15/build.py",
    "models/thyroid_ct_s0189/recipes/illustrative-exterior-r02/build.py",
    "models/skin/recipes/navigation-trial/build.py",
    "models/bone_marrow/recipes/lattice-economy-trial/trial.py",
    *(f"models/lymph_node/recipes/tissue_layers_r01/{name}.py" for name in ("build", "render", "plates")),
    *(f"lessons/{name}/{entry}.py" for name in ("right-arm-parts", "salivary-practice")
      for entry in ("render", "plates")),
)
SPLIT_PATHS = (
    "models/bronchial_tree/recipes/authored-central-fairing-r13/baseline-cameras.json",
    "models/vagina_hra/exports/teaching-context-r03/vagina_teaching_context.glb",
    "sources/fonts/dejavu/LICENSE.txt",
)


def module_path(root, owner, module):
    parts = module.split(".")
    if parts[0] in FORBIDDEN:
        raise ValueError(f"{owner} imports a historical or site module: {module}")
    if parts[0] == "med_assets":
        base = root / "lib"
    elif parts[0] in REPOSITORY_ROOTS:
        base = root
    else:
        base = (root / owner).parent
        # Existing direct-script imports may name tools modules without the tools prefix.
        if not (base / (parts[0] + ".py")).exists():
            base = root / "tools"
    candidate = base.joinpath(*parts).with_suffix(".py")
    if candidate.exists():
        return candidate.relative_to(root).as_posix()
    if parts[0] == "med_assets" and len(parts) > 1:
        raise ValueError(f"{owner} imports a missing toolkit module: {module}")
    return None


def dependency_path(owner, value):
    parts = PurePosixPath(value).parts
    while parts and parts[0] in ("", "/", ".."):
        parts = parts[1:]
    if not parts:
        return None
    if parts[0] in FORBIDDEN:
        raise ValueError(f"{owner} depends on historical or site material: {value}")
    if len(parts) > 1 and parts[0] in REPOSITORY_ROOTS:
        return value
    return None


def python_dependencies(root, owner, source):
    parent = PurePosixPath(owner).parent
    for node in ast.walk(ast.parse(source, filename=owner)):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            path = dependency_path(owner, node.value)
            if path:
                yield path
            # Blender subprocesses and runpy targets can be adjacent to this script.
            value = node.value
            if value.endswith(".py") and "/" not in value and value.isprintable():
                yield (parent / value).as_posix()
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr == "with_name" and len(node.args) == 1:
                argument = node.args[0]
                if isinstance(argument, ast.Constant) and isinstance(argument.value, str):
                    yield (parent / argument.value).as_posix()
        elif isinstance(node, ast.ImportFrom):
            if node.level == 1 and node.module:
                yield (parent / Path(*node.module.split(".")).with_suffix(".py")).as_posix()
                continue
            if node.module in ("med_assets", "tools"):
                names = [f"{node.module}.{alias.name}" for alias in node.names]
            else:
                names = [node.module] if node.module else []
            for name in names:
                path = module_path(root, owner, name)
                if path:
                    yield path
        elif isinstance(node, ast.Import):
            for alias in node.names:
                path = module_path(root, owner, alias.name)
                if path:
                    yield path


def json_dependencies(root, owner, value):
    if isinstance(value, dict):
        path = value.get("path") or value.get("source") or value.get("canonicalPayload")
        if isinstance(path, str) and dependency_path(owner, path):
            if "sha256" in value and "bytes" in value:
                if declared_identity(root, path) != (value["sha256"], value["bytes"]):
                    raise ValueError(f"{owner} has a stale input or output identity: {path}")
        for item in value.values():
            yield from json_dependencies(root, owner, item)
    elif isinstance(value, list):
        for item in value:
            yield from json_dependencies(root, owner, item)
    elif isinstance(value, str):
        path = dependency_path(owner, value)
        if path:
            yield path


def verify_graph(root, entries):
    root = root.resolve()
    pending = list(entries)
    checked = set()
    while pending:
        owner = pending.pop()
        if owner in checked:
            continue
        if (root / owner).is_dir():
            # Directory roots are used by a few declared joins. Reject redirected inputs.
            if (root / owner).resolve() != root / owner:
                raise ValueError(f"Linked recipe input: {owner}")
            continue
        path = repo_file(root, owner)
        checked.add(owner)
        if path.suffix == ".py":
            pending.extend(python_dependencies(root, owner, path.read_text()))
        if path.suffix == ".json":
            pending.extend(json_dependencies(root, owner, json.loads(path.read_text())))
    return checked


def owner_configs(root):
    packages = [package for area in ("models", "assemblies", "body", "heart", "lessons")
                for package in (root / area).iterdir() if package.is_dir()]
    configs = set()
    documented = set()
    for package in packages:
        for path in sorted((package / "recipes").glob("*.json")):
            recipe = json.loads(path.read_text())
            if not isinstance(recipe, dict) or "operation" not in recipe:
                continue
            relative = path.relative_to(root).as_posix()
            owner = package.relative_to(root).as_posix()
            source, output = recipe["source"], recipe["output"]
            if not output["path"].startswith(owner + "/"):
                raise ValueError(f"{relative} describes another package's output: {output['path']}")
            for pin in (source, output):
                if any(field not in pin for field in ("path", "bytes", "sha256")):
                    raise ValueError(f"{relative} has an incomplete source or output pin")
            configs.add(relative)
        readmes = [package / "README.md", *package.glob("exports/*/README.md")]
        for path in readmes:
            if not path.is_file():
                continue
            for line in path.read_text().splitlines():
                if "tools/rebuild_asset.py" not in line and "tools/rebuild_mesh.py" not in line:
                    continue
                documented.update(word.strip('`') for word in line.split()
                                  if "/recipes/" in word and word.rstrip('`').endswith(".json"))
    if configs != documented:
        raise ValueError(f"Owner recipe declarations and rebuild instructions differ. "
                         f"Missing recipes: {sorted(documented - configs)}. "
                         f"Undocumented recipes: {sorted(configs - documented)}.")
    return sorted(configs)


def recipe_roots(root):
    """Return the active rebuild commands, owner declarations and declared path joins."""
    salivary = "lessons/salivary-practice/views.json"
    views = json.loads(repo_file(root, salivary).read_text())
    layer_files = {layer["file"] for view in views.values() for layer in view["layers"]}
    salivary_inputs = [
        f"models/salivary_glands/exports/{edition}/{filename}"
        for edition in ("z-native-shared-r01", "z-native-scoped-r02")
        for filename in sorted(layer_files)
    ]
    return (
        *ENTRY_POINTS, *SPLIT_PATHS, *owner_configs(root), *salivary_inputs,
        "assemblies/hra-female-pelvis/bladder-selection.json",
        "lessons/right-arm-parts/arm-lesson-layers.json",
        "lessons/right-arm-parts/anchors.json",
        "models/lymph_node/recipes/tissue_layers_r01/selection.json",
        "body/breathing/recipes/dome-motion-r01/selection.json",
        salivary,
    )


def main():
    checked = verify_graph(ROOT, recipe_roots(ROOT))
    print(f"Verified {len(checked)} maintained recipe inputs, commands and identity declarations.")


if __name__ == "__main__":
    main()
