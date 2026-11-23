"""Restore verified Gallery inputs and build a fresh candidate or published rehearsal."""

import argparse
import io
import json
from pathlib import Path
import subprocess
import tempfile
import zipfile

from framework import SITE, prepare, prepare_published, read_seed, verified_framework_revision
from gallery_runtime import restore_viewer
from med_assets.artifacts import verify_bytes
from restore_snapshot import restore


def present(path):
    return path.exists() or path.is_symlink()


def restore_backup(site, backup, scratch, *, framework=None, seed=None):
    if backup is None:
        raise ValueError('Missing framework or Survey seed. Supply the frozen recovery ZIP with --backup.')
    resource = json.loads((site / 'framework.lock.json').read_text())['backup']
    with backup.open('rb') as handle:
        raw = verify_bytes(handle.read(resource['bytes'] + 1), {**resource, 'path': backup.name})
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        if framework is not None:
            bundle = scratch / 'framework.bundle'
            bundle.write_bytes(archive.read('model-survey-backup/framework.bundle'))
            with tempfile.TemporaryDirectory(prefix='gallery-framework-', dir=framework.parent) as temp:
                recovered = Path(temp) / 'framework'
                subprocess.run(['git', 'clone', '--no-checkout', '--quiet', str(bundle), str(recovered)], check=True)
                verified_framework_revision(site, recovered)
                if present(framework):
                    raise ValueError('Framework recovery cache appeared during restore. Retry the build.')
                recovered.rename(framework)
        if seed is not None:
            archived_seed = scratch / 'archived-seed.json'
            archived_seed.write_bytes(archive.read('model-survey-backup/app/src/data.json'))
            restore(archived_seed, seed, site=site)


def bootstrap(site, output, *, selection, source=None, seed_input=None,
              viewer_inputs=None, backup=None, offline=False):
    if present(output):
        raise ValueError('Output already exists; choose a fresh build directory.')
    if selection == 'published' and source is None:
        raise ValueError('Published rehearsal needs --source pointing to the exact Site Git checkout.')

    output.parent.mkdir(parents=True, exist_ok=True)
    cache = site / '.local/bootstrap'
    with tempfile.TemporaryDirectory(prefix='gallery-build-', dir=output.parent) as temporary:
        scratch = Path(temporary)
        source_recovery = None
        if source is None:
            source = site / '.local/publication'
            if not present(source):
                source = cache / 'framework'
                if not present(source):
                    source_recovery = source
        seed_recovery = None
        if seed_input is None:
            seed = site / 'app/src/data.json'
            if not present(seed):
                seed = cache / 'data.json'
                if not present(seed):
                    seed_recovery = seed
        else:
            seed = scratch / 'data.json'
            restore(seed_input, seed, site=site)
        if source_recovery is not None or seed_recovery is not None:
            cache.mkdir(parents=True, exist_ok=True)
            restore_backup(site, backup, scratch, framework=source_recovery, seed=seed_recovery)

        project = scratch / 'app'
        if selection == 'published':
            prepare_published(site, source, project, seed_path=seed)
        else:
            inputs = site / '.local/viewer-inputs' if viewer_inputs is None else viewer_inputs
            if not present(inputs):
                if offline:
                    raise ValueError('Missing pinned viewer inputs in offline mode. Run without --offline to restore them.')
                # Resolve local prerequisites before downloading viewer inputs.
                verified_framework_revision(site, source)
                reference = json.loads((site / 'snapshot-reference.json').read_text())
                read_seed(site, reference, seed)
                restore_viewer(site, inputs)
            prepare(site, source, project, inputs, seed_path=seed, offline=offline)

        npm_flags = ['--offline'] if offline else []
        subprocess.run(['npm', 'ci', '--no-audit', '--no-fund', *npm_flags], cwd=project, check=True)
        subprocess.run(['npm', 'run', 'build'], cwd=project, check=True)
        if not (project / 'dist/index.html').is_file():
            raise ValueError('Gallery build did not produce dist/index.html.')
        if present(output):
            raise ValueError('Output was created meanwhile; refusing to replace it.')
        project.rename(output)
    return output


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--selection', choices=('candidate', 'published'), default='candidate')
    parser.add_argument('--output', type=Path, required=True, help='Fresh directory for the built app')
    parser.add_argument('--source', type=Path, help='Local Git repository holding the pinned framework or exact publication')
    parser.add_argument('--viewer-inputs', type=Path, help='Pinned viewer input directory for the candidate')
    parser.add_argument('--seed', type=Path, help='Verified source seed or immutable snapshot')
    parser.add_argument('--backup', type=Path, help='Frozen ZIP from framework.lock.json for missing framework or seed')
    parser.add_argument('--offline', action='store_true', help='Use verified local inputs and populated npm and uv caches')
    args = parser.parse_args()
    if args.selection == 'published' and args.viewer_inputs is not None:
        parser.error('--viewer-inputs applies to the candidate build.')
    try:
        result = bootstrap(SITE, args.output, selection=args.selection, source=args.source,
                           seed_input=args.seed, viewer_inputs=args.viewer_inputs, backup=args.backup,
                           offline=args.offline)
    except (ValueError, OSError, KeyError, subprocess.CalledProcessError, zipfile.BadZipFile) as error:
        parser.exit(1, f'Gallery bootstrap failed: {error}\n')
    print(f'Built Anatomy Gallery {args.selection}: {result}')
