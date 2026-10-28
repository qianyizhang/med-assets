"""Offline contract checks, never reported as target-viewer/pixel acceptance."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace
import base64
import struct

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('esophagus_probe',ROOT/'ci/esophagus/probe.py')
probe=importlib.util.module_from_spec(spec);spec.loader.exec_module(probe)
F=probe.FIXTURE


def frame(name=None, gray=False):
    name=name or probe.FRAME_IDS[0]
    variant='baseline' if '-baseline-' in name else 'candidate'
    raw=bytes([80,120,160,255])*(512*512)
    row=dict(id=name,asset=F[variant]['id'],assetSHA256=F[variant]['sha256'],width=512,height=512,
             glError=0,contextLost=False,pixelSHA256=hashlib.sha256(raw).hexdigest(),
             visibleNodes=[dict(node=i,name=l['name'],visible=True) for i,l in enumerate(F['layers'])],
             rendererInfo=dict(calls=5,triangles=2 if gray else 7700),
             materials=[dict(number=l['number'],name=l['name'],rgba=l[variant+'RGBA'],metalness=0,
                             roughness=.7200000286102295,doubleSided=True) for l in F['layers']],
             legend=dict(language='en',labels=[f"{l['number']}  {l['en']}" for l in F['layers']],
                         notice=F['baselineNotices' if variant=='baseline' else 'notices']['en'],context=F['context']['en'],attribution=F['attribution'],
                         rect=dict(x=552,y=100,width=440,height=580)))
    return row,raw


class EsophagusRuntimeTests(unittest.TestCase):
    def test_pinned_fixture_and_state_bound(self):
        self.assertEqual(F['baseline']['bytes'],201328);self.assertEqual(F['candidate']['bytes'],201344)
        self.assertEqual(F['baseline']['sha256'],'e4f51a86040ef115776fe06a33443982f7b63243332681e53dadaa77f81c05f5')
        self.assertEqual(F['candidate']['sha256'],'c7ec6420edbd62f94b85610e1c51f6fa4dd31dc008248c19a9731ac5cef0c311')
        self.assertEqual(len(probe.FRAME_IDS),18);self.assertEqual(len(set(probe.FRAME_IDS)),18)
        self.assertEqual([l['number'] for l in F['layers']],list(range(1,6)))

    def test_wrong_input_before_output_and_under_optimized_python(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);source=root/'source.glb';source.write_bytes(b'wrong');out=root/'new'
            with self.assertRaisesRegex(ValueError,'size'):probe.prepare(source,out)
            result=subprocess.run([sys.executable,'-O',str(ROOT/'ci/esophagus/probe.py'),'--input',str(source),'--output',str(out)],capture_output=True)
            self.assertNotEqual(result.returncode,0);self.assertFalse(out.exists())

    def test_no_network_or_browser_launch_in_prepare_module(self):
        code=(ROOT/'ci/esophagus/probe.py').read_text()
        self.assertNotIn('urlopen',code);self.assertNotIn('Popen(',code)

    def test_truncated_chunk_rejected(self):
        with self.assertRaises(ValueError):probe.chunks(b'glTF')

    def test_metadata_contract_does_not_claim_display_or_anatomy(self):
        row,raw=frame();result=probe.validate_frame(row,raw,{})
        self.assertTrue(result['displayMatchRequired']);self.assertTrue(result['legendActualPixelReviewRequired'])
        self.assertFalse(result['anatomicalApproval']);self.assertFalse(result['clinicalApproval'])

    def test_swapped_mapping_and_material_rejected(self):
        for field in ('visibleNodes','materials'):
            row,raw=frame();row[field][0],row[field][1]=row[field][1],row[field][0]
            with self.assertRaises(ValueError):probe.validate_frame(row,raw,{})

    def test_wrong_label_notice_context_and_offscreen_legend_rejected(self):
        for key in ('labels','notice','context','attribution','rect'):
            row,raw=frame();row['legend'][key]=({'x':1200,'y':100,'width':440,'height':580} if key=='rect' else [] if key=='labels' else 'wrong')
            with self.assertRaises(ValueError):probe.validate_frame(row,raw,{})

    def test_context_loss_hash_and_sequence_rejected(self):
        for key,value in [('contextLost',True),('pixelSHA256','0'*64),('id',probe.FRAME_IDS[1])]:
            row,raw=frame();row[key]=value
            with self.assertRaises(ValueError):probe.validate_frame(row,raw,{})

    def test_equal_candidate_pixels_do_not_pass_material_change(self):
        row,raw=frame('esophagus-candidate-oblique')
        previous={name:raw for name in probe.FRAME_IDS[:7]}
        with self.assertRaisesRegex(ValueError,'framebuffer change'):probe.validate_frame(row,raw,previous)

    def test_restore_requires_actual_pixels(self):
        row,raw=frame('esophagus-candidate-restored')
        previous={name:raw for name in probe.FRAME_IDS[:-1]}
        probe.validate_frame(row,raw,previous)
        bad=bytearray(raw);bad[0]=0;row['pixelSHA256']=hashlib.sha256(bad).hexdigest()
        with self.assertRaisesRegex(ValueError,'framebuffer change'):probe.validate_frame(row,bad,previous)

    def test_gray_derived_from_pixels_and_bad_anchor_rejected(self):
        row,source=frame('esophagus-candidate-gray-en',True)
        previous={name:source for name in probe.FRAME_IDS[:14]}
        row['anchors']=[dict(number=i+1,hitNode=i,point=l['anchor'],pixel=[int((l['anchor'][0]/.0165+1)*256+.5),int((1+l['anchor'][2]/.0165)*256+.5)]) for i,l in enumerate(F['layers'])]
        row['graySourceSHA256']=hashlib.sha256(source).hexdigest()
        lum=int(.2126*80+.7152*120+.0722*160+.5);gray=bytes([lum,lum,lum,255])*(512*512)
        gray=bytearray(gray)
        for anchor in row['anchors']:
            x,y=anchor['pixel']
            for dy in range(-5,6):
                for dx in range(-5,6):
                    j=((511-y+dy)*512+x+dx)*4;v=0 if dx<0 else 255;gray[j:j+3]=bytes([v,v,v])
        row['pixelSHA256']=hashlib.sha256(gray).hexdigest();probe.validate_frame(row,gray,previous)
        bad=bytearray(gray);bad[0]+=4;row['pixelSHA256']=hashlib.sha256(bad).hexdigest()
        with self.assertRaisesRegex(ValueError,'rendered pixels'):probe.validate_frame(row,bad,previous)
        row['pixelSHA256']=hashlib.sha256(gray).hexdigest();row['anchors'][0]['hitNode']=4
        with self.assertRaisesRegex(ValueError,'mapping'):probe.validate_frame(row,gray,previous)

    def test_display_mismatch_is_not_a_pass(self):
        row,_=frame()
        raw=bytes([80,120,160,255])*(512*256)+bytes([170,160,150,255])*(512*256)
        row['pixelSHA256']=hashlib.sha256(raw).hexdigest()
        row['rgbaBase64']=base64.b64encode(raw).decode()
        # Header validation uses dimensions; the actual displayed pixels are independently checked.
        row['canvasPNG']='data:image/png;base64,'+base64.b64encode(b'\x89PNG\r\n\x1a\n'+b'12345678'+struct.pack('>II',512,512)).decode()
        row['displayRect']=dict(x=0,y=0,width=512,height=512)
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);(root/'framebuffer').mkdir();(root/'framebuffer/Xvfb_screen0').write_bytes(b'synthetic-xwd')
            shared=SimpleNamespace(OUT=root,decode_xwd=lambda data:(1280,1024,bytes(1280*1024*3)),png=lambda w,h,p:b'png',dump=lambda *args:None)
            previous={}
            with patch('time.sleep'), self.assertRaisesRegex(ValueError,'Display screenshot'):
                probe.capture_snapshot(row,root,previous,shared)
            self.assertEqual(previous,{})

    def test_gray_missing_badge_rejected(self):
        row,source=frame('esophagus-candidate-gray-en',True)
        previous={name:source for name in probe.FRAME_IDS[:14]}
        row['anchors']=[dict(number=i+1,hitNode=i,point=l['anchor'],pixel=[int((l['anchor'][0]/.0165+1)*256+.5),int((1+l['anchor'][2]/.0165)*256+.5)]) for i,l in enumerate(F['layers'])]
        row['graySourceSHA256']=hashlib.sha256(source).hexdigest()
        lum=int(.2126*80+.7152*120+.0722*160+.5);gray=bytes([lum,lum,lum,255])*(512*512)
        row['pixelSHA256']=hashlib.sha256(gray).hexdigest()
        with self.assertRaisesRegex(ValueError,'badge'):probe.validate_frame(row,gray,previous)

    def test_zh_label_mismatch_rejected(self):
        row,source=frame('esophagus-candidate-gray-zh',True)
        previous={name:source for name in probe.FRAME_IDS[:15]}
        with self.assertRaisesRegex(ValueError,'language'):probe.validate_frame(row,source,previous)


if __name__=='__main__':unittest.main()
