"""Rebuild the bounded survey snapshot from this committed checkout."""
import collections
import os
import hashlib
import json
import struct
import subprocess
from pathlib import Path

OUT = Path(__file__).resolve().parents[1]
ROOT = Path(os.environ.get("MED_ASSETS_REPO", OUT.parents[1])).expanduser().resolve()
REV = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
FILES = subprocess.check_output(['git', 'ls-files'], cwd=ROOT, text=True).splitlines()
BASE = f'https://github.com/qianyizhang/med-assets/blob/{REV}/'

def read(p):
    return json.loads((ROOT / p).read_text())

def url(p):
    assert p in FILES, p
    return BASE + p

# Status describes only the explicitly named useful scope, never whole-organ approval.
# id | label | system | purpose | scope status | useful scope | important limit
ROWS = '''adipose-context|Adipose pads|Body & support|Localization|Scoped static|Four authored pads with illustrative body locator|Not fitted skin, measured fat volume or body-habitus coverage
adrenals|Adrenal pair|Endocrine|Localization|Scoped static|BP3D exterior silhouettes; kidney context in review|No internal zones; source replay not portable
aorta|Aorta · s1233|Cardiovascular|Exterior reference|Needs review|Source-derived arterial exterior; metadata alternative|Coverage ambiguous; source/context review needed
aortic_tree_z|Aortic tree · Z|Cardiovascular|Routes & relationships|Scoped static|15 source structures in 9 meshes; arch locators|Open rims and unfused joins; no continuous lumen
bladder|Bladder|Urinary|Localization|Scoped static|Female HRA six-patch exterior with pelvic context|Open patches; no validated wall layers or filling state
blood_cell_study|Blood-cell forms|Lymphatic & tissue|Layers & cutaways|Scoped static|Authored RBC, neutrophil and platelet form study|Arbitrary scale; not microscopy or complete blood-cell repertoire
bone_marrow|Bone-marrow cutaway|Musculoskeletal|Layers & cutaways|Limited supplement|Source exterior with authored marrow/cortical teaching interior|No measured trabeculae or complete marrow anatomy
brain|Brain|Nervous & senses|Exterior reference|Scoped static|49 BP3D external atlas parts; source-cut annotation|Faceting and truncated brainstem; no internal tissue atlas
breasts_hra|Breast pair|Reproductive|Layers & cutaways|Scoped static|HRA sculpted layers and simplified ducts|Open/nonmanifold parts; no complete microanatomy
bronchial_tree|Bronchial tree|Respiratory|Routes & relationships|Needs revision|r07 → r09 → r13 improve local authored junctions|Schematic routes, capped terminals and residual collar/pocket
dental-root-support|Molar root & support|Oral & dental|Layers & cutaways|Scoped static|Teeth 35–37, bone crop and separate synthetic PDL view|No fine crown relief, internal tissues or trabecular microstructure
dental_specimens|UFF Tomo1B specimen|Oral & dental|Specimen research|Draft / review|Scan-derived hard boundary and internal-space proxy|Unknown FDI; proxy connects to exterior and is algorithmically capped
diaphragm|Diaphragm|Respiratory|Localization|Scoped static|Native static gross shape with auxiliary skeletal context|No differentiated tendon/fibres; earlier breathing schematic needs revision
ears_z|Auricles / pinnae|Nervous & senses|Exterior reference|Scoped static|Z-native external ear envelopes|No canal, tympanum, middle or inner ear
esophagus_wall|Esophageal wall|Digestive|Layers & cutaways|Limited supplement|Five meshes show four tunics in a short authored wedge|Layer order only; no full-organ repair, histology or validated thickness
eye_anterior_segment|Eye · anterior segment|Nervous & senses|Layers & cutaways|Limited supplement|Three-structure cornea–pupil-opening–lens teaching order|Seven-node export includes rejected ciliary/zonular teaching geometry
eye_exterior|Eye · exterior courses|Nervous & senses|Localization|Limited supplement|Two scenes, globe envelopes and extraocular courses|Optic ends are source cuts; no chiasm, action or attachment validation
fetus|Fetal inset study|Reproductive|Exterior reference|Noncanonical|Bounded authored head–face junction recipe and historical review|Candidate media not included; non-age-calibrated; further public delivery not planned
gallbladder|Gallbladder|Digestive|Exterior reference|Needs review|s1233 exterior with illustrative wall/duct baseline|Ambiguous source/duct relationship; no accepted detailed 3D pathway
heart|Heart · body shell|Cardiovascular|Exterior reference|Needs revision|Coarse source-case exterior and metadata alternative|Separate from detailed authored cardiac atlas; translation is not heartbeat
hypothalamus|Hypothalamus|Endocrine|Localization|Scoped static|Two low-detail BP3D exterior/localization surfaces|No nuclei; original pituitary stalk envelopes overlap
joints|Regional joints|Musculoskeletal|Localization|Scoped static|Right shoulder, elbow, knee; separate rotator-cuff locator|Selected tissues only; no complete cartilage, attachments or mechanics
kidney_left|Left kidney|Urinary|Layers & cutaways|Scoped static|Female HRA exterior and isolated pyramids/tip surfaces|No collecting system or vessels; columns/medulla overlap mode rejected
kidney_right|Right kidney|Urinary|Layers & cutaways|Scoped static|Female HRA exterior and isolated pyramids/tip surfaces|No collecting system or vessels; not registered to s1233 body
large-intestine|Large bowel|Digestive|Exterior reference|Scoped static|Ten BP3D exterior components; taenia teaching ribbons|Disconnected exterior; no validated continuous lumen
liver|Liver|Digestive|Exterior reference|Scoped static|HRA capsule, bare area and six named source ligaments|Open region patches; no internal vascular/biliary tree
lung_left|Left lung · s1233|Respiratory|Motion & imaging|Needs review|Retained source lobes with illustrative breathing morph|Static detailed fidelity needs review; motion is not physiological validation
lung_pair|Lung pair · HRA|Respiratory|Exterior reference|Scoped static|Combined lobes and supplied intrapulmonary branches|56 open-boundary meshes; no main bronchi/trachea; five-color draft pending review
lung_right|Right lung · s1233|Respiratory|Motion & imaging|Needs review|Retained source lobes with illustrative breathing morph|Static detailed fidelity needs review; no accepted HRA motion transfer
lymph-collecting-routes|Lymph collecting routes|Lymphatic & tissue|Routes & relationships|Limited supplement|Seven authored source routes with regional contour/highlight lesson|Contour is illustrative; no measured body registration or systemic flow proof
lymph_node|Single lymph node|Lymphatic & tissue|Layers & cutaways|Scoped static|Seven HRA source meshes; reviewed layer contacts|Source vascular network identity conflicts; open/non-two-incidence edges
muscle|Muscle atlas|Musculoskeletal|Exterior reference|Scoped static|462 muscle/part meshes plus 47 support meshes|41 source topology warnings; no attachment, fibre or mechanics validation
nose_sinuses|Nasal / sinus airspace|Respiratory|Specimen research|Limited supplement|NIH3D CT-derived airspace specimen display|Cyst indentation and four intersection pairs; not mucosa or healthy template
ovaries|Ovary + tubal ends|Reproductive|Localization|Limited supplement|Ten native HRA surfaces with fimbrial/tubal context|No follicles, uterus, ligaments or continuous lumen; gaps/cuts preserved
pancreas|Pancreas|Digestive|Localization|Scoped static|HRA five-region exterior with same-atlas context|Degenerate/sliver patches and normal warnings; no duct patency
parathyroids|Parathyroid localization|Endocrine|Localization|Limited supplement|Four source-named glands, isolated and thyroid-context roles|Mirrored simplified shapes; thyroid projection uninterpreted
parotid_glands|Parotid pair|Oral & dental|Exterior reference|Scoped static|Z-native outer gland envelopes|No ducts/deep lobes; overlaps broader salivary localization study
penis|Penile components|Reproductive|Routes & relationships|Limited supplement|Native gross internal-component relationships|Glans edge defects; skin, prepuce, vessels and continuous urethral lumen absent
peripheral_nerves|Regional peripheral nerves|Nervous & senses|Localization|Limited supplement|Right ulnar/elbow, median/wrist-hand and sciatic/hip studies|Three local courses; no complete plexuses, distal innervation or nerve mechanics
pharynx_larynx|Pharynx / larynx|Respiratory|Localization|Scoped static|33 BP3D dissected muscle/cartilage/ligament components|Disputed laterality labels; no mucosal airway or swallowing/voice mechanics
pituitary|Pituitary|Endocrine|Localization|Scoped static|BP3D low-detail exterior envelope|No lobes/fine neuroanatomy; stalk overlap in original source pair
placenta|Full-term placenta|Reproductive|Layers & cutaways|Scoped static|Eight named HRA layers; material-only refinement|505 non-two-incidence edges; no perfusion, exchange or numerical gestational age
prostate|Prostate|Reproductive|Layers & cutaways|Scoped static|HRA zones and accessory source structures|Open annotation patches; no complete tract or continuous lumen
pulmonary_vein|Pulmonary-vein component|Cardiovascular|Localization|Limited supplement|Retained largest component with same-case heart/lung teaching context|Left-sided retained subset only; no restored branches or lumen continuity
salivary_glands|Major salivary glands|Oral & dental|Routes & relationships|Limited supplement|Three gland pairs and gross parotid duct course|Both submandibular ducts excluded; left source crossing confirmed
skeleton|Skeletal atlas|Musculoskeletal|Exterior reference|Scoped static|271 representation meshes: bone-category, cartilage/disc and dental context|206 bone-category meshes are not 206 validated bones; no rig/mechanics
skin|Body envelope|Body & support|Localization|Scoped static|Adult male BP3D external envelope for navigation|No skin layers, thickness, demographic coverage or rigging
small-intestine|Small bowel|Digestive|Motion & imaging|Scoped static|55 BP3D exterior components; authored proximal bridge|Respiratory morph is not peristalsis; no continuous validated lumen
spinal_cord|Spinal cord & roots|Nervous & senses|Routes & relationships|Limited supplement|Authored conus/filum and r04 dorsal-ganglion/ventral-root relationships|17 bilateral illustrative levels; no complete 31-pair map, rootlets or meninges
spleen|Spleen|Lymphatic & tissue|Exterior reference|Scoped static|HRA five exterior regions; protected hilum and bounded normal changes|Open patches; not registered to s1233 body or clinical reference
stomach|Stomach · s1233|Digestive|Layers & cutaways|Needs revision|Source exterior plus independent authored mucosal teaching section|Retained ribbing/corrugation; separate polished external baseline not bundled here
swirendo_fdi31|FDI31 · prepared specimen|Oral & dental|Specimen research|Scoped static|Balanced educational LOD; four source-labelled tissues|Prepared T2 specimen, islands/open interfaces/cuts; no certified LOD error bound
teeth_gums|Adult teeth & gingiva|Oral & dental|Exterior reference|Scoped static|28 BP3D tooth exteriors plus two shared gingiva surfaces|Not 32-tooth/primary set; exposed cut roots; no accepted whole-set anatomy
testes|Testis–epididymis|Reproductive|Localization|Limited supplement|Four native Z testis/epididymis gross exteriors|No ductus deferens, scrotum, internal anatomy or tract continuity
thymus|Thymus|Lymphatic & tissue|Localization|Scoped static|Two BP3D lobe exteriors with retrosternal review context|Sternum occlusion; no histology or age-dependent morphology
thyroid_ct_s0189|Thyroid · s0189|Endocrine|Specimen research|Limited supplement|Sample-specific clinical-source exterior; illustrative ridge smoothing|No healthy/normative claim; exact same-case trachea absent locally
tongue_authored_study|Tongue · hybrid|Oral & dental|Exterior reference|Scoped static|HRA-derived dorsum/papillae plus authored body/ventral joins|Four provenance partitions are not removable layers; no oral floor or internal muscles
trachea|Trachea / Y-airway|Respiratory|Layers & cutaways|Limited supplement|r06 authored open shell and cutaway; r05 illustrative C-bands|Wall/cuts are inferred, not specimen histology or normal caliber; whole asset unpromoted
urethra_male|Male urethral context|Urinary|Routes & relationships|Limited supplement|Six native objects locate gross route in bladder/prostate/erectile context|Outlet, segment detail, connections and continuous lumen unvalidated
uterus|Uterus exterior|Reproductive|Exterior reference|Scoped static|HRA exterior derivative omits overlapping source wall solids|No created cavity, complete tubes/ovaries or full-system acceptance
vagina_hra|Vaginal / cervical context|Reproductive|Localization|Scoped static|HRA exterior with selected pelvic source context|No vulva, mucosa, validated lumen or complete pelvis
vertebrae_L3|L3 vertebra|Musculoskeletal|Exterior reference|Scoped static|Gross s1233 exterior; seven-field metadata-only alternative|Fine anatomy unreviewed; not a whole-spine or biomechanics model'''

PRIMARY = {
 'aorta':'reviews/accounting/2026-10-23/baseline-decisions.json',
 'gallbladder':'reviews/accounting/2026-10-23/baseline-decisions.json',
 'adipose-context':'models/adipose-context/r01/independent-review.json',
 'aortic_tree_z':'reviews/z-small-studies/2026-10-24-bounded-migration/aortic_tree_z/record.json',
 'bone_marrow':'reviews/bone_marrow/2026-10-26-source-cutaway-r05/review-decision.json',
 'brain':'reviews/brain/2026-10-24-bodyparts3d-4.0-atlas-r2-bounded-migration/bounded-record.json',
 'breasts_hra':'reviews/breasts_hra/2026-10-24-bounded-migration/bounded-record.json',
 'bronchial_tree':'models/bronchial_tree/exports/authored-central-fairing-r13/README.md',
 'dental-root-support':'models/dental-root-support/v3/review-record.json',
 'dental_specimens':'reviews/dental_specimens/uff_tomo1b/2026-10-26-r01/independent-review-summary.md',
 'ears_z':'reviews/z-small-studies/2026-10-24-bounded-migration/ears_z/record.json',
 'eye_anterior_segment':'reviews/eye_anterior_segment/2026-10-28-teaching-scope-r02/decision.json',
 'eye_exterior':'reviews/eye_exterior/2026-10-30-z-native-courses-r01/README.md',
 'fetus':'models/fetus/exports/head-face-junction-r01/README.md',
 'heart':'reviews/accounting/2026-10-23/baseline-decisions.json',
 'joints':'reviews/joints/2026-10-24-bounded-migration/README.md',
 'large-intestine':'reviews/intestines/2026-10-24-bounded-migration/large-intestine/record.json',
 'lymph-collecting-routes':'models/lymph-collecting-routes/source-context-refined-r01/README.md',
 'muscle':'reviews/muscle/2026-10-24-bounded-migration/bounded-record.json',
 'nose_sinuses':'reviews/nose_sinuses/2026-10-26-nih3d-airspace-r01/review-decision.json',
 'ovaries':'reviews/ovaries/2026-10-30-hra-ovary-tubal-r01/README.md',
 'parathyroids':'reviews/parathyroids/2026-10-25-localization-r01/README.md',
 'parotid_glands':'reviews/z-small-studies/2026-10-24-bounded-migration/parotid_glands/record.json',
 'penis':'reviews/penis/2026-10-26-native-components-r04/decision.json',
 'peripheral_nerves':'reviews/peripheral_nerves/2026-10-30-median-wrist-r01/README.md',
 'pharynx_larynx':'reviews/pharynx_larynx/2026-10-24-r03-bounded-migration/bounded-record.json',
 'pulmonary_vein':'reviews/pulmonary_vein/2026-10-30-context/checks.json',
 'salivary_glands':'reviews/salivary_glands/2026-10-26-native-scoped-r02/decision.json',
 'skeleton':'reviews/skeleton/2026-10-24-source-candidate-03-bounded-migration/bounded-record.json',
 'skin':'reviews/skin/2026-10-24-bp3d-envelope-r01-bounded-migration/bounded-record.json',
 'small-intestine':'reviews/intestines/2026-10-24-bounded-migration/small-intestine/record.json',
 'spinal_cord':'reviews/spinal_cord/2026-10-29-authored-roots-r04/README.md',
 'stomach':'reviews/accounting/2026-10-23/baseline-decisions.json',
 'swirendo_fdi31':'reviews/swirendo_fdi31/2026-10-28-balanced-focus/README.md',
 'teeth_gums':'reviews/teeth_gums/2026-10-24-r02-bounded-migration/bounded-record.json',
 'testes':'reviews/testes/2026-10-30-native-epididymis/independent-review.json',
 'thyroid_ct_s0189':'reviews/thyroid_ct_s0189/2026-10-29-illustrative-exterior-r01/review.json',
 'trachea':'reviews/trachea/2026-10-29-open-airway-r06/checks.json',
 'urethra_male':'reviews/urethra_male/2026-10-26-native-context-r01/decision.json',
 'vagina_hra':'reviews/vagina_hra/2026-10-24-bounded-migration/bounded-record.json',
}

def gates(d):
    if not isinstance(d,dict):return {}
    g=d.get('gates',d.get('recordedPublicGates',d.get('inheritedGates',{})))
    if not isinstance(g,dict):return {}
    return {k:(v.get('status',str(v)) if isinstance(v,dict) else str(v)) for k,v in g.items()}

all_records=[]
for p in FILES:
    if p.endswith('.json') and p.startswith(('reviews/','models/')):
        try:d=read(p)
        except (ValueError,OSError):continue
        if gates(d): all_records.append((p,d))

media=[]
for p in FILES:
    if not p.endswith('.glb'):continue
    path=ROOT/p
    with path.open('rb') as f:head=f.read(256)
    item={'path':p,'url':url(p),'role':'Asset export' if p.startswith(('models/','assemblies/','body/','heart/')) else 'Source / review input'}
    if head.startswith(b'version https://git-lfs.github.com/spec/v1'):
        text=head.decode();item.update(sha256=text.split('oid sha256:')[1].split()[0],bytes=int(text.split('size ')[1].split()[0]),availability='LFS pointer only')
    else:
        data=path.read_bytes();item.update(sha256=hashlib.sha256(data).hexdigest(),bytes=len(data),availability='Local bytes')
        if head[:4]==b'glTF':
            n=struct.unpack_from('<I',data,12)[0]; gltf=json.loads(data[20:20+n]);item.update(meshes=len(gltf.get('meshes',[])),animations=len(gltf.get('animations',[])))
    matches=[]
    for rp,d in all_records:
        if item['sha256'] in json.dumps(d):matches.append({'path':rp,'url':url(rp),'gates':gates(d)})
    item['recordReferences']=[{'path':m['path'],'url':m['url']} for m in matches]
    media.append(item)

rows=[]
for line in ROWS.splitlines():
    id,label,system,purpose,state,use,limit=line.split('|')
    docs=[p for p in FILES if p.startswith('models/'+id+'/') and p.endswith('README.md') and '/recipes/' not in p and '/provenance/' not in p]
    rp=PRIMARY.get(id)
    if rp and rp not in FILES:
        # Recover exact owner names without guessing an unavailable source link.
        choices=[p for p in FILES if p.startswith('reviews/'+id+'/') and p.endswith(('record.json','bounded-record.json')) and 'metadata-cleanup' not in p]
        rp=choices[-1] if choices else (docs[0] if docs else None)
    if not rp:
        choices=[p for p in FILES if p.startswith('reviews/'+id+'/') and p.endswith(('record.json','bounded-record.json')) and 'metadata-cleanup' not in p]
        rp=choices[-1] if choices else next((p for p in FILES if p.startswith('reviews/'+id+'/') and p.endswith('record.json')),None)
    assert rp,id
    d=read(rp) if rp.endswith('.json') else {}
    gs=gates(d)
    if rp=='reviews/accounting/2026-10-23/baseline-decisions.json':
        b=next((b for b in d['records'] if b['assetId']==id),None)
        if b:gs={'visual':b['visual']['status']+' — '+b['visual'].get('scope',''),'technical':'Metadata equivalence is not a new geometry-quality certificate','anatomy':'No anatomy/clinical promotion','runtime':'No full intended-consumer promotion'}
    if not gs:
        for k in ['technical','visual','anatomy','runtime']:
            v=d.get(k) if isinstance(d,dict) else None
            if v:gs[k]=v.get('status',str(v)) if isinstance(v,dict) else str(v)
    if not gs:
        gs={'technical':'See bounded checks in owner','visual':state+' — named scope only','anatomy':'No specialist/clinical approval established','runtime':'No full intended-consumer pass established'}
    rows.append({'id':id,'label':label,'system':system,'purpose':purpose,'state':state,'use':use,'limit':limit,'evidence':{'path':rp,'url':url(rp)},'gates':gs,'docs':[{'path':p,'url':url(p)} for p in docs], 'media':[m for m in media if m['path'].startswith('models/'+id+'/')]})

assert {r['id'] for r in rows}=={p.split('/')[1] for p in FILES if p.startswith('models/')}

# Additional products are shown separately, so shared views never inflate family counts.
PRODUCTS = [
('body-atlas','3D Anatomy Workshop','Body & support','Exterior reference','Collection / limited','18 grouped assets; 17 s1233 exterior surfaces plus authored teaching details','Thoracoabdominal focus; authored additions and detailed heart are not scan-registered','body/anatomy-workshop-r1/README.md','body/anatomy-workshop-r1/'),
('breathing','Breathing collection','Respiratory','Motion & imaging','Illustrative motion','11 animated GLBs: lung morphs, diaphragm and organ translations','CPU/Blender evidence; not measured physiology or complete browser acceptance','body/breathing/README.md','body/breathing/'),
('cardiac-static','Cardiac Atlas · native & static','Cardiovascular','Layers & cutaways','Needs revision','Four chambers, valves/chordae, representative vessels/coronaries; editable native rig','Analytic junctions and exposed cords/gaps fail detailed exterior target; ED exports static','heart/Cardiac_Atlas/docs/README.md','heart/Cardiac_Atlas/'),
('cardiac-animated','Cardiac Atlas · animated','Cardiovascular','Motion & imaging','Illustrative motion','Three full/cutaway/tissue GLBs; 0.8-second authored morph cycle','Schematic timing and anatomy; no pressure/flow/biomechanics validation','heart/Cardiac_Atlas_Animated/README.md','heart/Cardiac_Atlas_Animated/'),
('cardiac-exterior','Cardiac opaque exteriors','Cardiovascular','Exterior reference','Limited supplement','Two opaque derivatives; later exact fitted correspondence check passed with limits','Presentation fix only; no fitted derivative exported, wall healing or live WebGL pass','reviews/heart_exterior/2026-11-01-fitted-applicability/README.md','heart/exterior-presentation-r01/'),
('synthetic-imaging','Synthetic cardiac imaging','Cardiovascular','Motion & imaging','Synthetic reference','Matched ED label, arbitrary-contrast CT/MR and ultrasound-style fan volumes','Not patient imaging, scanner physics or time-resolved cine','heart/synthetic-imaging/beating-heart/imaging/README.md','heart/synthetic-imaging/'),
('svg-atlas','2D spatial anatomy atlas','Body & support','2D & lessons','Schematic / historical review','54 primary anatomy IDs, 15 variants, 54 overlays and 21 regional views','Editable SVGs, not 3D; original review does not approve every later edit','body/2d-v4/whole-body-anatomy-v4-spatial/README.md','body/2d-v4/'),
('stalk-assembly','Hypothalamus–pituitary join','Endocrine','Routes & relationships','Limited supplement','Separate authored continuous exterior resolves intersecting stalk envelopes','No nuclei, lobes, axons or measured junction','assemblies/hypothalamus-pituitary/teaching-stalk-r01/README.md','assemblies/hypothalamus-pituitary/'),
('kidney-assembly','Kidney pair replay','Urinary','Layers & cutaways','Shared recipe','Replays the two retained HRA studies','Not another accepted model or new collecting system','models/kidney_left/README.md','assemblies/kidney-pair/'),
('liver-spleen-assembly','Liver / spleen replay','Digestive','Exterior reference','Shared recipe','Shared reconstruction for retained native HRA exteriors','External 374.5 MB female atlas required; not body registration','models/liver/README.md','assemblies/liver-spleen/'),
('bladder-pancreas-assembly','Bladder / pancreas replay','Digestive','Localization','Shared recipe','Exact accepted bytes from shared HRA input and pinned scripts','Recipe composition, not an anatomical bladder–pancreas assembly','models/bladder/README.md','assemblies/bladder-pancreas/'),
('marrow-assembly','Bone / trabecula comparison','Musculoskeletal','Specimen research','Limited supplement','Femur exterior and independent segmented-bone reference','Unregistered, different scales; header/prose spacing discrepancy','assemblies/marrow-comparison/2026-10-23/README.md','assemblies/marrow-comparison/'),
('achilles-assembly','Calf–Achilles–heel','Musculoskeletal','Localization','Limited supplement','Eight source-native right-sided meshes','Not validated enthesis or complete tendon/ligament coverage','assemblies/musculoskeletal-teaching/2026-10-23/README.md','assemblies/musculoskeletal-teaching/'),
('cartilage-assembly','Costal cartilage / L3–L4 disc','Musculoskeletal','Localization','Limited supplement','Two static source-context teaching views','No annulus/nucleus, full cartilage or biomechanics','assemblies/skeletal-teaching/README.md','assemblies/skeletal-teaching/'),
('swirendo-pilot','FDI31 / FDI46 pilot records','Oral & dental','Specimen research','Record / external geometry','Two prepared T2 specimens; four source-labelled layers each','Pilot summaries only; full binaries not published by those records','sources/datasets/swirendo-pilot/validation-summary.json','sources/datasets/swirendo-pilot/'),
('fdi36-experiment','FDI36 surface experiment','Oral & dental','Specimen research','Noncanonical','Authored occlusal cleanup recipe and matched evidence','Intact/restoration baseline unaccepted; media generated outside tracked tree','experiments/dental/fdi36-surface-cleanup/README.md','experiments/dental/fdi36-surface-cleanup/'),
]
LESSONS={
'aortic-arch-locators':('Aortic arch locators','Cardiovascular','Reviewed static sheet','Source-group branch names; no fourth direct arch branch'),
'arch-identification':('Dental arch identification','Oral & dental','Reviewed offline / browser unverified','28 FDI crown locators; no bite/contact validation'),
'brain-source-cut':('Brain source-cut sheet','Nervous & senses','Reviewed static sheet','Marks truncated brainstem; no missing tissue added'),
'dental-layer-controls':('Dental layer controls','Oral & dental','Bounded prototype','Prepared FDI31 reveal/isolate/reset; no complete anatomy pass'),
'kidney-location':('Kidney location prototype','Urinary','Independent review pending','2D outline around retained tiles; no measured learning benefit'),
'one-breath':('One breath','Respiratory','Bounded prototype / browser unverified','Mechanics → airway → separate alveolar/capillary schematic'),
'ovary-tubal-context':('Ovary–fimbrial teaching sheet','Reproductive','Reviewed static sheet','Source-labelled orientation; retained cuts/gaps'),
'pulmonary-vein-context':('Pulmonary-vein context sheet','Cardiovascular','Reviewed static sheet','Largest retained component in same-case heart/lung context'),
}
for folder,(label,system,state,limit) in LESSONS.items():
    PRODUCTS.append(('lesson-'+folder,label,system,'2D & lessons',state,'EN/中文 bounded teaching product',limit,'lessons/'+folder+'/README.md','lessons/'+folder+'/'))
for folder,label,limit in [
('fdi31-layer-reveal','Prepared FDI31 layer-reveal preview','Nine-second working preview; not intact healthy anatomy'),
('periodontal-cleaning','Schematic cleaning preview','Accepted schematic demo; realistic gingival-margin/subgingival baseline unsuitable'),
('caries-restoration','Caries / restoration script','Script and vector comparison preview; realistic modular tooth sequence deferred')]:
    p='lessons/dental-animation/'+folder+'/README.md'
    PRODUCTS.append(('lesson-'+folder,label,'Oral & dental','2D & lessons','Schematic / preview','Bounded dental animation or script',limit,p,'lessons/dental-animation/'+folder+'/'))
for folder,label,system in [('biliary_pathway','Biliary / pancreatic pathways','Digestive'),('oral_spaces','Oral spaces','Oral & dental'),('testis_pathway','Testis transport pathway','Reproductive'),('urinary_outflow','Urinary outflow comparison','Urinary')]:
    p='diagrams/'+folder+'/exports/'+('r02' if folder=='testis_pathway' else 'r01')+'/README.md'
    PRODUCTS.append(('diagram-'+folder,label,system,'2D & lessons','Reviewed schematic','EN/中文 static relationship diagram','Not a 3D repair or anatomy/clinical approval',p,'diagrams/'+folder+'/'))

products=[]
for id,label,system,purpose,state,use,limit,p,prefix in PRODUCTS:
    products.append({'id':id,'label':label,'system':system,'purpose':purpose,'state':state,'use':use,'limit':limit,'evidence':{'path':p,'url':url(p)},'gates':{},'docs':[],'media':[m for m in media if m['path'].startswith(prefix)],'product':True})

OVERLAPS=[
('Baseline ↔ source studies','Keep distinct representations','17 s1233 body surfaces and authored baselines coexist with HRA/BP3D/Z studies; native frames and review scopes differ. No default replacement.',['body-atlas','brain','liver','kidney_left','lung_pair','bladder']),
('Atlas ↔ regional extraction','Reuse source context','Skeleton includes dental/cartilage context; muscle atlas includes eye/regional muscles. Regional joints, nerves and Achilles studies teach narrower relationships.',['skeleton','teeth_gums','muscle','eye_exterior','joints','peripheral_nerves','achilles-assembly','cartilage-assembly']),
('Heart full / cutaway / motion','Views of one authored model','Static, animated, tissue and opaque-exterior derivatives serve different views; synthetic imaging shares idealized ED geometry, not time-resolved motion.',['cardiac-static','cardiac-animated','cardiac-exterior','synthetic-imaging','heart']),
('Respiratory alternatives','Do not fuse by appearance','s1233 lungs move; HRA lungs expose lobes/branches; authored bronchial routes and tracheal shells have separate limitations. One-breath composes selected inputs.',['lung_left','lung_right','lung_pair','bronchial_tree','trachea','breathing','lesson-one-breath']),
('Primary / context exports','One study, multiple roles','Diaphragm, salivary glands, parathyroids and dental PDL exports include primary/context views; file count is not additional organ coverage.',['diaphragm','salivary_glands','parathyroids','dental-root-support']),
('Dental exteriors ↔ specimens','Complementary, unregistered','28 atlas exteriors, prepared FDI31/46 specimens, UFF proxy and synthetic root-support segment do not form a coherent layered mouth.',['teeth_gums','swirendo_fdi31','dental_specimens','dental-root-support']),
('Parotid-only ↔ salivary study','Narrow / broad selections','Parotid pair is a simple envelope reference; broader native study adds other gland pairs and selected ducts, with explicit duct exclusions.',['parotid_glands','salivary_glands']),
('Gland exports ↔ stalk assembly','Originals plus authored join','Hypothalamus/pituitary exports preserve intersecting source envelopes; separate teaching assembly creates a continuous inferred exterior.',['hypothalamus','pituitary','stalk-assembly']),
('Metadata alternatives','Same geometry; no quality gain','Sixteen named metadata-only alternatives correct scene extras. Later original-baseline decisions can supersede their earlier visual labels.',['aorta','brain','heart','liver','stomach','vertebrae_L3']),
]
GAPS=[
('Qualification','P1','Clinical/anatomical review','Missing validation','Add scoped specialist review for intended teaching claims; static appearance and source labels alone do not establish anatomy.','docs/WORKFLOW.md'),
('Qualification','P1','Live 3D acceptance','Missing validation','Verify actual target viewer loading, scene selection, motion, isolation and failure recovery. Prior CPU/offline evidence has narrower coverage.','lessons/one-breath/review/README.md'),
('Qualification','P1','Cross-source registration','Proposed integration','Choose one native frame per lesson; quantify explicit transforms before mixed CT/HRA/BP3D/Z assemblies. Preserve source alternatives.','body/anatomy-workshop-r1/README.md'),
('Dental suite','P1','Intact modular adult molar','Deferred plan','Qualify an intact detailed baseline before caries → preparation → restoration. Reuse existing support/tool assets where fit.','docs/dental-atlas/PLAN.md'),
('Dental suite','P1','Source-qualified cleaning segment','Deferred plan','Tooth/gingiva context plus independent deposits and generic tool; existing schematic remains useful.','docs/dental-atlas/PLAN.md'),
('Dental suite','P2','Complete permanent + primary sets','Missing geometry / review','Four adult target slots 18/28/38/48 and all 20 primary exterior slots unavailable; coherent layered sets and condition pairs unaccepted.','docs/dental-atlas/set-review.md'),
('Airways & ducts','P1','Coherent conducting airway','Proposed adaptation','Compose/qualify compatible retained sources; current bronchial tree needs revision and HRA lung source omits main bronchi/trachea.','reviews/lung_pair/2026-10-24-bounded-migration/README.md'),
('Airways & ducts','P2','Urinary collecting / outlet relationships','Proposed supplement','Kidneys lack pelvis/calyces/ureters; male contextual urethra lacks validated outlet/continuity; no dedicated source-qualified female urethra family.','models/kidney_left/README.md'),
('Airways & ducts','P2','Complete oral duct / mucosal context','Proposed supplement','Use existing gland envelopes; qualify excluded submandibular courses and absent sublingual/outlet anatomy.','reviews/salivary_glands/2026-10-26-native-scoped-r02/README.md'),
('Airways & ducts','P2','Biliary / pancreatic 3D relationships','Proposed supplement','Current 2D diagram explains routes; 3D gallbladder/pancreas evidence does not establish continuous ducts or flow.','diagrams/biliary_pathway/exports/r01/README.md'),
('Depth & relationships','P2','Detailed cardiac junctions','Proposed revision','Improve native chamber/vessel/valve relationships before expanding realistic-heart claims; opaque filtering only fixes presentation.','heart/exterior-presentation-r01/README.md'),
('Depth & relationships','P2','Joint cartilage / attachments','Proposed supplement','Regional bones/ligaments and cuff localization exist; no complete separate cartilage, validated tendon continuity or mechanics.','models/joints/exports/z-shoulder-r01/README.md'),
('Depth & relationships','P3','Internal neuroanatomy / neural continuity','Proposed supplement','External brain, representative spinal roots and three regional nerves leave internal tissue, plexuses and integrated CNS–PNS context unresolved.','models/brain/exports/bodyparts3d-4.0-atlas-r2/README.md'),
('Depth & relationships','P3','Middle / inner ear','Proposed node','External pinnae exist; source-qualified canal, tympanic and deeper hearing structures have no dedicated 3D family in this snapshot.','models/ears_z/exports/r04/README.md'),
('Depth & relationships','P3','Skin layers','Proposed node','Body-envelope navigation exists; a small skin-layer teaching cutaway would add a distinct depth use. Reuse source evidence before maintaining a variant.','models/skin/exports/bp3d-envelope-r01/README.md'),
]

# Report every encountered prose/source disagreement; do not silently rewrite immutable history.
MISMATCHES=[
{'label':'Eye provider coverage vs actual source inventory','evidence':'reviews/eye_anterior_segment/2026-10-27-source-coverage-r01/source-inventory.json','other':'models/eye_anterior_segment/README.md','fix':'Use component-level names: optic disc and ciliary muscle exist; no separately named optic nerve, extraocular muscle or long posterior ciliary artery. Keep provider-distribution discrepancy unresolved.'},
{'label':'Trabecular voxel spacing','evidence':'assemblies/marrow-comparison/2026-10-23/README.md','other':'reviews/draft_bone/2026-10-23-marrow-comparison/bounded-record.json','fix':'Reconcile 17.409 µm header-derived spacing with 17.59 µm prose. Retain original provenance and identify the corrected display scale.'},
{'label':'Heart applicability gap text is stale','evidence':'heart/exterior-presentation-r01/README.md','other':'reviews/heart_exterior/2026-11-01-fitted-applicability/README.md','fix':'Link the 1 November exact-fitted correspondence pass in the earlier README; preserve its dated boundary. No fitted export, wall repair, clinical or runtime promotion follows.'},
]

coverage=read('reviews/accounting/2026-10-23/coverage-summary.json')
snapshot=json.loads((OUT/'app/src/data.json').read_text())
def source(paths,detail):
    paths=list(dict.fromkeys(paths))
    return {'name':'med-assets · '+REV[:12], 'files':paths,'links':[{'label':p,'url':url(p)} for p in paths], 'evidenceFlow':[{'title':'Repository snapshot','detail':detail+' Exact commit '+REV+'. No remote availability, new renders, geometry/anatomy review or live asset-runtime testing in this survey.'}]}
snapshot.update(title='Medical model survey',buildStatus='creating',generatedAt='2026-11-06T00:00:00Z',report={'asOf':'2026-11-06'},survey={'revision':REV,'familyCount':len(rows),'productCount':len(products),'glbPaths':len(media),'assetGlbPaths':sum(m['role']=='Asset export' for m in media),'localGlbs':sum(m['availability']=='Local bytes' for m in media),'pointerGlbs':sum(m['availability']!='Local bytes' for m in media),'overlaps':[{'title':a,'action':b,'detail':c,'ids':d} for a,b,c,d in OVERLAPS],'gaps':[{'group':a,'priority':b,'label':c,'state':d,'scope':e,'source':url(f),'path':f} for a,b,c,d,e,f in GAPS],'mismatches':[{**m,'url':url(m['evidence']),'otherUrl':url(m['other'])} for m in MISMATCHES]})
snapshot['queries']={
 'model_survey':{'rows':rows,'source':source([r['evidence']['path'] for r in rows],'Complete indexed models/* family coverage; curated system/purpose slices are interpretations; gates retain their recorded scope and date.')},
 'products':{'rows':products,'source':source([r['evidence']['path'] for r in products],'Assemblies, body/heart products, diagrams and lessons shown separately from 62 individual-model families.')},
 'baseline_status':{'rows':[{'status':k.replace('-',' ').title(),'count':v} for k,v in coverage['baselineVisualStates'].items()],'source':source(['reviews/accounting/2026-10-23/coverage-summary.json','reviews/accounting/2026-10-23/baseline-decisions.json'],'Historical 2026-10-23 accounting for 62 original baseline exports. Not a count or verdict for the 62 current models/* families or later scoped studies.')},
 'media_inventory':{'rows':media,'source':source(['docs/WORKFLOW.md'],'All indexed .glb paths. Asset exports distinguished from source/review inputs. Identical bytes at distinct paths are retained as paths. Read GLB JSON only when hydrated; no geometry/pixel assessment.')},
}
(OUT/'app/src/data.json').write_text(json.dumps(snapshot,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'families':len(rows),'products':len(products),'glbPaths':len(media),'pointerGlbs':snapshot['survey']['pointerGlbs'],'revision':REV,'states':dict(collections.Counter(r['state'] for r in rows))}))
