"""Offline checks for the bounded authored surface fields, not anatomy acceptance."""
import ast
import math
from pathlib import Path
import runpy
import sys
import tempfile
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import patch

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
        cls.tree = tree

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

    def test_actual_projection_preserves_lower_region_and_xy(self):
        # Execute the retained recipe's projection block on synthetic vertices.
        # This exercises its loop and preservation guards without building a model.
        def assignment(node, name):
            return isinstance(node, ast.Assign) and any(
                isinstance(target, ast.Name) and target.id == name for target in node.targets)
        start = next(i for i, node in enumerate(self.tree.body) if assignment(node, 'original'))
        end = next(i for i, node in enumerate(self.tree.body) if assignment(node, 'orig_input'))
        class Coordinate:
            def __init__(self, z):
                self.x, self.y, self.z = .001, -.002, z
            def __iter__(self):
                return iter((self.x, self.y, self.z))
        heights = (0, .003499, .0035, .003501, .004, .0045, .006)
        vertices = [SimpleNamespace(co=Coordinate(z)) for z in heights]
        namespace = {'ob': SimpleNamespace(data=SimpleNamespace(vertices=vertices, update=lambda: None)),
                     'height': lambda x, y: 9, 'smoothstep': self.ns['smoothstep']}
        exec(compile(ast.Module(body=self.tree.body[start:end], type_ignores=[]), str(SCRIPT), 'exec'), namespace)
        for vertex, original in zip(vertices, heights):
            self.assertEqual((vertex.co.x, vertex.co.y), (.001, -.002))
            if original <= .0035:
                self.assertEqual(vertex.co.z, original)
            else:
                self.assertGreater(vertex.co.z, original)
                self.assertLessEqual(vertex.co.z, .009 + math.ulp(.009))
                if original >= .0045:
                    self.assertAlmostEqual(vertex.co.z, .009)
        self.assertEqual(namespace['changed'], 4)

    def test_actual_cli_refuses_existing_output_and_wrong_source_without_writes(self):
        modules = {name: ModuleType(name) for name in ('bpy', 'bmesh', 'numpy', 'mathutils')}
        modules['mathutils'].Vector = object
        for existing in (False, True):
            with self.subTest(existing_output=existing), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                script = root / SCRIPT.name
                script.write_bytes(SCRIPT.read_bytes())
                baseline = root / 'baseline'
                baseline.mkdir()
                source = baseline / 'FDI36-authored.glb'
                source.write_bytes(b'wrong source')
                output = root / 'candidate'
                if existing:
                    output.mkdir()
                    (output / 'keep').write_bytes(b'previous result')
                before = {str(p.relative_to(root)): p.read_bytes() for p in root.rglob('*') if p.is_file()}
                with patch.dict(sys.modules, modules), patch.object(sys, 'argv', [str(script), '--', 'candidate']):
                    with self.assertRaises(RuntimeError if existing else AssertionError):
                        runpy.run_path(str(script), run_name='__main__')
                self.assertEqual({str(p.relative_to(root)): p.read_bytes() for p in root.rglob('*') if p.is_file()}, before)
                self.assertEqual(output.exists(), existing)

if __name__ == '__main__':
    unittest.main()
