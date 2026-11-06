"""Offline checks for the bounded authored surface fields, not anatomy acceptance."""
import ast
import math
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'experiments/dental/fdi36-surface-cleanup/revise_surface.py'

class SurfaceFieldTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        tree = ast.parse(SCRIPT.read_text())
        names = {'G', 'RIDGES', 'FOSSAE'}
        functions = {'segdist', 'smoothstep', 'groove', 'feature_height'}
        selected = [node for node in tree.body if
                    isinstance(node, ast.FunctionDef) and node.name in functions or
                    isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id in names for t in node.targets)]
        cls.ns = {'math': math}
        exec(compile(ast.Module(body=selected, type_ignores=[]), str(SCRIPT), 'exec'), cls.ns)
        cls.source = SCRIPT.read_text()

    def test_groove_blend_never_deepens_original_maximum(self):
        for i in range(-22, 23):
            for j in range(-19, 20):
                x, y = i / 4, j / 4
                depths = [d * math.exp(-(min(self.ns['segdist'](x,y,a,b) for a,b in zip(line,line[1:]))/w)**2)
                          for line,w,d in self.ns['G']]
                actual = self.ns['groove'](x,y)
                self.assertTrue(math.isfinite(actual))
                self.assertGreaterEqual(actual, 0)
                self.assertLessEqual(actual, max(depths) + 1e-14)

    def test_no_second_negative_fossa_field(self):
        self.assertEqual(self.ns['FOSSAE'], [])
        for i in range(-22, 23):
            for j in range(-19, 20):
                self.assertGreaterEqual(self.ns['feature_height'](i/4,j/4), 0)

    def test_ridge_controls_have_semantic_names(self):
        self.assertEqual({r[0] for r in self.ns['RIDGES']}, {
            'MB_triangular_ridge','DB_triangular_ridge','ML_triangular_ridge',
            'DL_triangular_ridge','Mesial_marginal_ridge','Distal_marginal_ridge'})

    def test_projection_keeps_lower_region_and_xy_assertions(self):
        self.assertIn('if z<=3.5:continue', self.source)
        self.assertIn('assert all(tuple(v.co)==p', self.source)
        self.assertIn('assert all(v.co.x==p[0] and v.co.y==p[1]', self.source)
        self.assertIn("source_check['decoded_triangles_sha256']", self.source)

    def test_fail_closed_output_and_canonical_source(self):
        self.assertIn("if OUT.exists():raise RuntimeError", self.source)
        self.assertIn("54b29904746bf0a53a96143326e09cef84995d2e40a29cd1da634b43908fe38c", self.source)
        self.assertIn("7bb59a58776c4dcfc6e4d7de2792576c62a4322c5b9f7deef0dfda5abfb078e5", self.source)

if __name__ == '__main__':
    unittest.main()
