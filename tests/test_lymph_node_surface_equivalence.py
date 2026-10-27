"""Offline tests for the bounded audit; actual Blender replay remains separate."""
import copy
import importlib.util
from pathlib import Path
import sys
import unittest

TOOLS = Path(__file__).resolve().parents[1] / 'tools/lymph_node/editorial_window_r03'
spec = importlib.util.spec_from_file_location('lymph_import_audit', TOOLS / 'import_audit.py')
audit = importlib.util.module_from_spec(spec)
_original_path = sys.path[:]
try:
    spec.loader.exec_module(audit)
finally:
    sys.path[:] = _original_path

A = ((0., 0., 0.), (1., 0., 0.), (0., 1., 0.))
B = ((0., 0., 1.), (1., 0., 1.), (0., 1., 1.))
R = (B[0], B[2], B[1])


class SurfaceEquivalenceTests(unittest.TestCase):
    def test_exact_cyclic_and_reordered_faces(self):
        self.assertTrue(audit.compare_faces([A, B], [B[1:]+B[:1], A])['fullOrientedMultisetPreserved'])

    def test_declared_reverse_duplicate_is_separate_from_strict_pass(self):
        row = audit.compare_faces([A, B, R], [A, B], {audit.support(B)})
        self.assertFalse(row['fullOrientedMultisetPreserved'])
        self.assertEqual(row['oppositeWindingOccurrencesRemoved'], 1)

    def test_missing_distinct_face(self):
        with self.assertRaisesRegex(ValueError, 'Distinct surface'):
            audit.compare_faces([A, B, R], [B], {audit.support(B)})

    def test_flipped_unambiguous_face(self):
        with self.assertRaisesRegex(ValueError, 'Unambiguous winding'):
            audit.compare_faces([A, B, R], [(A[0], A[2], A[1]), B], {audit.support(B)})

    def test_moved_face(self):
        with self.assertRaisesRegex(ValueError, 'Distinct surface'):
            audit.compare_faces([A], [B])

    def test_extra_duplicate(self):
        with self.assertRaisesRegex(ValueError, 'unexpected duplicate'):
            audit.compare_faces([A], [A, A])

    def test_undeclared_duplicate_removal(self):
        with self.assertRaisesRegex(ValueError, 'unexpected duplicate'):
            audit.compare_faces([B, R], [B])

    def test_declared_pair_must_lose_exactly_one(self):
        with self.assertRaisesRegex(ValueError, 'Unexpected duplicate survival'):
            audit.compare_faces([B, R], [B, R], {audit.support(B)})

    def test_same_winding_pair_cannot_get_exception(self):
        with self.assertRaisesRegex(ValueError, 'not one opposite'):
            audit.compare_faces([B, B], [B], {audit.support(B)})

    def test_unknown_exception(self):
        with self.assertRaisesRegex(ValueError, 'Unknown duplicate'):
            audit.compare_faces([A], [A], {audit.support(B)})

    def test_material_color_alpha_and_culling_changes(self):
        before = audit.material_semantics({'name': 'tissue'})
        for material in ({'name':'tissue', 'doubleSided':True},
                         {'name':'tissue', 'alphaMode':'BLEND'},
                         {'name':'tissue', 'pbrMetallicRoughness':{'baseColorFactor':[0,1,1,1]}}):
            with self.subTest(material=material), self.assertRaisesRegex(ValueError, 'Material'):
                audit.check_materials(before, audit.material_semantics(material))

    def test_material_assignment(self):
        with self.assertRaisesRegex(ValueError, 'Material'):
            audit.check_materials(('capsule',), ('network',))

    def test_transform(self):
        with self.assertRaisesRegex(ValueError, 'transforms'):
            audit.check_transforms((0,0,0), (0,0,.001))

    def test_untraced_source_pair(self):
        raw = {'mesh': {'indices':[(0,1,2),(0,2,1)], 'faces':[B,R]}}
        with self.assertRaisesRegex(ValueError, 'not traced'):
            audit.source_pairs(raw, raw, {'mesh':[0,0]})

    def test_normal_audit_uses_face_corners_not_position_lookup(self):
        n = ((0.,0.,1.),)*3
        raw = {'faces':[B,R], 'normals':[n,tuple((-x,-y,-z) for x,y,z in n)]}
        imported = {'faces':[B], 'normals':[n]}
        self.assertEqual(audit.normal_audit(raw, imported)['changedNormalizedNormalCornersExact'], 0)
        imported['normals'] = [tuple((-x,-y,-z) for x,y,z in n)]
        self.assertEqual(audit.normal_audit(raw, imported)['negativeNormalDotCorners'], 3)

    def test_coincident_face_normal_occurrences_cannot_be_reused(self):
        up = ((0., 0., 1.),)*3
        down = ((0., 0., -1.),)*3
        raw = {'faces': [B, B], 'normals': [up, down]}
        actual = {'faces': [B, B], 'normals': [up, up]}
        row = audit.normal_audit(raw, actual)
        self.assertEqual(row['normalPreservation'], 'failed-exact-preservation')
        self.assertEqual(row['unmatchedNormalizedFaceNormalOccurrences'], 1)
        self.assertEqual(row['maxNormalizedComponentDifference'], 0)
        self.assertEqual(audit.normal_audit(raw, raw)['normalPreservation'], 'passed')


if __name__ == '__main__':
    unittest.main()
