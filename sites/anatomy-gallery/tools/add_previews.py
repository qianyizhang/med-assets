"""Attach bounded, source-labelled preview derivatives; preserve survey identities."""
import base64
import os
import hashlib
import io
import json
import subprocess
from pathlib import Path
from PIL import Image, ImageOps, ImageDraw

OUT=Path(__file__).resolve().parents[1]
ROOT=Path(os.environ.get("MED_ASSETS_REPO", OUT.parents[1])).expanduser().resolve()
SNAPSHOT=OUT/'app/src/data.json'
FILES=set(subprocess.check_output(['git','ls-files'],cwd=ROOT,text=True).splitlines())
DATA=json.loads(SNAPSHOT.read_text())
BASE='https://github.com/qianyizhang/med-assets/blob/'+DATA['survey']['revision']+'/'
FRESH=OUT/'.local/preview-renders'

# Explicit selections keep related source models, prototypes and current exports separate.
PICKS={
'adipose-context':['models/adipose-context/r01/comparison-en.png'],
'aorta':['reviews/readonly-audits/torso-readonly-audit-20261023/aorta-diagnostic-contact.png'],
'aortic_tree_z':['reviews/aortic_tree_z/2026-10-29-arch-locators/overview-comparison.png','reviews/aortic_tree_z/2026-10-29-arch-locators/junction-comparison.png'],
'bone_marrow':['reviews/bone_marrow/2026-10-26-source-cutaway-r05/annotated-context.png','reviews/bone_marrow/2026-10-26-source-cutaway-r05/close.webp'],
'brain':['reviews/brain/bodyparts3d-4.0-atlas-r2/screenshots/contact.png'],
'bronchial_tree':['reviews/bronchial_tree/2026-10-26-authored-central-fairing-r13/evidence/after-whole.png','reviews/bronchial_tree/2026-10-26-authored-central-fairing-r13/evidence/after-close.png'],
'dental-root-support':['models/dental-root-support/v3/media/detail-plate.png','models/dental-root-support/v3/media/pdl-only-plate.png','models/dental-root-support/v3/media/locator.png'],
'dental_specimens':['reviews/dental_specimens/uff_tomo1b/2026-10-26-r01/media/display-hard_tissue.png','reviews/dental_specimens/uff_tomo1b/2026-10-26-r01/media/display-void_side.png'],
'diaphragm':['reviews/diaphragm/2026-10-24-z-static-study/evidence/context_oblique.png','reviews/diaphragm/2026-10-24-z-static-study/evidence/front.png'],
'esophagus_wall':['reviews/esophagus_wall/2026-10-25-authored-teaching/teaching-sheet.png','reviews/esophagus_wall/2026-10-25-authored-teaching/oblique.png'],
'eye_anterior_segment':['reviews/eye_anterior_segment/2026-10-23-hra-v1.3-r01/display/cornea-iris-lens.webp','reviews/eye_anterior_segment/2026-10-23-hra-v1.3-r01/display/cornea-source-comparison.webp'],
'eye_exterior':['reviews/eye_exterior/2026-10-30-z-native-courses-r01/presentation/teaching.png','reviews/eye_exterior/2026-10-30-z-native-courses-r01/presentation/matched-source-R-posterior.png'],
'gallbladder':['reviews/readonly-audits/torso-readonly-audit-20261023/gallbladder-diagnostic-contact.png'],
'heart':['reviews/readonly-audits/heart-stomach-readonly-audit-20261023/heart/contact.png'],
'joints':['reviews/joints/2026-10-30-rotator-cuff-r01/v2/teaching.png'],
'kidney_left':['reviews/kidney_left/2026-10-23-hra-female-v1.3-r02/display/contact.webp','reviews/kidney_left/2026-10-23-hra-female-v1.3-r02/display/medulla_and_tip_surfaces_front.webp'],
'kidney_right':['reviews/kidney_right/2026-10-23-hra-female-v1.3-r02/display/contact.webp','reviews/kidney_right/2026-10-23-hra-female-v1.3-r02/display/medulla_and_tip_surfaces_front.webp'],
'liver':['reviews/liver/2026-10-23-hra-female-v1.10-r02/display/contact.webp','reviews/liver/2026-10-23-hra-female-v1.10-r02/display/candidate_material_oblique.webp'],
'lymph-collecting-routes':['models/lymph-collecting-routes/source-context-refined-r01/comparison-en.png'],
'lymph_node':['reviews/lymph_node/2026-10-23-hra-v1.2/display/exact-export-layer-contact.webp','reviews/lymph_node/2026-10-23-hra-v1.2/display/layer-key-contact.webp'],
'nose_sinuses':['reviews/nose_sinuses/2026-10-26-nih3d-airspace-r01/candidate-oblique.webp','reviews/nose_sinuses/2026-10-26-nih3d-airspace-r01/candidate-plusY.webp'],
'ovaries':['lessons/ovary-tubal-context/teaching.png','reviews/ovaries/2026-10-30-hra-ovary-tubal-r01/screenshots/export-overview.png'],
'parathyroids':['reviews/parathyroids/2026-10-25-localization-r01/teaching-posterior.png','reviews/parathyroids/2026-10-25-localization-r01/posterior-oblique-display.png'],
'penis':['reviews/penis/2026-10-26-native-components-r04/annotated-context.png','reviews/penis/2026-10-26-native-components-r04/oblique.webp'],
'peripheral_nerves':['reviews/peripheral_nerves/2026-10-30-median-wrist-r01/v2/teaching.png','reviews/peripheral_nerves/2026-10-30-ulnar-elbow-r01/evidence/teaching.png','reviews/peripheral_nerves/2026-10-30-sciatic-hip-r01/v2/teaching.png'],
'placenta':['reviews/placenta/2026-10-23-hra-v1.1-r02/display/contact.webp','reviews/placenta/2026-10-23-hra-v1.1-r02/display/fetal_chorionic_oblique_amnion_hidden.webp'],
'prostate':['reviews/prostate/2026-10-23-hra-v1.1/display/contact.webp','reviews/prostate/2026-10-23-hra-v1.1/display/context-oblique.webp'],
'pulmonary_vein':['lessons/pulmonary-vein-context/pulmonary-vein-context.png'],
'salivary_glands':['reviews/salivary_glands/2026-10-26-native-scoped-r02/annotated-context.webp','reviews/salivary_glands/2026-10-26-native-scoped-r02/context-side-source.webp'],
'stomach':['reviews/readonly-audits/heart-stomach-readonly-audit-20261023/stomach/contact.png'],
'swirendo_fdi31':['reviews/swirendo_fdi31/2026-10-28-balanced-focus/matched-overview-detail.jpg'],
'teeth_gums':['reviews/teeth_gums/2026-10-26-set-contact-checkpoint/media/upper-occlusal-teeth.png','reviews/teeth_gums/2026-10-26-set-contact-checkpoint/media/lower-occlusal-teeth.png'],
'testes':['reviews/testes/2026-10-30-native-epididymis/evidence/v2-pair.png','reviews/testes/2026-10-30-native-epididymis/evidence/v2-side-close.png'],
'thyroid_ct_s0189':['reviews/thyroid_ct_s0189/2026-10-29-illustrative-exterior-r01/comparison.png'],
'urethra_male':['reviews/urethra_male/2026-10-26-native-context-r01/annotated-context.webp','reviews/urethra_male/2026-10-26-native-context-r01/urethra-oblique.webp'],
'breathing':['body/breathing/expiration.webp','body/breathing/inspiration.webp'],
'cardiac-static':['reviews/readonly-audits/heart-stomach-readonly-audit-20261023/heart_detailed/contact.png','reviews/readonly-audits/heart-stomach-readonly-audit-20261023/heart_detailed/matched-neutral/contact.png'],
'cardiac-animated':['reviews/readonly-audits/heart-stomach-readonly-audit-20261023/heart_animated/contact.png'],
'cardiac-exterior':['reviews/heart_exterior/2026-11-01-fitted-applicability/images/updated-whole-front.png','reviews/heart_exterior/2026-11-01-fitted-applicability/images/updated-seam-front.png'],
'synthetic-imaging':['heart/synthetic-imaging/beating-heart/imaging/start_here_same_slice.png','heart/synthetic-imaging/beating-heart/imaging/ultrasound_labeled_fan.png'],
'svg-atlas':['body/2d-v4/whole-body-anatomy-v4-spatial/overview.svg'],
'stalk-assembly':['reviews/hypothalamus_pituitary/2026-10-29-teaching-stalk-r01/renders/updated-whole.png','reviews/hypothalamus_pituitary/2026-10-29-teaching-stalk-r01/renders/updated-junction.png'],
'marrow-assembly':['reviews/draft_bone/2026-10-23-marrow-comparison/evidence/two-panel-intended.png'],
'achilles-assembly':['reviews/draft_muscle/2026-10-23-achilles-context/evidence/neutral-oblique.png','reviews/draft_muscle/2026-10-23-achilles-context/evidence/heel-close-posterior.png'],
'cartilage-assembly':['reviews/skeletal_teaching/2026-10-23/second-costal-1.webp','reviews/skeletal_teaching/2026-10-23/L3-L4-disc-1.webp'],
'fdi36-experiment':['experiments/dental/fdi36-surface-cleanup/evidence/original-updated.png','experiments/dental/fdi36-surface-cleanup/evidence/occlusal-detail.png'],
'lesson-aortic-arch-locators':['reviews/aortic_tree_z/2026-10-29-arch-locators/overview-comparison.png'],
'lesson-arch-identification':['lessons/arch-identification/review/updated-upper-en.png','lessons/arch-identification/review/narrow-lower-zh.png'],
'lesson-brain-source-cut':['reviews/brain/2026-10-29-source-cut/screenshots/front-comparison.png'],
'lesson-dental-layer-controls':['lessons/dental-layer-controls/media/control-review-sheet.jpg','lessons/dental-layer-controls/media/control-separated.jpg'],
'lesson-kidney-location':['reviews/kidney_left/2026-10-30-location-prototype/updated-en.png'],
'lesson-one-breath':['lessons/one-breath/review/offline-storyboard.png','lessons/one-breath/review/exchange-static-states.png'],
'lesson-ovary-tubal-context':['lessons/ovary-tubal-context/teaching.png'],
'lesson-pulmonary-vein-context':['lessons/pulmonary-vein-context/pulmonary-vein-context.png'],
'lesson-fdi31-layer-reveal':['lessons/dental-animation/fdi31-layer-reveal/source-pose.jpg','lessons/dental-animation/fdi31-layer-reveal/editorial-reveal.jpg'],
'lesson-periodontal-cleaning':['lessons/dental-animation/periodontal-cleaning/poster.svg'],
'lesson-caries-restoration':['lessons/dental-animation/caries-restoration/poster.svg'],
'diagram-biliary_pathway':['diagrams/biliary_pathway/exports/r01/biliary-pathways-en.png'],
'diagram-oral_spaces':['diagrams/oral_spaces/exports/r01/oral-spaces-en.png'],
'diagram-testis_pathway':['diagrams/testis_pathway/exports/r02/testis-pathway-en.svg'],
'diagram-urinary_outflow':['diagrams/urinary_outflow/exports/r01/urinary-outflow-en.png'],
}
REUSE={'kidney-assembly':['kidney_left','kidney_right'],'liver-spleen-assembly':['liver','spleen'],'bladder-pancreas-assembly':['bladder','pancreas'],'swirendo-pilot':['swirendo_fdi31']}
FRESH_IDS={'lung_left','lung_right','vertebrae_L3','body-atlas','trachea','spinal_cord'}
CAPTIONS={
'cardiac-animated':'Historical sampled stills · not live playback',
'cardiac-exterior':'Exact fitted input · in-memory visibility study; not a fitted derivative export',
'eye_anterior_segment':'Historical cornea / iris / lens display · rejected ciliary/zonular attachment claims remain excluded',
'dental_specimens':'Research display · hard boundary / space proxy, not validated canal',
'swirendo-pilot':'FDI31 reference only · FDI46 pilot geometry/images not bundled here',
'lesson-one-breath':'Offline storyboard / SVG states · not browser or live WebGL evidence',
'lesson-arch-identification':'Offline SVG render · not browser capture',
'fdi36-experiment':'Historical V5/V6 comparison · shadow-attribution correction applies; noncanonical',
'svg-atlas':'2D schematic atlas · not 3D',
}

def paths_in(value):
    if isinstance(value,dict):
        if value.get('selectionRole')=='before' or value.get('reviewPhase')=='baseline':return []
        found=[]
        for k in ['retainedPath','path','file']:
            p=value.get(k)
            if isinstance(p,str) and p in FILES and Path(p).suffix.lower() in {'.png','.jpg','.jpeg','.webp','.svg'}:
                found.append(p)
        for k,v in value.items():
            if k not in ['originalFile','originalPngExternal','originalPNG','source','sources']:found.extend(paths_in(v))
        return found
    if isinstance(value,list):return [p for v in value for p in paths_in(v)]
    return []

def select(r):
    if r['id'] in PICKS:return [p for p in PICKS[r['id']] if p in FILES]
    p=r['evidence']['path']
    found=[]
    if p.endswith('.json'):found=paths_in(json.loads((ROOT/p).read_text()))
    return list(dict.fromkeys(found))[:2]

def encode(im,size,quality):
    im=im.copy();im.thumbnail(size,Image.Resampling.LANCZOS)
    if im.mode not in ['RGB','RGBA']:im=im.convert('RGBA')
    out=io.BytesIO();im.save(out,'WEBP',quality=quality,method=6)
    return 'data:image/webp;base64,'+base64.b64encode(out.getvalue()).decode()

def load(path):
    if path.suffix.lower()=='.svg':
        raster=FRESH/('svg-'+hashlib.sha256(path.read_bytes()).hexdigest()[:16]+'.png')
        if not raster.exists():
            subprocess.run([os.environ.get('MODEL_SURVEY_NODE','node'),str(OUT/'tools/rasterize_svg.mjs'),str(path),str(raster)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        return Image.open(raster)
    return Image.open(path)

def main():
    FRESH.mkdir(parents=True,exist_ok=True)
    rows=DATA['queries']['model_survey']['rows']+DATA['queries']['products']['rows']
    selections={r['id']:select(r) for r in rows}
    # Add regional joint candidates bound to each regional record, not the shared old baseline.
    for region in ['shoulder','elbow','knee']:
        p=next(p for p in FILES if p.startswith('reviews/joints/') and region+'-bounded-migration/bounded-record.json' in p)
        candidates=paths_in(json.loads((ROOT/p).read_text()))
        if candidates:selections['joints'].append(candidates[0])
    for id in FRESH_IDS:
        selections[id]=[str(p.relative_to(ROOT)) for p in sorted(FRESH.glob(id+'-*.png'))]
    bindings=json.loads((FRESH/'render-bindings.json').read_text())
    by_image={x['image']:x for x in bindings}
    for id,related in REUSE.items():
        selections[id]=[selections[x][0] for x in related if selections[x]]
    gallery={};tiles=[]
    for r in rows:
        ids=[]
        for i,p in enumerate(selections[r['id']]):
            path=ROOT/p
            assert path.is_file(),p
            sha=hashlib.sha256(path.read_bytes()).hexdigest()
            key=sha[:24]
            fresh=p.startswith(str(FRESH.relative_to(ROOT))+'/') and not path.name.startswith('svg-')
            if fresh:
                binding=by_image[path.name]
                assert binding['imageSha256']==sha, 'Preview image identity changed: '+p
                current={m['path']:m['sha256'] for m in r['media']}
                assert all(current.get(m['path'])==m['sha256'] for m in binding['inputs']), 'Preview source identity changed: '+p
            if key not in gallery:
                with load(path) as im:
                    gallery[key]={'image':encode(im,(1800,1500),90),'thumb':encode(im,(240,180),85),'width':im.width,'height':im.height,'source':p if not fresh else 'Local exact-GLB preview','sourceSha256':sha,'kind':'Fresh neutral GLB preview · unreviewed' if fresh else ('Schematic / teaching illustration' if '/diagrams/' in '/'+p or path.suffix=='.svg' else 'Retained review image'),'sourceUrl':BASE+p if p in FILES else r['evidence']['url']}
                    if fresh:gallery[key]['inputBindings']=binding['inputs']
            ids.append(key)
        r['previewIds']=list(dict.fromkeys(ids))
        r['previewCaption']=('Fresh neutral inventory views from existing GLBs · not a replay of prior review pixels' if r['id'] in FRESH_IDS else CAPTIONS.get(r['id'], 'Related retained asset views · recipe only' if r['id'] in REUSE else 'Retained source/review views · recorded scope unchanged'))
        r['previewMissing']='Recipe only · no retained model or review pixels' if r['id']=='fetus' else 'No retained preview available'
        if ids:
            im=load(ROOT/selections[r['id']][0]);tile=Image.new('RGB',(300,220),'#f1f2f3');thumb=ImageOps.contain(im.convert('RGB'),(290,180));tile.paste(thumb,((300-thumb.width)//2,0));ImageDraw.Draw(tile).text((6,185),r['id'],fill='#111111');tiles.append(tile)
    DATA['previewGallery']=gallery
    DATA['survey']['previewCoverage']={'families':sum(bool(r['previewIds']) for r in DATA['queries']['model_survey']['rows']),'familyTotal':62,'products':sum(bool(r['previewIds']) for r in DATA['queries']['products']['rows']),'productTotal':31,'images':len(gallery)}
    DATA['buildStatus']='updating'
    SNAPSHOT.write_text(json.dumps(DATA,ensure_ascii=False,indent=2)+'\n')
    for page in range((len(tiles)+19)//20):
        board=Image.new('RGB',(1500,880),'white')
        for j,tile in enumerate(tiles[page*20:page*20+20]):board.paste(tile,((j%5)*300,(j//5)*220))
        qa=OUT/'.local/qa';qa.mkdir(parents=True,exist_ok=True)
        board.save(qa/f'preview-selection-{page+1}.jpg',quality=90)
    print(json.dumps({'coverage':DATA['survey']['previewCoverage'],'missing':[r['id'] for r in rows if not r['previewIds']],'bytes':SNAPSHOT.stat().st_size}))

if __name__=='__main__':main()
