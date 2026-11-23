"""Replay historical teaching reviews and collect approved recipe-built candidates."""
import hashlib
from html import unescape
import json
import posixpath
import re
from pathlib import Path
from typing import NamedTuple


REGISTER = "docs/gallery/maintained-models.md"


class Selection(NamedTuple):
    collection: str
    label: str
    family: str
    shared_owner: str | None


def register_selections(raw):
    rows = {}
    families = set()
    collection = ""
    for line in raw.splitlines():
        if line.startswith("## "):
            collection = unescape(line[3:].strip())
        if not line.startswith("|") or line in ("| Family | Starting file |", "| --- | --- |"):
            continue
        cells = line.split("|")
        if len(cells) != 4 or cells[0] or cells[-1] or not collection:
            raise ValueError(f"Unrecognized maintained register row: {line}")
        label = cells[1].strip()
        shared = re.fullmatch(r"([^|]+) · \[([^\]]+)\]\((\.\./\.\./(?:assemblies|models|heart)/[^) ]+/README\.md)\)", label)
        if not shared and ("[" in label or "]" in label):
            raise ValueError(f"Invalid shared family link: {label}")
        label, family, owner = shared.groups() if shared else (label, label, None)
        label, family = unescape(label), unescape(family)
        selection = Selection(collection, label, family, posixpath.normpath(posixpath.join("docs/gallery", owner)) if owner else None)
        if not family or (collection, family) in families:
            raise ValueError(f"Ambiguous maintained row: {line}")
        families.add((collection, family))
        for file in cells[2].strip().split("<br>"):
            match = re.fullmatch(r"\[([^\]]+)\]\(([^ )]+)\)", file.strip())
            if not match:
                raise ValueError(f"Invalid starting-file link: {file}")
            label, link = match.groups()
            path = posixpath.normpath(posixpath.join("docs/gallery", link))
            if not path.startswith(("models/", "assemblies/", "lessons/", "heart/", "body/")):
                raise ValueError(f"Invalid starting path: {path}")
            if Path(path).name != label or Path(path).suffix not in (".blend", ".glb"):
                raise ValueError(f"Invalid starting-file link: {file}")
            if path in rows:
                raise ValueError(f"Duplicate maintained selection: {path}")
            rows[path] = selection
    if not rows:
        raise ValueError("Empty maintained register")
    return rows


def register_rows(raw):
    return {path: (item.collection, item.label) for path, item in register_selections(raw).items()}


def assessment_digest(row):
    data = json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()
    return hashlib.sha256(data).hexdigest()


def refinement_rows(repo: Path):
    directory = repo / 'reviews/teaching-assessments'
    changes = {}
    for path in sorted(directory.glob('*/accepted.json')):
        batch = json.loads(path.read_text())
        if batch['schemaVersion'] != 1:
            raise ValueError(f'Unsupported refinement schema: {path}')
        for change in batch['outcomes']:
            key = change['path'], change['sha256'], change['controlAssessmentSha256']
            if key in changes:
                raise ValueError(f'Duplicate refinement: {key[0]}')
            changes[key] = path, batch, change

    for path in sorted(directory.glob('*/campaign-assessments.json')):
        batch = json.loads(path.read_text())
        if batch['schemaVersion'] != 1:
            raise ValueError(f'Unsupported assessment schema: {path}')
        for row in batch['assessments']:
            key = row['export']['path'], row['export']['sha256'], assessment_digest(row)
            if key not in changes:
                yield path, batch, row
                continue
            owner, review, change = changes.pop(key)
            yield owner, review, refined_row(row, change, review)
    if changes:
        raise ValueError(f"Refinement does not match its control export, task or assessment: {next(iter(changes))[0]}")


def refined_row(row, change, review):
    axes = [dict(axis) for axis in row['axes']]
    for axis, result in change['axisChanges'].items():
        if axis not in ('0', '1', '2', '3') or not result['observation'].strip():
            raise ValueError(f"Invalid changed axis for {change['path']}")
        score = result['score']
        if score is not None and (type(score) is not int or not 0 <= score <= 4):
            raise ValueError(f"Invalid changed score for {change['path']}")
        axes[int(axis)] = result
    views = {v['path']: v for v in row['views']}
    for view in (change['before'], change['after'], *([change['teaching']] if 'teaching' in change else [])):
        previous = views.get(view['path'])
        if previous and (previous['sha256'], previous['bytes']) != (view['sha256'], view['bytes']):
            raise ValueError(f"Refinement changes an existing view identity: {view['path']}")
        views.setdefault(view['path'], view)
    record = {
        'family': change['family'], 'group': review['group'], 'finding': change['finding'],
        'limits': change['limits'], 'beforeScores': [a['score'] for a in row['axes']],
        'before': change['before']['path'], 'after': change['after']['path'],
        'caption': change['after']['label'],
    }
    if 'candidate' in change:
        record['candidate'] = change['candidate']
    sources = list(row['sources'])
    for source in change.get('sources', []):
        if source not in sources:
            sources.append(source)
    updated = {**row, 'axes': axes, 'views': list(views.values()), 'sources': sources,
               'decision': change['decision'], 'refinement': record}
    teaching = change.get('teaching') or (change['after'] if change.get('useAsTeachingView') else None)
    if teaching:
        updated['teachingView'] = teaching['path']
        updated['views'] = [{**v, 'label': teaching['label']} if v['path'] == teaching['path'] else v
                            for v in updated['views']]
    return updated


def campaign_rows(repo: Path):
    rows = list(refinement_rows(repo))
    directory = repo / 'reviews/teaching-assessments'
    owner = directory / 'target-standard.json'
    if not owner.is_file():
        yield from rows
        return
    review = json.loads(owner.read_text())
    if review['schemaVersion'] != 1:
        raise ValueError(f'Unsupported teaching target schema: {owner}')
    rows = list(target_round(repo, rows, sorted(directory.glob('target-*/decisions.json')), review))
    yield from target_round(repo, rows, sorted(directory.glob('reopen-*/decisions.json')), review, reopened=True)


def target_round(repo, rows, paths, review, *, reopened=False):
    """Resolve decision pins against the immediately preceding assessed state."""
    by_digest = {assessment_digest(row): row for _, _, row in rows}
    selected = {}
    controls = set()
    for path in paths:
        for item in json.loads(path.read_text()):
            control = by_digest.get(item['controlAssessmentSha256'])
            assessed = by_digest.get(item['assessmentSha256'])
            if (control is None or assessed is None or control['export']['path'] != item['baseline']
                    or assessed['export']['path'] != item['path']):
                raise ValueError(f"Teaching target differs from its reviewed file or task: {item['family']}")
            if reopened:
                previous = control.get('target', {})
                if (not previous.get('exemptions') or previous['family'] != item['family']
                        or set(item['reviewedAxes']) != set(previous['exemptions'])):
                    raise ValueError(f"Reopened axes differ from the preceding exemptions: {item['family']}")
            key = item['assessmentSha256']
            if key in selected or item['baseline'] in controls:
                raise ValueError(f"Duplicate teaching target: {item['path']}")
            controls.add(item['baseline'])
            axes = list(assessed['axes'])
            for index, result in item.get('axisChanges', {}).items():
                if (index not in ('0', '1', '2', '3') or type(result.get('score')) is not int
                        or not 0 <= result['score'] <= 4 or not result.get('observation', '').strip()):
                    raise ValueError(f"Invalid target assessment axis: {item['family']}")
                axes[int(index)] = result
            low = {str(i) for i, axis in enumerate(axes) if axis['score'] is None or axis['score'] < 3}
            exceptions = item['exemptions']
            if low != set(exceptions) or any(
                not value.get(field, '').strip() for value in exceptions.values()
                for field in ('reason', 'permittedUse', 'reopen')
            ):
                raise ValueError(f"Unresolved teaching target axes: {item['family']}")
            if (not item['taskCheck'].strip() or item['status'] not in ('passed', 'blocked')
                    or not item['evidence']):
                raise ValueError(f"Missing learner action or outcome: {item['family']}")
            sources = list(assessed['sources'])
            for name in item['evidence']:
                source = (repo / name).resolve()
                if source != repo / name or not source.is_relative_to(repo) or not source.is_file():
                    raise ValueError(f'Missing target evidence: {name}')
                if name not in {ref.get('path') for ref in sources} and Path(name).suffix not in ('.png', '.jpg', '.webp'):
                    sources.append({'path': name, 'label': 'Target evidence · ' + Path(name).parent.name + '/' + Path(name).name})
            target = {field: item[field] for field in ('family', 'baseline', 'taskCheck', 'status', 'exemptions')}
            views = {v['path']: v for v in assessed['views']}
            for witness in (item['before'], item['after'], *([item['teaching']] if 'teaching' in item else [])):
                prior = views.get(witness['path'])
                if prior and (prior['sha256'], prior['bytes']) != (witness['sha256'], witness['bytes']):
                    raise ValueError(f"Conflicting target witness: {witness['path']}")
                views.setdefault(witness['path'], witness)
            if reopened:
                target['reviewedAxes'] = item['reviewedAxes']
                target['familyBaseline'] = previous.get('familyBaseline', previous['baseline'])
                if item.get('workItem'):
                    target['workItem'] = item['workItem']
            target['before'] = item['before']['path']
            target['after'] = item['after']['path']
            target['beforeScores'] = [a['score'] for a in control['axes']]
            target['controlSha256'] = control['export']['sha256']
            result = {**assessed, 'target': target, 'axes': axes, 'sources': sources, 'views': list(views.values())}
            if 'teaching' in item:
                result['teachingView'] = item['teaching']['path']
            if 'decision' in item:
                result['decision'] = item['decision']
            if 'refinement' in assessed:
                result['refinement'] = {**assessed['refinement'],
                                        'reviewedScores': assessed['refinement'].get('reviewedScores', [a['score'] for a in assessed['axes']]),
                                        'decision': assessed['refinement'].get('decision', assessed['decision'])}
            selected[key] = path, review, result
    for original in rows:
        yield selected.get(assessment_digest(original[2]), original)


def collect_candidates(repo, directories):
    """Install only reviewed recipe outputs into the loopback preview's content store."""
    import os
    from tempfile import NamedTemporaryFile
    from maintained_teaching import CurrentTeaching

    repo = repo.resolve()
    current = CurrentTeaching(repo)
    maintained = current.maintained_exports()
    wanted = {}
    for assessment in current.gallery():
        item = assessment.row.get('refinement', {}).get('candidate')
        if (item and item.get('download') and item['path'].startswith('.artifacts/teaching-refinements/candidates/')
                and (item['sha256'], item['bytes']) not in maintained):
            wanted[item['sha256']] = item
    if not wanted:
        return 0, []
    destination = repo / '.artifacts/teaching-refinements/candidates'
    if destination.resolve() != destination:
        raise ValueError(f'Linked candidate directory: {destination}')
    destination.mkdir(parents=True, exist_ok=True)
    pending = set(wanted)
    for digest in wanted:
        target = destination / (digest + '.glb')
        if target.is_symlink() or (target.exists() and hashlib.sha256(target.read_bytes()).hexdigest() != digest):
            raise ValueError(f'Existing candidate differs: {target}')
        if target.is_file():
            pending.remove(digest)
    for folder in directories:
        for path in folder.rglob('*.glb') if folder.is_dir() else [folder]:
            if path.is_symlink() or not path.is_file():
                continue
            raw = path.read_bytes()
            digest = hashlib.sha256(raw).hexdigest()
            if digest not in pending:
                continue
            target = destination / (digest + '.glb')
            if len(raw) != wanted[digest]['bytes']:
                raise ValueError(f'Candidate size differs: {path}')
            with NamedTemporaryFile(dir=destination) as stage:
                stage.write(raw)
                stage.flush()
                try:
                    os.link(stage.name, target)
                except FileExistsError:
                    if target.is_symlink() or hashlib.sha256(target.read_bytes()).hexdigest() != digest:
                        raise ValueError(f'Existing candidate differs: {target}')
            pending.remove(digest)
    return len(wanted) - len(pending), sorted(pending)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Collect verified recipe-built GLBs for the local Gallery.')
    parser.add_argument('outputs', type=Path, nargs='+', help='Review recipe output directories or individual GLBs')
    args = parser.parse_args()
    count, missing = collect_candidates(Path(__file__).resolve().parents[1], args.outputs)
    print(f'{count} approved candidates available. {len(missing)} have not been rebuilt.')
