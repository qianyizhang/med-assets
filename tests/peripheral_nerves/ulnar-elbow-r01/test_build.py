import copy
import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
spec=importlib.util.spec_from_file_location('ulnar_build',HERE/'build.py')
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
V1=ROOT/'reviews/peripheral_nerves/2026-10-30-ulnar-elbow-r01/v1/native-elbow.glb'
V2=ROOT/'models/peripheral_nerves/exports/ulnar-elbow-r01/right-ulnar-elbow.glb'
EXPECTED='94a7bde3f8a2882cc632082301d7701a737a769e1d1afe0f55629ecac3013ac3'

class BuildContract(unittest.TestCase):
    def test_replay_exact(self):
        with tempfile.TemporaryDirectory() as t:
            out=Path(t)/'replay.glb';r=b.build(V1,out)
            self.assertEqual(r['outputSha256'],EXPECTED)
            self.assertEqual(out.read_bytes(),V2.read_bytes())

    def test_wrong_source_leaves_no_output(self):
        with tempfile.TemporaryDirectory() as t:
            bad=Path(t)/'bad.glb';bad.write_bytes(b'unknown asset')
            out=Path(t)/'out.glb'
            with self.assertRaisesRegex(ValueError,'Exact retained'):b.build(bad,out)
            self.assertFalse(out.exists())

    def test_existing_output_preserved(self):
        with tempfile.TemporaryDirectory() as t:
            out=Path(t)/'existing.glb';out.write_bytes(b'preserve')
            with self.assertRaises(FileExistsError):b.build(V1,out)
            self.assertEqual(out.read_bytes(),b'preserve')

    def test_mesh_binary_and_transforms_unchanged(self):
        a,abin=b.read_glb(V1);c,cbin=b.read_glb(V2)
        self.assertEqual(abin,cbin)
        for k in ['accessors','bufferViews','buffers','meshes']:
            self.assertEqual(a[k],c[k])
        strip=lambda n:{k:v for k,v in n.items() if k not in ['name','extras']}
        self.assertEqual([strip(n) for n in a['nodes']],[strip(n) for n in c['nodes']])

    def test_identity_and_limits(self):
        d,_=b.read_glb(V2);e=d['scenes'][0]['extras']
        self.assertEqual([n['extras']['source_object'] for n in d['nodes']],b.NAMES)
        self.assertEqual(e['sourceBlendSha256'],b.SOURCE_SHA)
        self.assertEqual(e['license'],'CC BY-SA 4.0')
        self.assertIn('not an old-scaffold replacement',e['limitations'])
        self.assertIn('No skin, muscle, retinaculum',e['limitations'])

    def test_invalid_header_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'truncated.glb';p.write_bytes(V2.read_bytes()[:-4])
            with self.assertRaisesRegex(ValueError,'header'):b.read_glb(p)

if __name__=='__main__':unittest.main()
