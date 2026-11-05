"""Resolve the repository's retained navigation links; no media-byte claim."""
from pathlib import Path
import re
import unittest
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]
LINK = re.compile(r'\[[^\]]+\]\(([^)]+)\)')
NAVIGATION_DOCS = ('README.md', 'docs/SCOPED-STUDIES.md', 'docs/ASSET_LAYOUT.md')


class DirectoryNavigation(unittest.TestCase):
    def test_relative_links_and_fragments_resolve(self):
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
                        heading = url.fragment.replace('-', ' ')
                        self.assertIn(f'## {heading}\n', target.read_text().lower())


if __name__ == '__main__':
    unittest.main()
