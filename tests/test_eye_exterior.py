"""Source-bound static export failures; no source downloads or Blender in CI."""
import copy
import importlib.util
from pathlib import Path
import struct
import unittest

spec = importlib.util.spec_from_file_location('eye_glb', Path(__file__).resolve().parents[1]/'tools/eye_exterior/glb.py')
glb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(glb)


class EyeExportTests(unittest.TestCase):
    def setUp(self):
        self.objects = []
        for side in ('l','r'):
            self.objects.append({'name':'Optic nerve (II).'+side,'sourceType':'CURVE','sourceParent':'Eyeball.g',
                'matrixNative':[[-1,0,0,.03125],[0,1,0,-.0625],[0,0,1,1.5],[0,0,0,1]],
                'positions':[[0,0,0],[.125,0,0],[0,.25,0]],'normals':[[0,0,1]]*3,'indices':[0,1,2]})
        self.bindings = [{k:o[k] for k in ('name','sourceType','sourceParent','matrixNative')} | {
            'triangles':1,'nativeTriangleCornersSha256':glb.corners_sha(o['positions'],o['normals'],o['indices'])} for o in self.objects]
        self.data = glb.make(self.objects, {'sha256':'a'*64})

    def test_mirrored_native_matrix_and_scene_partition_survive(self):
        result=glb.verify(self.data,self.bindings)
        self.assertEqual(result['objects'],2)
        self.assertEqual(result['defaultSourceSide'],'r')
        self.assertEqual(self.data,glb.make(copy.deepcopy(self.objects),{'sha256':'a'*64}))

    def test_vertex_tamper_rejected(self):
        doc,payload=glb.decode(self.data); payload=bytearray(payload)
        struct.pack_into('<f',payload,0,.125)
        with self.assertRaisesRegex(ValueError,'positions/normals'):
            glb.verify(glb.encode(doc,bytes(payload)),self.bindings)

    def test_normal_tamper_rejected(self):
        doc,payload=glb.decode(self.data);payload=bytearray(payload)
        index=doc['meshes'][0]['primitives'][0]['attributes']['NORMAL']
        view=doc['bufferViews'][doc['accessors'][index]['bufferView']]
        struct.pack_into('<f',payload,view['byteOffset'],.25)
        with self.assertRaisesRegex(ValueError,'positions/normals'):
            glb.verify(glb.encode(doc,bytes(payload)),self.bindings)

    def test_fitting_translation_rejected(self):
        doc,payload=glb.decode(self.data);doc['nodes'][0]['matrix'][12]+=.1
        with self.assertRaisesRegex(ValueError,'Native matrix'):
            glb.verify(glb.encode(doc,payload),self.bindings)

    def test_source_action_shader_name_rejected(self):
        doc,payload=glb.decode(self.data);doc['materials'][0]['name']='Flexion'
        with self.assertRaisesRegex(ValueError,'material semantics'):
            glb.verify(glb.encode(doc,payload),self.bindings)

    def test_opposite_side_cannot_silently_join_default_scene(self):
        doc,payload=glb.decode(self.data);doc['scenes'][0]['nodes']=[0,1]
        with self.assertRaisesRegex(ValueError,'partition'):
            glb.verify(glb.encode(doc,payload),self.bindings)

    def test_source_name_mapping_cannot_change(self):
        doc,payload=glb.decode(self.data);doc['nodes'][0]['extras']['sourceSide']='r'
        with self.assertRaisesRegex(ValueError,'provenance'):
            glb.verify(glb.encode(doc,payload),self.bindings)

    def test_missing_surface_rejected(self):
        doc,payload=glb.decode(self.data);doc['nodes'].pop()
        with self.assertRaisesRegex(ValueError,'inventory'):
            glb.verify(glb.encode(doc,payload),self.bindings)


if __name__ == '__main__':
    unittest.main()
