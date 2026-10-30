"""Failure controls for lossless source composition, runnable without LFS media."""
import copy
import importlib.util
import json
from pathlib import Path
import struct
import tempfile
import unittest

PATH=Path(__file__).resolve().parents[1]/'tools/ovary_tubal/build.py'
SPEC=importlib.util.spec_from_file_location('ovary_tubal_build',PATH)
build=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(build)


def sample(name,shift):
    points=struct.pack('<fffffffff',shift,0,0,shift+1,0,0,shift,1,0)
    payload=points+struct.pack('<HHH',0,1,2)+b'\0\0'
    doc={'asset':{'version':'2.0'},'scene':0,'scenes':[{'nodes':[0]}],
         'nodes':[{'name':name,'children':[1]},{'name':name+' surface','mesh':0}],
         'meshes':[{'name':name+' mesh','primitives':[{'attributes':{'POSITION':0},'indices':1,'material':0}]}],
         'accessors':[{'bufferView':0,'componentType':5126,'count':3,'type':'VEC3'},
                      {'bufferView':1,'componentType':5123,'count':3,'type':'SCALAR'}],
         'bufferViews':[{'buffer':0,'byteLength':36},{'buffer':0,'byteOffset':36,'byteLength':6}],
         'buffers':[{'byteLength':len(payload)}],'materials':[{'name':name+' material','pbrMetallicRoughness':{'roughnessFactor':.3}}]}
    return {'file':name+'.glb','sha256':build.sha(build.encode(doc,payload)),'document':doc,'payload':payload}


class OvaryTubalPreservationTests(unittest.TestCase):
    def setUp(self):
        self.sources=[sample('one',0),sample('two',5)]
        self.data=build.combine(self.sources)

    def alter(self,edit):
        doc,payload=build.decode(self.data);edit(doc);return build.encode(doc,payload)

    def test_both_native_graphs_and_binary_payloads_survive(self):
        report=build.validate(self.sources,self.data)
        doc,payload=build.decode(self.data)
        self.assertEqual(report['sourceRoots'],[0,2])
        self.assertEqual(doc['nodes'][2]['children'],[3])
        self.assertEqual(payload,self.sources[0]['payload']+self.sources[1]['payload'])
        self.assertEqual(build.combine(self.sources),self.data)

    def test_source_binary_corruption_fails(self):
        doc,payload=build.decode(self.data);bad=bytearray(payload);bad[1]^=1
        with self.assertRaisesRegex(ValueError,'BIN changed'):build.validate(self.sources,build.encode(doc,bytes(bad)))

    def test_per_object_fitting_fails(self):
        bad=self.alter(lambda d:d['nodes'][3].update(translation=[.002,0,0]))
        with self.assertRaisesRegex(ValueError,'nodes changed'):build.validate(self.sources,bad)

    def test_dropped_source_mesh_fails(self):
        bad=self.alter(lambda d:d['meshes'].pop())
        with self.assertRaisesRegex(ValueError,'meshes changed'):build.validate(self.sources,bad)

    def test_changed_native_name_fails(self):
        bad=self.alter(lambda d:d['nodes'][3].update(name='invented side'))
        with self.assertRaisesRegex(ValueError,'nodes changed'):build.validate(self.sources,bad)

    def test_source_material_change_fails(self):
        bad=self.alter(lambda d:d['materials'][1]['pbrMetallicRoughness'].update(roughnessFactor=.9))
        with self.assertRaisesRegex(ValueError,'materials changed'):build.validate(self.sources,bad)

    def test_root_reparenting_fails(self):
        bad=self.alter(lambda d:d['scenes'][0].update(nodes=[0]))
        with self.assertRaisesRegex(ValueError,'root hierarchy changed'):build.validate(self.sources,bad)

    def test_unhydrated_source_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);manifest=root/build.MANIFEST;manifest.parent.mkdir(parents=True)
            (root/'source.glb').write_bytes(b'version https://git-lfs.github.com/spec/v1\n')
            manifest.write_text(json.dumps({'models':['source.glb']*4,'files':[{'file':'source.glb','size':9000,'sha256':'0'*64,'gitBlobSha1':'0'*40}]}))
            with self.assertRaisesRegex(ValueError,'identity mismatch'):build.read_sources(root)

    def test_existing_export_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'retained.glb';path.write_bytes(b'keep')
            with self.assertRaisesRegex(ValueError,'already exists'):build.run(Path(temp),path)
            self.assertEqual(path.read_bytes(),b'keep')


if __name__=='__main__':unittest.main()
