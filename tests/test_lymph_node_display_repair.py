"""Offline adversarial checks; actual Blender results remain separate evidence."""
import copy
import importlib.util
from pathlib import Path
import sys
import unittest
TOOLS=Path(__file__).resolve().parents[1]/'tools/lymph_node/editorial_window_r03'
spec=importlib.util.spec_from_file_location('lymph_display_repair',TOOLS/'display_repair.py')
repair=importlib.util.module_from_spec(spec)
original_path=sys.path[:]
try:spec.loader.exec_module(repair)
finally:sys.path[:]=original_path
FACE=((0.,0.,0.),(1.,0.,0.),(0.,1.,0.))
UP=((0.,0.,1.),)*3
WHITE=((1.,1.,1.,1.),)*3

def triangle_document(colors=WHITE,indices=(0,1,2)):
    doc={'meshes':[{'name':'mesh','primitives':[{'attributes':{}}]}],
         'buffers':[{'byteLength':0}],'bufferViews':[],'accessors':[]}
    binary=bytearray();primitive=doc['meshes'][0]['primitives'][0]
    for key,array in [('POSITION',FACE),('NORMAL',UP),('COLOR_0',colors)]:
        primitive['attributes'][key]=repair.append_accessor(doc,binary,array,'VEC'+str(len(array[0])),5126)
    primitive['indices']=repair.append_accessor(doc,binary,[(i,) for i in indices],'SCALAR',5125)
    doc['buffers'][0]['byteLength']=len(binary)
    return doc,bytes(binary)

class DisplayRepairTests(unittest.TestCase):
    def test_full_split_preserves_attributes_without_shared_corner_fans(self):
        doc,blob=triangle_document(indices=(0,1,2,1,0,3))
        binary=bytearray(blob);p=doc['meshes'][0]['primitives'][0]
        arrays={'POSITION':(*FACE,(0.,0.,1.)),'NORMAL':(*UP,UP[0]),'COLOR_0':(*WHITE,WHITE[0])}
        for key,array in arrays.items():
            p['attributes'][key]=repair.append_accessor(doc,binary,array,'VEC'+str(len(array[0])),5126)
        output,data,changes=repair.deindex(doc,bytes(binary),full_split=True)
        repair.compare_attributes(repair.attribute_faces(doc,bytes(binary)),repair.attribute_faces(output,data))
        primitive=output['meshes'][0]['primitives'][0]
        self.assertEqual([x[0] for x in repair.accessor(output,data,primitive['indices'])],list(range(6)))
        self.assertEqual(len(repair.values(output,data,primitive['attributes']['POSITION'])),6)
        self.assertEqual(changes,[])

    def test_rgb_implicit_alpha_is_semantically_exact(self):
        rgba=repair.attribute_faces(*triangle_document())
        rgb=repair.attribute_faces(*triangle_document(((1.,1.,1.),)*3))
        repair.compare_attributes(rgba,rgb)
        translucent=repair.attribute_faces(*triangle_document(((1.,1.,1.,.5),)*3))
        with self.assertRaisesRegex(ValueError,'vertex color'):
            repair.compare_attributes(translucent,rgb)

    def test_only_colliding_indexed_faces_are_split(self):
        doc,binary=triangle_document(indices=(0,1,2,0,2,1))
        output,blob,changes=repair.deindex(doc,binary,repair=True)
        repair.compare_attributes(repair.attribute_faces(doc,binary),repair.attribute_faces(output,blob))
        self.assertEqual(changes,[])
        p=output['meshes'][0]['primitives'][0]
        self.assertEqual(len(repair.values(output,blob,p['attributes']['POSITION'])),6)
        self.assertEqual([x[0] for x in repair.accessor(output,blob,p['indices'])],[0,1,2,3,4,5])

    def test_missing_color_attribute_rejected(self):
        doc,binary=triangle_document()
        del doc['meshes'][0]['primitives'][0]['attributes']['COLOR_0']
        with self.assertRaisesRegex(ValueError,'Missing normal or color'):
            repair.attribute_faces(doc,binary)

    def test_preserves_valid_source_normal(self):
        normal=(0.,.6,.8)
        self.assertEqual(repair.repair_normal(normal,FACE),(normal,False))

    def test_invalid_normals_use_existing_face_winding(self):
        for normal in ((0.,0.,0.),(1e-11,0.,0.)):
            self.assertEqual(repair.repair_normal(normal,FACE),((0.,0.,1.),True))
            self.assertEqual(repair.repair_normal(normal,(FACE[0],FACE[2],FACE[1])),((0.,0.,-1.),True))

    def test_intermediate_or_nonfinite_normal_rejected(self):
        for normal in ((.5,0.,0.),(float('nan'),0.,0.)):
            with self.assertRaises(ValueError):repair.repair_normal(normal,FACE)

    def test_zero_area_fallback_rejected(self):
        with self.assertRaises(ValueError):repair.repair_normal((0.,0.,0.),(FACE[0],)*3)

    def test_exact_attributes_pass(self):
        rows={'mesh':[(FACE,UP,WHITE)]}
        self.assertTrue(repair.compare_attributes(rows,rows)[0]['vertexColorsExact'])

    def test_color_and_alpha_corruption_rejected(self):
        before={'mesh':[(FACE,UP,WHITE)]}
        for color in ((.5,1.,1.,1.),(1.,1.,1.,.5)):
            with self.assertRaisesRegex(ValueError,'vertex color'):
                repair.compare_attributes(before,{'mesh':[(FACE,UP,(color,*WHITE[1:]))]})

    def test_normal_loss_and_reversal_rejected(self):
        before={'mesh':[(FACE,UP,WHITE)]}
        for normal in ((0.,0.,0.),(0.,0.,-1.)):
            with self.assertRaises(ValueError):
                repair.compare_attributes(before,{'mesh':[(FACE,(normal,*UP[1:]),WHITE)]})

    def test_geometry_and_multiplicity_rejected(self):
        before={'mesh':[(FACE,UP,WHITE)]}
        for rows in ([],[(FACE,UP,WHITE)]*2,[((FACE[0],FACE[2],FACE[1]),UP,WHITE)]):
            with self.assertRaisesRegex(ValueError,'geometry, multiplicity'):
                repair.compare_attributes(before,{'mesh':rows})

    def test_coincident_normal_occurrence_cannot_be_reused(self):
        down=((0.,0.,-1.),)*3
        before={'mesh':[(FACE,UP,WHITE),(FACE,down,WHITE)]}
        with self.assertRaisesRegex(ValueError,'Normal direction or occurrence'):
            repair.compare_attributes(before,{'mesh':[(FACE,UP,WHITE)]*2})
        self.assertEqual(repair.compare_attributes(before,before,angle_degrees=180)[0]['maxNormalAngleDegrees'],0)

    def test_declared_budget_is_not_exact_byte_identity(self):
        import math
        angle=math.radians(.02);near=((0.,math.sin(angle),math.cos(angle)),)*3
        result=repair.compare_attributes({'mesh':[(FACE,UP,WHITE)]},{'mesh':[(FACE,near,WHITE)]})
        self.assertAlmostEqual(result[0]['maxNormalAngleDegrees'],.02,places=6)

    def test_prepared_document_change_rejected(self):
        # An empty valid document isolates metadata validation from payload work.
        baseline={'meshes':[],'buffers':[{'byteLength':0}],'bufferViews':[],'accessors':[]}
        prepared=copy.deepcopy(baseline);prepared['extras']={'displayRepair':repair.repair_extras()}
        repair.validate_prepared(baseline,b'',prepared,b'')
        prepared['nodes']=[{'translation':[1,0,0]}]
        with self.assertRaisesRegex(ValueError,'pinned-input repair policy'):
            repair.validate_prepared(baseline,b'',prepared,b'')

if __name__=='__main__':unittest.main()
