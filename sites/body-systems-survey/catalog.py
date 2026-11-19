"""Selected teaching evidence, bound to the repository LFS index."""
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
BASE = "body/anatomy-workshop-r1/meshes"
FRONT = (0, -1, 0)
SIDE = (1, 0, 0)


def prepare():
    result = subprocess.check_output(["git", "lfs", "ls-files", "--long"], cwd=REPO, text=True)
    index = {path: digest for digest, _, path in (line.split(" ", 2) for line in result.splitlines())}
    jobs = []

    def select(path, role, *, surface=False, only=None):
        matches = [item for item in index if Path(item).match(path)]
        if len(matches) != 1:
            raise ValueError(f"Expected one indexed GLB for {path}: {matches}")
        match = matches[0]
        values = dict(path=match, sha256=index[match], role=role, surfaceOnly=surface)
        if only:
            values["only"] = only
        return values

    def asset(id, name, *sources, front=FRONT):
        jobs.append(dict(id=id, title=name, inputs=sources, front=front))

    def part(id, name, pattern, color, front=FRONT):
        asset(id, name, select(pattern, color), front=front)

    def workshop(name, role, surface=True):
        return select(f"{BASE}/{name}.glb", role, surface=surface)

    def animated(name, role):
        return select(f"body/breathing/{name}_breathing.glb", role, surface=name != "diaphragm")

    part("skin", "Adult external skin envelope", "models/skin/exports/*/*.glb", "skin")
    skeleton = select("models/skeleton/exports/*/*.glb", "bone")
    asset("skeleton", "Axial and appendicular skeleton", skeleton)
    part("knee", "Knee joint and soft-tissue context", "models/joints/exports/z-knee-r01/*.glb", "bone", SIDE)
    part("spinal-joint", "Lumbar vertebrae and disc", "assemblies/skeletal-teaching/*/L3-L4-disc.glb", "bone")
    part("costal-joint", "Rib, costal cartilage and sternum", "assemblies/skeletal-teaching/*/second-costal.glb", "bone")
    part("muscles", "Whole-body muscle surface study", "models/muscle/exports/*/*.glb", "muscle")
    part("achilles", "Achilles tendon, lower calf and heel context", "assemblies/musculoskeletal-teaching/2026-10-23/achilles-right-context.glb", "muscle", SIDE)
    part("rotator", "Shoulder and rotator cuff", "models/joints/exports/z-rotator-cuff-r01/*.glb", "muscle")
    part("brain", "Atlas brain", "models/brain/exports/bodyparts3d-4.0-atlas-r2/*.glb", "nerve")
    part("cord", "Spinal cord and representative roots", "models/spinal_cord/exports/authored-roots-r04/*.glb", "nerve")
    part("sciatic", "Sciatic nerve at the hip", "models/peripheral_nerves/exports/sciatic-hip-r01/*.glb", "nerve")
    part("eye", "Eye and orbital nerve courses", "models/eye_exterior/exports/*/*.glb", "nerve")
    part("ear", "Auricle exterior", "models/ears_z/exports/*/*.glb", "bone", SIDE)
    part("nose", "Nasal airspace", "models/nose_sinuses/exports/*/*.glb", "air", SIDE)
    part("tongue", "Tongue teaching study", "models/tongue_authored_study/exports/*/*.glb", "organ")
    part("pituitary", "Hypothalamus and pituitary stalk", "assemblies/hypothalamus-pituitary/*/*.glb", "gland")
    part("thyroid", "Thyroid with localized parathyroids", "models/parathyroids/exports/*/*thyroid_context.glb", "gland", (0, 1, 0))
    part("adrenals", "Adrenal glands", "models/adrenals/exports/*/*.glb", "gland")
    part("pancreas", "Pancreas exterior and regional context", "models/pancreas/exports/hra-female-context-r04/*.glb", "gland")
    part("heart-cut", "Cardiac Atlas cutaway", "heart/Cardiac_Atlas/exports/*Cutaway*.glb", "organ")
    part("aortic", "Aorta and selected arterial branches", "models/aortic_tree_z/exports/*/*.glb", "artery")
    asset("pulmonary-vein", "Pulmonary venous surface", workshop("pulmonary_vein", "vein"), front=(0, 1, 0))
    asset("cardio-context", "Heart, aorta and pulmonary venous context",
          workshop("heart", "organ"), workshop("aorta", "artery"), workshop("pulmonary_vein", "vein"))
    part("lymph-node", "Regional lymph node teaching mesh", "models/lymph_node/exports/*/*.glb", "lymph")
    part("lymph-routes", "Seven selected collecting routes", "models/lymph-collecting-routes/source-context-r01/*.glb", "lymph")
    part("thymus", "Thymus exterior", "models/thymus/exports/*/*.glb", "lymph")
    part("spleen", "Spleen exterior", "models/spleen/exports/hra-female-v1.10-r03/*.glb", "organ")
    part("larynx", "Pharynx and larynx exterior", "models/pharynx_larynx/exports/*/*.glb", "air", SIDE)
    part("trachea", "Trachea and primary bronchial openings", "models/trachea/exports/open-airway-r06/trachea-cutaway.glb", "air")
    asset("bronchi", "Authored lobar bronchial tree", workshop("bronchial_tree", "air"))
    asset("lungs", "Five lung lobes", workshop("lung_left", "lung"), workshop("lung_right", "lung"))
    part("diaphragm", "Diaphragm shape study", "models/diaphragm/exports/*/*_native_static.glb", "muscle")
    asset("breathing-context", "Lungs and diaphragm in the breathing assembly",
          animated("lung_left", "lung"), animated("lung_right", "lung"), animated("diaphragm", "muscle"))
    asset("lobar-context", "Five lung lobes and illustrative lobar airway",
          workshop("lung_left", "lung"), workshop("lung_right", "lung"), workshop("bronchial_tree", "air"),
          front=(0, 1, 0))
    part("oral", "Teeth and gingiva", "models/teeth_gums/exports/*/*.glb", "bone")
    part("salivary", "Salivary glands and source-named parotid ducts", "models/salivary_glands/exports/*/glands-and-parotid-ducts.glb", "gland")
    part("esophagus", "Esophageal wall cutaway", "models/esophagus_wall/exports/*/*.glb", "organ")
    asset("stomach", "Stomach exterior", workshop("stomach", "organ"))
    asset("liver", "Liver exterior", workshop("liver", "organ"))
    asset("gallbladder", "Gallbladder exterior", workshop("gallbladder", "duct"))
    small = select("models/small-intestine/exports/*/*.glb", "organ")
    large = select("models/large-intestine/exports/*/*.glb", "duct")
    asset("small-bowel", "Small intestine", small)
    asset("large-bowel", "Large intestine", large)
    asset("upper-digestive", "Upper abdominal digestive organs",
          workshop("stomach", "organ"), workshop("liver", "organ"),
          workshop("pancreas", "gland"), workshop("gallbladder", "duct"))
    asset("bowel-context", "Small and large bowel in the BP3D source frame", small, large)
    asset("kidneys", "Paired kidneys in the Workshop frame",
          workshop("kidney_left", "organ"), workshop("kidney_right", "organ"))
    asset("lower-urinary", "Bladder, bilateral schematic ureters and outlet", workshop("bladder", "organ"))
    asset("urinary-context", "Kidneys, ureters, bladder and outlet in the Workshop frame",
          workshop("kidney_left", "organ"), workshop("kidney_right", "organ"), workshop("bladder", "organ"))
    part("ovary", "Ovaries with fimbrial and tubal ends", "models/ovaries/exports/*/*.glb", "organ")
    part("uterus", "Uterus exterior", "models/uterus/exports/*/*.glb", "organ")
    part("pelvis-f", "Uterus, cervix and vagina in same-atlas pelvic context",
         "models/vagina_hra/exports/*/*.glb", "organ", SIDE)
    part("mammary", "Breast exterior study", "models/breasts_hra/exports/*/*.glb", "organ")
    part("testes", "Testes with epididymides", "models/testes/exports/*/*.glb", "organ")
    part("prostate", "Prostate surface parts", "models/prostate/exports/*/*.glb", "gland")
    part("urethra-m", "Male outlet context", "models/urethra_male/exports/*/*.glb", "organ", SIDE)
    part("penis", "Penile internal components", "models/penis/exports/*/*.glb", "organ", SIDE)
    print(json.dumps(jobs, indent=2))


if __name__ == "__main__":
    prepare()
