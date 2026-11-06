"""Assemble survey overlays with the exact external Data framework, offline."""
import argparse
import hashlib
import io
import json
import re
import shutil
import subprocess
import tarfile
import tempfile
from pathlib import Path, PurePosixPath

SITE = Path(__file__).resolve().parents[1]


def git(source, *args):
    result = subprocess.run(['git', '-C', str(source), *args], capture_output=True)
    if result.returncode:
        raise ValueError('Pinned framework is unavailable. Restore its frozen ZIP Git bundle, or open the existing Site source into .local/publication first.')
    return result.stdout


def prepare(site, source, output):
    """Create a fresh full project; never overwrite an existing destination."""
    if output.exists() or output.is_symlink():
        raise ValueError('Output already exists; choose a fresh build directory.')
    lock = json.loads((site / 'framework.lock.json').read_text())
    commit = lock['commit']
    if not re.fullmatch('[0-9a-f]{40}', commit):
        raise ValueError('Framework commit must be an exact Git object ID.')
    tree = git(source, 'rev-parse', f'{commit}^{{tree}}').decode().strip()
    if tree != lock['tree']:
        raise ValueError('Framework tree differs from its lock.')
    manifest = git(source, 'show', f'{commit}:protected-runtime.json')
    if hashlib.sha256(manifest).hexdigest() != lock['runtimeManifestSha256']:
        raise ValueError('Framework integrity manifest differs from its lock.')
    hosting = json.loads(git(source, 'show', f'{commit}:.openai/hosting.json'))
    overlay_hosting = json.loads((site / 'app/.openai/hosting.json').read_text())
    if hosting != overlay_hosting or hosting['project_id'] != lock['projectId']:
        raise ValueError('Site identity/bindings differ; refusing to assemble another Site.')
    reference = json.loads((site / 'snapshot-reference.json').read_text())
    snapshot = site / 'app/src/data.json'
    if not snapshot.is_file() or snapshot.is_symlink():
        raise ValueError('Restore app/src/data.json with tools/restore_snapshot.py first.')
    raw = snapshot.read_bytes()
    if json.loads(raw).get('id') != reference['artifactId']:
        raise ValueError('Snapshot belongs to another artifact.')
    # Read source, never an old ignored dist or dependency cache.
    archive = tarfile.open(fileobj=io.BytesIO(git(source, 'archive', '--format=tar', commit)))
    members = archive.getmembers()
    for member in members:
        path = PurePosixPath(member.name)
        if path.is_absolute() or '..' in path.parts or '.git' in path.parts or not (member.isfile() or member.isdir()):
            raise ValueError('Framework archive contains an unsafe path or link.')
    overlays = []
    for directory in ('src/content', '.openai', 'tests'):
        base = site / 'app' / directory
        if base.is_symlink():
            raise ValueError('Survey overlays must not contain symlinks.')
        for path in base.rglob('*'):
            if path.is_symlink():
                raise ValueError('Survey overlays must not contain symlinks.')
            if path.is_file() and '__pycache__' not in path.parts:
                overlays.append(path)
    overlays.append(site / 'app/src/theme.css')
    if any(path.is_symlink() or not path.is_file() for path in overlays):
        raise ValueError('Survey overlay is missing or is a symlink.')
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='survey-framework-', dir=output.parent) as temporary:
        staged = Path(temporary) / 'project'
        staged.mkdir()
        for member in members:
            # Survey content is owned here, never silently restored from the old Site.
            if member.name.startswith('src/content/') or member.name == 'src/theme.css':
                continue
            target = staged / member.name
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(archive.extractfile(member).read())
                target.chmod(member.mode & 0o777)
        for path in overlays:
            target = staged / path.relative_to(site / 'app')
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, target)
        (staged / 'src/data.json').write_bytes(raw)
        # rename refuses an existing nonempty project; no source/history is replaced.
        if output.exists() or output.is_symlink():
            raise ValueError('Output was created meanwhile; refusing to replace it.')
        staged.rename(output)
    return output


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=SITE / '.local/publication')
    parser.add_argument('--output', type=Path, default=SITE / '.local/app')
    args = parser.parse_args()
    try:
        result = prepare(SITE, args.source, args.output)
    except (ValueError, OSError, KeyError, json.JSONDecodeError) as error:
        parser.exit(1, f'{error}\n')
    print(f'Prepared pinned framework plus survey source: {result}')
