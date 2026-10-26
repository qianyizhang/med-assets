"""Offline documentation checks; LFS pointers are not treated as verified payloads."""
import hashlib
from pathlib import Path
import re
import subprocess
import tempfile
import unittest
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]
OVERVIEW = ROOT / 'docs/SCOPED-STUDIES.md'
LINK = re.compile(r'\[[^\]]+\]\(([^)]+)\)')
NAVIGATION_DOCS = ('README.md', 'docs/SCOPED-STUDIES.md', 'docs/ASSET_LAYOUT.md')


class HistoricalOverview(unittest.TestCase):
    # Characterized before the navigation change at main 6fd567d (includes PR87).
    # These are frozen historical evidence, not a registry for future additions.
    # An intentional correction needs review of the changed content and digest.
    def test_existing_entries_headings_and_limits_are_preserved(self):
        text = OVERVIEW.read_text()
        snapshot = text[text.index('Snapshot:'):]
        rows = [line for line in snapshot.splitlines() if line.startswith('| ') and '[GLB]' in line]
        self.assertEqual(len(rows), 36)
        self.assertEqual(len(LINK.findall(snapshot)), 91)
        self.assertEqual(hashlib.sha256(snapshot.encode()).hexdigest(),
                         '7ed304da9123f55bef8ec3978ff8bfb252ea8b3610be6d96186078b593bb0399')

    def test_linked_status_evidence_and_provenance_are_preserved(self):
        text = OVERVIEW.read_text()
        snapshot = text[text.index('Snapshot:'):]
        records = []
        for link in sorted(set(LINK.findall(snapshot))):
            path = OVERVIEW.parent / link
            with self.subTest(link=link):
                self.assertTrue(path.is_file(), link)
            if path.suffix in {'.json', '.md'}:
                records.append(f'{link} {hashlib.sha256(path.read_bytes()).hexdigest()}')
        self.assertEqual(len(records), 55)
        self.assertEqual(hashlib.sha256('\n'.join(records).encode()).hexdigest(),
                         'a2e337912fba52c84b50328935dd8c3822aad0411e7185bdf32a556adfda693b')


class DirectoryNavigation(unittest.TestCase):
    def test_relative_links_and_new_fragments_resolve(self):
        for name in NAVIGATION_DOCS:
            doc = ROOT / name
            for link in LINK.findall(doc.read_text()):
                url = urlsplit(link)
                if url.scheme or url.netloc:
                    continue
                target = doc.parent / unquote(url.path) if url.path else doc
                with self.subTest(doc=name, link=link):
                    self.assertTrue(target.exists(), link)
                    if url.fragment:
                        # These navigation docs use simple heading fragments.
                        heading = url.fragment.replace('-', ' ')
                        self.assertIn(f'## {heading}\n', target.read_text().lower())
            # Every entry point exposes all four directories, not just old rows.
            destinations = {(doc.parent / urlsplit(link).path).resolve()
                            for link in LINK.findall(doc.read_text())}
            for directory in ('reviews', 'models', 'diagrams', 'assemblies'):
                self.assertIn(ROOT / directory, destinations)

    def test_two_independent_studies_merge_without_shared_edits(self):
        # Text-only fixtures exercise discovery and Git, not real asset approval.
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)

            def git(*args):
                return subprocess.run(
                    ['git', '-c', 'user.name=Navigation Test',
                     '-c', 'user.email=navigation@example.invalid',
                     '-c', 'commit.gpgsign=false', '-c', 'core.hooksPath=/dev/null',
                     *args], cwd=root, check=True, capture_output=True, text=True).stdout

            for name in NAVIGATION_DOCS:
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes((ROOT / name).read_bytes())
            git('init', '--initial-branch=base')
            git('add', '.')
            git('commit', '-m', 'Navigation fixture')
            expected = set()
            for study in ('synthetic-a', 'synthetic-b'):
                git('switch', '-c', study, 'base')
                review = f'reviews/{study}/run/README.md'
                model = f'models/{study}/exports/r01/README.md'
                for name, text in (
                    (review, f'# {study}\n\nSynthetic, unreviewed; no asset approval.\n'),
                    (model, f'# {study}\n\n[Status and limits](../../../../{review})\n'),
                ):
                    path = root / name
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text(text)
                    expected.add(name)
                git('add', '.')
                git('commit', '-m', f'Add {study} entry')
            git('merge', '--no-edit', 'synthetic-a')
            self.assertEqual(set(git('diff', '--name-only', 'base', 'HEAD').splitlines()), expected)
            self.assertEqual({p.name for p in (root / 'reviews').iterdir()},
                             {'synthetic-a', 'synthetic-b'})
            for name in expected:
                self.assertTrue((root / name).is_file())
            for name in NAVIGATION_DOCS:
                self.assertEqual((root / name).read_bytes(), (ROOT / name).read_bytes())


if __name__ == '__main__':
    unittest.main()
