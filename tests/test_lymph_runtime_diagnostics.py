"""Receipt rejection tests only; actual renderer mutations require the reviewed job."""
import base64
import copy
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import unittest
from unittest import mock
import sys
import tempfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('lymph_diagnostics', ROOT/'ci/lymph_diagnostics.py')
d = importlib.util.module_from_spec(spec)
spec.loader.exec_module(d)
sys.path.insert(0, str(ROOT/'ci'))
import glb_runtime_probe as probe
sys.path.pop(0)


class LymphDiagnosticTests(unittest.TestCase):
    def setUp(self):
        self.fixture = json.loads((ROOT/'ci/glb-runtime-fixture.json').read_text())
        rows = []
        for asset in ('lymph', 'lymphCandidate'):
            sha = self.fixture['lymphCandidate']['sha256'] if asset == 'lymphCandidate' else next(
                x['sha256'] for x in self.fixture['resources'] if x.get('id') == asset)
            for i in range(7):
                rows.append(dict(asset=asset, assetSHA256=sha, mesh=str(i), referencedVertices=3,
                                 nonfinite=0, zero=0, nonunit=0, minLength=1, maxLength=1,
                                 triangles=1, degenerateTriangles=0, opposedNormalCorners=0, frontSide=True))
        self.report = dict(normalDiagnostics=rows, normalPolicy={'zeroEpsilon': 1e-6, 'unitTolerance': 1e-3},
                           orbitSamples=[{'id': k, 'direction': v} for k, v in d.SAMPLES])
        self.baseline = dict(id='lymph-source-normal-front', asset='lymph', diagnostic='normal-front',
                             camera=dict(min=[-1]*3, max=[1]*3, target=[0]*3, orthographicSpan=2.4,
                                         cameraPosition=[x/math.sqrt(5.25)*4 for x in [1, .5, 2]]),
                             culling=dict(enabled=True, mode=1029, frontFace=2305))

    def test_candidate_zero_nonunit_nonfinite_and_missing_reports_fail(self):
        self.assertEqual(len(d.validate_normals(self.report, self.fixture)), 14)
        for key, val in [('zero', 1), ('nonunit', 1), ('nonfinite', 1), ('minLength', 0),
                         ('maxLength', 2), ('minLength', float('nan')), ('frontSide', False),
                         ('assetSHA256', 'wrong'), ('triangles', 0), ('opposedNormalCorners', 4)]:
            with self.subTest(key=key):
                bad = copy.deepcopy(self.report); bad['normalDiagnostics'][-1][key] = val
                with self.assertRaises(ValueError): d.validate_normals(bad, self.fixture)
        for mutate in [lambda r: r['normalDiagnostics'].pop(),
                       lambda r: r['normalDiagnostics'][-1].update(mesh='0'),
                       lambda r: r['orbitSamples'].pop()]:
            bad = copy.deepcopy(self.report); mutate(bad)
            with self.assertRaises(ValueError): d.validate_normals(bad, self.fixture)

    def test_inherited_source_zero_and_opposed_corners_are_observations(self):
        row = self.report['normalDiagnostics'][0]
        row.update(zero=1, minLength=0, opposedNormalCorners=3)
        d.validate_normals(self.report, self.fixture)
        # The same validity defect is forbidden in the candidate; opposition alone
        # remains descriptive, since this is not an anatomical outward-direction test.
        self.report['normalDiagnostics'][-1]['opposedNormalCorners'] = 3
        d.validate_normals(self.report, self.fixture)

    def test_camera_scale_and_gl_culling_mismatches_fail(self):
        d.validate_frame(self.baseline, self.baseline)
        for key, value in [('enabled', False), ('mode', 1028), ('frontFace', 2304)]:
            row = copy.deepcopy(self.baseline); row['culling'][key] = value
            with self.assertRaises(ValueError): d.validate_frame(row, self.baseline)
        for key in ('target', 'cameraPosition'):
            row = copy.deepcopy(self.baseline); row['camera'][key][0] += .01
            with self.assertRaises(ValueError): d.validate_frame(row, self.baseline)
        row = copy.deepcopy(self.baseline); row['id'] = 'lymph-source-normal-back'
        row['diagnostic'] = 'normal-back'; row['culling']['frontFace'] = 2304
        d.validate_frame(row, self.baseline)

    def test_fixed_orbits_and_mutation_receipts(self):
        for name in d.ORBIT_IDS:
            row = copy.deepcopy(self.baseline); row['id'] = name
            sample = next(k for k, _ in d.SAMPLES if '-'+k+'-' in name)
            row['orbitSample'] = sample
            vec = dict(d.SAMPLES)[sample]; norm = math.sqrt(sum(x*x for x in vec))
            row['camera']['cameraPosition'] = [x/norm*4 for x in vec]
            row['asset'] = 'lymph' if '-source-' in name else 'lymphCandidate'
            if name.endswith('-back'):
                row['diagnostic'] = 'normal-back'; row['culling']['frontFace'] = 2304
            d.validate_frame(row, self.baseline)
        row = copy.deepcopy(self.baseline)
        row.update(id='lymph-control-negated-normals', asset='lymphCandidate')
        with self.assertRaises(ValueError): d.validate_frame(row, self.baseline)
        row.update(negativeControl='negated-normals', mutatedInMemory=True)
        d.validate_frame(row, self.baseline)

    def test_noop_mutation_and_imperfect_restore_are_rejected(self):
        # These injected counts test the gate, not real renderer sensitivity.
        previous = {'lymph-candidate-normal-front': b'baseline'}
        for kind in d.CONTROLS:
            name = 'lymph-control-'+kind
            for changed in (0, 99):
                with self.assertRaises(ValueError):
                    d.control_difference(name, b'', previous, lambda a, b: changed)
            self.assertEqual(d.control_difference(name, b'', previous, lambda a, b: 100), 100)
            self.assertEqual(d.control_difference(name+'-restored', b'', previous, lambda a, b: 0), 0)
            with self.assertRaises(ValueError):
                d.control_difference(name+'-restored', b'', previous, lambda a, b: 1)


    def test_host_rejects_noop_control_before_display_capture(self):
        name = 'lymph-control-negated-normals'
        raw = bytes([0, 0, 0, 255]) + bytes([255, 255, 255, 255])*1000 + bytes([0, 0, 0, 255])*(512*512-1001)
        previous = dict.fromkeys(probe.FRAME_IDS[:probe.FRAME_IDS.index(name)], raw)
        row = copy.deepcopy(self.baseline)
        row.update(id=name, asset='lymphCandidate', assetSHA256=self.fixture['lymphCandidate']['sha256'],
                   width=512, height=512, glError=0, contextLost=False, negativeControl='negated-normals',
                   mutatedInMemory=True, visibleNodes=[dict(layer, visible=True) for layer in self.fixture['lymph']['layers']],
                   rendererInfo={'calls': 7, 'triangles': 167367}, rgbaBase64=base64.b64encode(raw).decode(),
                   pixelSHA256=hashlib.sha256(raw).hexdigest(),
                   canvasPNG='data:image/png;base64,'+base64.b64encode(probe.png(512,512,bytes(512*512*3))).decode())
        with tempfile.TemporaryDirectory() as directory, mock.patch.object(probe, 'OUT', Path(directory)):
            with self.assertRaisesRegex(ValueError, 'Renderer negative control/restoration failed'):
                probe.verify_snapshot(row, self.fixture, Path(directory), previous, self.baseline)
        self.assertNotIn(name, previous)

    def test_contact_sheet_binds_twenty_tiles_and_flips_gl_origin(self):
        # Bottom row black, top half red: a vertically inverted thumbnail fails.
        raw = bytes([0,0,0,255])*(512*256) + bytes([255,0,0,255])*(512*256)
        previous = dict.fromkeys(d.NORMAL_IDS+d.CONTROL_IDS, raw)
        thumbs = []
        def encode(width, height, rgb):
            thumbs.append(rgb)
            return probe.png(width, height, rgb)
        sheet, cells = d.contact_sheet(previous, encode)
        xml = ET.fromstring(sheet)
        self.assertEqual(len(xml.findall('{http://www.w3.org/2000/svg}image')), 20)
        self.assertEqual([x['frame'] for x in cells], d.NORMAL_IDS+d.CONTROL_IDS)
        self.assertTrue(all(x['readPixelsSHA256'] == hashlib.sha256(raw).hexdigest() for x in cells))
        self.assertEqual(thumbs[0][:3], bytes([255,0,0]))
        self.assertEqual(thumbs[0][-3:], bytes([0,0,0]))
        self.assertIn(b'CC BY 4.0', sheet)


if __name__ == '__main__': unittest.main()
