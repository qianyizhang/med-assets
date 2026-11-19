"""Documented assembly choices and named display parts for the body-systems gallery."""

from hashlib import file_digest
import json
import os
from pathlib import Path
import re

SOURCE = Path(__file__).resolve().parent
REPO = Path(os.environ.get("MED_ASSETS_REPO", SOURCE.parents[1])).resolve()
GALLERY = REPO / ".artifacts/body-systems-survey-2026-11-19"
GALLERY_VIEWS = GALLERY / "presentation-r01"
WORKSHOP_ASSEMBLIES = GALLERY / "workshop-s1233-r01"
WORKSHOP_CONFIG = SOURCE.parents[1] / "assemblies/workshop-s1233/inputs.json"

# Hue and lightness both change between sequential entries. Legends identify every role.
PALETTE = (
    "#206C94", "#E8A34A", "#8E3B60", "#54BCAD", "#514587", "#E77459",
    "#2B7948", "#E7CE71", "#784533", "#6CAFE3", "#AD528C", "#ABC373",
    "#4D6773", "#EB957B", "#453444", "#8A6C2A",
)
FRONT = (0, -1, 0)
BACK = (0, 1, 0)


def load(filename):
    return json.loads((SOURCE / filename).read_text())


def study_records(system):
    study = system["study"]
    owner = REPO / study["owner"]
    review = REPO / study["review"]
    for receipt in sorted(review.rglob("renders.json")):
        record = json.loads(receipt.read_text())
        matches = list(owner.rglob(record["glb"]))
        if len(matches) != 1:
            raise ValueError(f"Cannot resolve {record['glb']} for {receipt}")
        folder = receipt.parent.relative_to(review).as_posix()
        yield receipt, record, matches[0], "" if folder == "." else folder + "/"


def rules(*entries):
    return [
        dict(label=label, pattern=pattern, color=PALETTE[index],
             alpha=opacity[0] if opacity else 1)
        for index, (label, pattern, *opacity) in enumerate(entries)
    ]


DETAIL_RULES = {
    "skeletal": rules(("Femur", "femur$"), ("Tibia", "tibia$"), ("Fibula", "fibula$"),
                      ("Load and support", "load|support"), ("Pose labels", "caption")),
    "muscular": rules(("Achilles tendon", "tendon"), ("Heel bone", "calcaneus"),
                      ("Medial gastrocnemius", "medial head"), ("Soleus", "soleus"),
                      ("Lateral gastrocnemius", "lateral head"), ("Tibia", "tibia"),
                      ("Talus", "talus"), ("Fibula", "fibula")),
    "respiratory": rules(("Tracheal shell", "V7.*shell"), ("Tracheal cartilage", "C-band"),
                         ("Main bronchial route", "V7 guide"), ("Nasal wall", "sagittal wall"),
                         ("Conchae", "conchal"), ("Nasal passage", "Nasal.*Passage"),
                         ("Pharyngeal route", "^Pharynx"), ("Laryngeal cartilage", "larynx.*cartilage|larynx.*epiglottis"),
                         ("Laryngeal passage", "laryngeal passage"), ("Lobar branch", "^Branch"),
                         ("Terminal bronchioles and ducts", "^Terminal.*bronchiole|^Terminal.*duct"),
                         ("Alveolar cups", "alveolar cup")),
    "urinary": rules(("Kidney sections", "closed-back"), ("Medullary pyramids", "pyramid"),
                     ("Calyces", "calyx"), ("Renal pelvis", "pelvis funnel"),
                     ("Ureters", "^(Left|Right).*ureter"), ("Bladder", "^bladder.*section"),
                     ("Trigone", "trigone"), ("Bladder neck and urethra", "urethral"),
                     ("Flow cues", "^Flow"), ("Arterioles", "arteriole"),
                     ("Glomerular tuft", "capillary tuft"), ("Bowman capsule", "capsule"),
                     ("Proximal tubule", "proximal tubule")),
    "cardiovascular": rules(("Right atrium", "^01 "), ("Tricuspid valve", "^02 "),
                            ("Right ventricle", "^03 "), ("Pulmonary valve", "^04 "),
                            ("Pulmonary bed", "^05 "), ("Left atrium", "^07 "),
                            ("Mitral valve", "^08 "), ("Left ventricle", "^09 "),
                            ("Aortic valve", "^10 "), ("Systemic bed", "^11 "),
                            ("Connectors", "^Bridge"), ("Direction cues", "^Direction"),
                            ("Labels", "^Label")),
    "digestive": rules(("Oral cavity", "Food 01"), ("Pharynx", "Food 02"),
                       ("Esophagus", "Food 03"), ("Stomach", "Food 04|Source stomach"),
                       ("Duodenum", "Food 05"), ("Small bowel", "Food 06|Source small"),
                       ("Ascending colon", "Food 07"), ("Transverse colon", "Food 08"),
                       ("Descending colon", "Food 09"), ("Rectum and anal canal", "Food 10"),
                       ("Large bowel exterior", "Source large"), ("Liver", "Source liver"),
                       ("Gallbladder and bile ducts", "gallbladder|Accessory Bile"),
                       ("Pancreas and duct", "pancrea"), ("Salivary duct", "saliva"),
                       ("Common channel", "common channel")),
    "nervous": rules(("Brain", "^Central.*Brain"), ("Cord and bridge", "Authored cord|Cervicomedullary"),
                     ("Dorsal roots and column", "dorsal"), ("Ventral roots and ramus", "ventral"),
                     ("Mixed nerves", "mixed nerve"), ("Sciatic nerve", "sciatic"),
                     ("Outer ear and canal", "auricle|external acoustic canal"),
                     ("Tympanic membrane", "tympanic"), ("Ossicles", "malleus|incus|stapes"),
                     ("Cochlear structures", "cochlear|corti|spiral ganglion"),
                     ("Vestibular structures", "^Ear.*(canal|macula|utricle|saccule|vestibu)"),
                     ("Common nerve VIII", "VIII common"), ("Globe and epithelium", "sclera|epithelium|papilla section"),
                     ("Sensory receptors", "retinal strip|rod|receptor|cilia|cilium|taste bud|microvillus|basal ending"),
                     ("Relay and afferent neurons", "^Vision|^Smell|^Taste")),
    "endocrine": rules(("Hypothalamus and pituitary", "^Hypothalamus"), ("Thyroid", "Thyroid gland"),
                       ("Parathyroids", "parathyroid"), ("Adrenals", "^Adrenal"),
                       ("Pancreas", "^Pancreas"), ("Ovaries", "^Pelvic ovary"),
                       ("Testes", "^Alternative testis"), ("TRH signal", "^TRH"),
                       ("TSH signal", "^TSH"), ("Islet alpha cells", "alpha cell"),
                       ("Islet beta cells", "beta cell"), ("Islet capillary", "capillary"),
                       ("Outline and inset frames", "outline| frame$", 0.36)),
    "lymphatic": rules(("Tissue and initial capillaries", "initial capillary|tissue drainage"),
                       ("Afferent vessels", "afferent"), ("Node capsule", "capsule"),
                       ("Intranodal passage", "intranodal"), ("Efferent vessels", "efferent"),
                       ("Cisterna chyli", "cisterna"), ("Thoracic duct", "thoracic duct|terminal duct"),
                       ("Venous confluence", "vein"), ("Spleen", "^Spleen"),
                       ("Thymus", "^Thymus")),
    "female": rules(("Ovaries", "ovary"), ("Fimbriae and infundibula", "fibria|fimbria|infundibulum"),
                    ("Tubal ampullae", "ampulla"), ("Tubal isthmuses", "isthmus"),
                    ("Uterus", "uterus|cornua|uterine.segment"), ("Cervix", "cervi"), ("Vagina", "vagina")),
    "male": rules(("Testes", "^Testis"), ("Epididymides", "^Epididymis"), ("Ductus deferens", "^Ductus"),
                  ("Seminal vesicles", "^Seminal"), ("Vesicular ducts", "^Vesicular"),
                  ("Ejaculatory ducts", "^Ejaculatory"), ("Prostate", "^Prostate", 0.48),
                  ("Bladder", "^Urinary bladder", 0.55), ("Urethra", "^Urethra")),
    "integumentary": rules(("Epidermis", "epidermis"), ("Dermis", "Dermis"),
                          ("Subcutaneous tissue", "subcutaneous|fat lobule"), ("Hair", "hair root"),
                          ("Follicle", "follicle"), ("Sweat gland", "eccrine"), ("Sweat duct", "sweat duct"),
                          ("Nail plate", "nail plate"), ("Nail bed", "nail bed"),
                          ("Nail matrix", "matrix"), ("Nail fold", "nail fold"), ("Digit tissue", "digit tissue")),
}

# An anatomical assembly only groups assets with a documented common frame.
# The local protocols also support editorial views, clearly marked at the system level.
ASSEMBLIES = {
    "skeletal": ("Native frame", "Whole-body skeleton",
                 "BodyParts3D skeleton and translucent envelope share the source frame.", "skeleton"),
    "muscular": ("Native frame", "Whole-body muscle atlas",
                 "Z-Anatomy positions and dimensions are retained. Plantarflexion is a separate regional pose.", "muscles"),
    "respiratory": ("Shared thoracic frame", "Lungs, lobar bronchi and diaphragm",
                    "The Workshop lung lobes and illustrative lobar tree share coordinates with the breathing diaphragm. The upper airway and enlarged alveoli are under Asset detail.", "thorax"),
    "urinary": ("Shared regional frame", "Bilateral urinary tract",
                "Workshop kidney and bladder sections keep their placement. The ureters are authored. The enlarged filtration inset is in Asset detail.", "urinary-overview"),
    "cardiovascular": ("Partial assembly", "Heart and proximal vessels",
                       "Workshop placements preserve the heart, aorta and pulmonary venous region. The exploded circulation loop traces the full route in Asset detail.", "cardio-context"),
    "digestive": ("Partial assembly", "Upper abdomen and bowel",
                  "The Workshop upper abdomen and native BodyParts3D bowel are two separate frames. The ordered food and accessory routes are in Asset detail.", "upper-digestive", "bowel-context"),
    "nervous": ("Illustrative placement", "Brain, cord and right sciatic pathway",
                "The central pathway stages independent source groups with authored bridges. Regional sensory insets have separate scales.", "nervous-central"),
    "endocrine": ("Illustrative placement", "Head-to-pelvis gland locator",
                  "The source groups retain their individual sizes. Their positions mix atlas sources and use a schematic outline. The alternate gonads, islet and signal route are in Asset detail.", "endocrine-overview"),
    "lymphatic": ("Illustrative placement", "Lymphatic return and organ landmarks",
                  "The source duct anchors the route. The node is 2.4× source size. The organ locators and terminal bridge are editorial.", "lymphatic-overview"),
    "reproductive": ("Shared regional frames", "Female and male reproductive tracts",
                     "Each tract keeps its own source frame. Male duct and vesicle geometry includes authored segments. The breast remains a regional source view.", "reproductive-female", "reproductive-male"),
    "integumentary": ("Body locator", "External body envelope",
                      "The envelope gives body context. The skin block and nail are independent local samples with illustrative dimensions.", "skin"),
}
TITLES = {"upper-digestive": "Upper abdomen", "bowel-context": "Small and large bowel",
          "reproductive-female": "Female pelvis", "reproductive-male": "Male pelvis"}


def baseline_jobs():
    return {job["id"]: job for job in load("jobs.json")}


def baseline_scene(key, inputs, front=FRONT):
    return dict(id=key, inputs=inputs, views=[dict(id="assembly", front=front)])


def original_scenes():
    jobs = baseline_jobs()

    def one(key, index, label, color, *, alpha=1, groups=()):
        return dict(jobs[key]["inputs"][index], label=label, color=PALETTE[color],
                    alpha=alpha, groups=groups)

    def sources(key, specs):
        return [one(key, index, *spec) for index, spec in enumerate(specs)]

    yield baseline_scene("skeleton", [
        one("skeleton", 0, "Other bones", 12, groups=rules(
            ("Teeth", "tooth|molar|incisor|premolar|canine"),
            ("Cartilage and discs", "cartilage|disc"),
            ("Vertebrae", "vertebra|sacrum|coccyx"),
            ("Skull and jaw", "cranial|mandible|maxilla|zygomatic|frontal bone|parietal bone|occipital bone|temporal bone|ethmoid|sphenoid"),
            ("Ribs and sternum", "rib|sternum|manubrium"),
            ("Pelvis", "hip bone|ilium|ischium|pubis"),
            ("Upper limbs", "scapula|clavicle|humerus|radius|ulna|carpal|hand"),
            ("Lower limbs", "femur|tibia|fibula|patella|tarsal|foot|calcaneus|talus"),
        )),
        one("skin", 0, "Body envelope", 9, alpha=0.14),
    ])
    yield baseline_scene("muscles", [
        one("muscles", 0, "Other muscle groups", 12, groups=rules(
            ("Head and facial muscles", "eye|(?:lateral|medial|superior|inferior) rectus|(?:superior|inferior) oblique|orbicularis|buccinator|masseter|temporalis|tongue|mentalis|zygomatic|nasalis|frontalis"),
            ("Superficial shoulder and back", "trapezius|deltoid|latissimus|rhomboid|teres |infraspinatus|supraspinatus|subscapularis"),
            ("Chest and abdomen", "pectoralis|intercostal|serratus|rectus abdominis|abdominis"),
            ("Arm muscles", "triceps brachii|biceps brachii|brachialis|brachioradialis|anconeus"),
            ("Hip and thigh muscles", "gluteus|psoas|iliacus|sartorius|adductor|gracilis|vastus|femoris|semitendinosus|semimembranosus"),
            ("Leg muscles", "gastrocnemius|soleus|tibialis|fibularis|popliteus|plantaris"),
            ("Supporting connective tissue", "supporting connective"),
        )),
    ])
    yield baseline_scene("skin", [one("skin", 0, "External skin surface", 6)])
    yield baseline_scene("thorax", [
        one("lobar-context", 0, "Left lung", 3, alpha=0.36, groups=[
            dict(label="Left upper lobe", pattern="upper lobe", color=PALETTE[3], alpha=0.36),
            dict(label="Left lower lobe", pattern="lower lobe", color=PALETTE[5], alpha=0.42),
        ]),
        one("lobar-context", 1, "Right lung", 0, alpha=0.36, groups=[
            dict(label="Right upper lobe", pattern="upper lobe", color=PALETTE[0], alpha=0.42),
            dict(label="Right middle lobe", pattern="middle lobe", color=PALETTE[7], alpha=0.48),
            dict(label="Right lower lobe", pattern="lower lobe", color=PALETTE[4], alpha=0.42),
        ]),
        one("lobar-context", 2, "Lobar bronchi", 8),
        one("breathing-context", 2, "Diaphragm", 6),
    ], BACK)
    yield baseline_scene("cardio-context", sources("cardio-context",
                         [("Heart", 2), ("Aorta", 1), ("Pulmonary veins", 0)]), BACK)
    yield baseline_scene("upper-digestive", sources("upper-digestive",
                         [("Stomach", 0), ("Liver", 2), ("Pancreas", 1), ("Gallbladder", 6)]), (1, 0, 0))
    yield baseline_scene("bowel-context", sources("bowel-context",
                         [("Small bowel", 5), ("Large bowel", 0)]))

def detail_scene(system, record, model, prefix):
    system_id = system["id"]
    region = prefix.rstrip("/")
    display_rules = DETAIL_RULES[region or system_id]
    source = dict(path=model.relative_to(REPO).as_posix(), sha256=record["sha256"],
                  label="Other anatomy", color=PALETTE[-1], alpha=1, groups=display_rules)
    scene_id = system_id + ("-" + region if region else "")
    views = [
        dict(id=view["id"], include=view["visible"], frame=view["frame"],
             front=view["images"][1]["direction"], bounds=view["bounds"])
        for view in record["views"]
    ]
    if system_id == "urinary":
        overview = next(view for view in views if view["id"] == "overview")
        views.append(dict(id="tract", front=FRONT, include=[
            name for name in overview["include"]
            if not name.startswith("Filtration") and "filtrate" not in name
        ]))
    if system_id == "endocrine":
        glands = ("Adrenal", "Hypothalamus-pituitary", "Neck", "Pancreas",
                  "Pelvic ovary", "Head to pelvis")
        overview = next(view for view in views if view["id"] == "overview")
        views.append(dict(id="locator", front=FRONT,
                          include=[name for name in overview["include"] if name.startswith(glands)]))
    return dict(id=scene_id, inputs=[source], views=views)


def workshop_scenes():
    receipt_path = WORKSHOP_ASSEMBLIES / "assemblies.json"
    if not receipt_path.is_file():
        return
    receipt = json.loads(receipt_path.read_text())
    with WORKSHOP_CONFIG.open("rb") as source:
        if file_digest(source, "sha256").hexdigest() != receipt["configSha256"]:
            raise ValueError("Workshop assembly config differs from its build receipt")
    with (WORKSHOP_ASSEMBLIES / "mask-audit.json").open("rb") as source:
        if file_digest(source, "sha256").hexdigest() != receipt["maskAuditSha256"]:
            raise ValueError("Workshop mask audit differs from its build receipt")
    config = json.loads(WORKSHOP_CONFIG.read_text())
    for key, entry in config["assemblies"].items():
        groups = [dict(label=part["label"], pattern="^" + re.escape(part["label"]) + "$",
                       color=part["color"], alpha=0.55 if label in {"heart", "liver"} else 1)
                  for label, part in entry["parts"].items()]
        path = WORKSHOP_ASSEMBLIES / f"{key}.glb"
        source = dict(path=path.relative_to(REPO).as_posix(), sha256=receipt["artifacts"][key]["sha256"],
                      label="Other anatomy", color=PALETTE[-1], alpha=1, groups=groups)
        views = [dict(id="assembly", front=entry["front"]),
                 dict(id="route", front=entry["front"],
                      include=[entry["parts"][label]["label"] for label in entry["route"]])]
        yield dict(id=key + "-s1233", inputs=[source], views=views)


def render_plan():
    yield from original_scenes()
    yield from workshop_scenes()
    for system in load("systems.json"):
        for _, record, model, prefix in study_records(system):
            yield detail_scene(system, record, model, prefix)
