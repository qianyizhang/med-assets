"""Assemble survey overlays with the exact external Data framework, offline."""
import argparse
import hashlib
import io
import json
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path, PurePosixPath

SITE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SITE.parents[1]))
sys.path.insert(0, str(SITE / 'tools'))
from restore_snapshot import verify_source_seed


def git(source, *args):
    result = subprocess.run(['git', '-C', str(source), *args], capture_output=True)
    if result.returncode:
        raise ValueError('Pinned framework is unavailable. Restore its frozen ZIP Git bundle, or open the existing Site source into .local/publication first.')
    return result.stdout


def extract_project(source, commit, output, *, omit_overlay=False):
    with tarfile.open(fileobj=io.BytesIO(git(source, 'archive', '--format=tar', commit))) as archive:
        for member in archive.getmembers():
            path = PurePosixPath(member.name)
            if path.is_absolute() or '..' in path.parts or '.git' in path.parts or not (member.isfile() or member.isdir()):
                raise ValueError('Framework archive contains an unsafe path or link.')
            if omit_overlay and (member.name.startswith('src/content/') or member.name == 'src/theme.css'):
                continue
            target = output / path
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(archive.extractfile(member).read())
                target.chmod(member.mode & 0o777)


def compile_library(site, project, selection, *, offline=True, plan_inputs=None):
    reference = json.loads((site / 'snapshot-reference.json').read_text())
    subprocess.run(['node', str(site / 'tools/compile_library.mjs'), str(project), selection,
                    reference['sourceSnapshotSha256'], '--offline' if offline else '--online',
                    *([str(plan_inputs)] if plan_inputs else [])], check=True)


def plan_gallery_admission(site):
    from gallery_runtime import prepare_library_inputs

    with tempfile.TemporaryDirectory(prefix='gallery-admission-') as temporary:
        teaching = Path(temporary) / 'teaching-inputs'
        index = site / 'app/src/content/assets/delivery-index.json'
        prepare_library_inputs(site.parents[1], index, teaching)
        compile_library(site, site / 'app', 'candidate', plan_inputs=teaching)


def read_seed(site, reference, seed_path):
    snapshot = site / 'app/src/data.json' if seed_path is None else seed_path
    if not snapshot.is_file() or snapshot.is_symlink():
        raise ValueError('Restore app/src/data.json with the Gallery bootstrap or sites/anatomy-gallery/tools/restore_snapshot.py.')
    raw = snapshot.read_bytes()
    verify_source_seed(raw, reference)
    if json.loads(raw).get('id') != reference['artifactId']:
        raise ValueError('Snapshot belongs to another artifact.')
    return raw


def prepare_published(site, source, output, *, seed_path=None):
    """Rehearse the approved Site source with its public catalog on any preview origin."""
    reference = json.loads((site / 'snapshot-reference.json').read_text())
    release = reference['livePublication']
    seed = json.loads(read_seed(site, reference, seed_path))
    commit = release['publicationCommit']
    if not re.fullmatch('[0-9a-f]{40}', commit):
        raise ValueError('Published Gallery needs an exact Site source revision.')
    if output.exists() or output.is_symlink():
        raise ValueError('Output already exists; choose a fresh build directory.')
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='published-gallery-', dir=output.parent) as temp:
        project = Path(temp) / 'app'
        project.mkdir()
        extract_project(source, commit, project)
        seed['title'] = 'Anatomy Gallery'
        compact = json.dumps(seed, ensure_ascii=False, separators=(',', ':')).encode()
        pinned = release['snapshot']
        if len(compact) != pinned['bytes'] or hashlib.sha256(compact).hexdigest() != pinned['sha256']:
            raise ValueError('Frozen Survey seed does not reproduce the published snapshot.')
        (project / 'src/data.json').write_text(json.dumps(seed, ensure_ascii=False, indent=2) + '\n')
        gallery = project / 'src/content/gallery'
        compile_library(site, project, 'published')
        for name in ('selected-library.js', 'decode-library.js'):
            shutil.copyfile(site / 'app/src/content/gallery' / name, gallery / name)
        # The v10 source has one host switch. Adapt only its catalog reads for local rehearsal.
        replacements = {
            'Gallery.jsx': [
                ('const localPreview = isLoopbackGallery(location.hostname);', 'const localPreview = false;'),
                ('const rows = libraryRows(snapshot, teachingReview, { localPreview });', ''),
            ],
            'Planning.jsx': [("const rows = section === 'overlaps' ? libraryRows(snapshot) : [];",
                              "const rows = planning;")],
        }
        for name, changes in replacements.items():
            file = gallery / name
            body = file.read_text()
            for old, new in changes:
                if body.count(old) != 1:
                    raise ValueError(f'Published Gallery source needs a reviewed catalog adapter: {name}')
                body = body.replace(old, new)
            symbol = 'rows' if name == 'Gallery.jsx' else 'planning'
            file.write_text(f"import {{ {symbol} }} from './selected-library.js';\n" + body)
        if output.exists() or output.is_symlink():
            raise ValueError('Output was created meanwhile; refusing to replace it.')
        project.rename(output)
    return output


def verified_framework_revision(site, source):
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
    return commit


def prepare(site, source, output, viewer_inputs=None, *, seed_path=None, offline=True):
    """Create a fresh full project; never overwrite an existing destination."""
    if output.exists() or output.is_symlink():
        raise ValueError('Output already exists; choose a fresh build directory.')
    commit = verified_framework_revision(site, source)
    reference = json.loads((site / 'snapshot-reference.json').read_text())
    raw = read_seed(site, reference, seed_path)
    seed = json.loads(raw)
    # Read source, never an old ignored dist or dependency cache.
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
        extract_project(source, commit, staged, omit_overlay=True)
        for path in overlays:
            if path.suffix == '.webp':
                with path.open('rb') as stream:
                    header = stream.read(12)
                if header[:4] != b'RIFF' or header[8:] != b'WEBP':
                    raise ValueError(f'Expected a hydrated WebP image: {path.relative_to(site)}')
            target = staged / path.relative_to(site / 'app')
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, target)
        gallery = staged / 'src/content/gallery'
        if gallery.is_dir():
            from gallery_runtime import prepare_gallery
            if (gallery / 'UltrasoundDevelopment.jsx').is_file():
                from ultrasound_progress import prepare_ultrasound_progress

                prepare_ultrasound_progress(site.parents[1], gallery / 'ultrasound-progress')
            prepare_gallery(site, viewer_inputs or site / '.local/viewer-inputs', gallery, offline=offline)
            # The protected Worker at the pinned framework revision still imports this filename.
            index = gallery.parent / 'assets/delivery-index.json'
            shutil.copyfile(index, index.with_name('r2-trial.json'))
            # The immutable survey seed retains its original catalogue identity.
            seed['title'] = 'Anatomy Gallery'
            raw = (json.dumps(seed, ensure_ascii=False, indent=2) + '\n').encode()
        (staged / 'src/data.json').write_bytes(raw)
        if gallery.is_dir():
            compile_library(site, staged, 'candidate', offline=offline)
        # rename refuses an existing nonempty project; no source/history is replaced.
        if output.exists() or output.is_symlink():
            raise ValueError('Output was created meanwhile; refusing to replace it.')
        staged.rename(output)
    return output


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=SITE / '.local/publication')
    parser.add_argument('--output', type=Path, default=SITE / '.local/app')
    parser.add_argument('--viewer-inputs', type=Path, help='Directory restored by tools/gallery_runtime.py')
    parser.add_argument('--selection', choices=('candidate', 'published'), default='candidate')
    parser.add_argument('--publication-source', type=Path, help='Owner Site Git checkout containing the approved release')
    parser.add_argument('--plan-library-admission', action='store_true',
                        help='Print proposed candidate Library admission without writing a build or modifying the catalog')
    args = parser.parse_args()
    try:
        if args.plan_library_admission:
            if args.selection != 'candidate':
                parser.error('--plan-library-admission applies to the candidate.')
            plan_gallery_admission(SITE)
            sys.exit(0)
        elif args.selection == 'published':
            result = prepare_published(SITE, args.publication_source or args.source, args.output)
        else:
            result = prepare(SITE, args.source, args.output, args.viewer_inputs)
    except (ValueError, OSError, KeyError, subprocess.CalledProcessError) as error:
        parser.exit(1, f'{error}\n')
    print(f'Prepared pinned framework plus Anatomy Gallery source: {result}')
