"""Verify the hydrated bounded eye package; does not establish anatomy/runtime."""
import argparse
import hashlib
import json
from pathlib import Path

import glb

REVIEW=Path('reviews/eye_exterior/2026-10-30-z-native-courses-r01')
MODEL=Path('models/eye_exterior/exports/z-native-courses-r01/eye-exterior-courses.glb')
SOURCE=Path('sources/datasets/z-anatomy/eye-exterior-courses')


def run(root):
    manifest=json.loads((root/REVIEW/'payload-manifest.json').read_text())
    for row in manifest['files']:
        path=(root/row['file']).resolve()
        glb.require(path.is_relative_to(root.resolve()),'Manifest path escapes root')
        data=path.read_bytes()
        glb.require(len(data)==row['bytes'] and glb.sha(data)==row['sha256'],'Payload identity differs: '+row['file'])
    bindings=json.loads((root/REVIEW/'bindings.json').read_text())
    inventory=json.loads((root/SOURCE/'source-inventory.json').read_text())
    glb.require(len(bindings['objects'])==20 and sum(r['triangles'] for r in bindings['objects'])==35884,'Wrong bounded inventory')
    glb.require({r['name'] for r in bindings['objects']}=={r['name'] for r in inventory['objects']},'Source object mapping differs')
    for b in bindings['objects']:
        source=next(r for r in inventory['objects'] if r['name']==b['name'])
        glb.require(source['matrixWorld']==b['matrixNative'] and source['worldGeometrySha256']==b['sourceEvaluatedWorldGeometrySha256'],'Source preflight binding differs')
    checked=glb.verify((root/MODEL).read_bytes(),bindings['objects'])
    artifact_sha=glb.sha((root/MODEL).read_bytes())
    receipt=json.loads((root/REVIEW/'renders/reimport-render.json').read_text())
    composition=json.loads((root/REVIEW/'presentation/composition.json').read_text())
    glb.require(receipt['candidateSha256']==composition['candidateSha256']==artifact_sha,'Evidence bound to another artifact')
    cameras=json.loads((root/'tools/eye_exterior/cameras.json').read_text())
    for view in receipt['views']:
        source=next(r for r in cameras['views'] if r['file']==view['sourceImage'])
        glb.require(view['cameraMatrixWorld']==source['cameraMatrixWorld'] and view['orthographicScaleNativeUnits']==source['orthographicScaleNativeUnits'],'Matched camera differs')
        glb.require(view['resolution']==source['resolution'] and view['visibleSourceNames']==source['visibleSourceNames'],'View inventory/size differs')
        glb.require(min(view['frameMarginsPx'].values())>=90,'Uncropped render margin failed')
    for leader in composition['leaders']:
        view=next(r for r in receipt['views'] if r['view']==leader['view'])
        anchor=view['anchors'][leader['role']]
        glb.require(leader['sourceNode']==anchor['sourceNode']==anchor['rayHitNode'] and leader['sourcePixel']==anchor['pixel'],'Leader source binding differs')
    print(json.dumps({'files':len(manifest['files']),'objects':checked['objects'],'triangles':35884,
                      'glbSha256':artifact_sha,'matchedViews':len(receipt['views']),'boundLeaders':len(composition['leaders'])}))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True)
    run(p.parse_args().root)
