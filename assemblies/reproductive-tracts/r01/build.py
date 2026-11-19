"""Two independently editable regional assemblies. All Blender points in metres."""
import json
import sys
from pathlib import Path

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "tools"))
from teaching_scene import colorize, export, load_meshes, material, tube


INPUTS = json.loads((HERE / "inputs.json").read_text())


def materials():
    return {
        k: material(k, rgb) for k, rgb in {
            "gland": (.65,.42,.21), "reproductive tissue": (.55,.23,.18),
            "neck": (.66,.38,.26), "route": (.20,.46,.48),
            "context": (.42,.48,.51), "vesicular secretion": (.71,.50,.20),
            "gonad": (.72,.61,.44),
        }.items()
    }


def female():
    mats = materials()
    adnexa = load_meshes(**INPUTS['ovary'])
    for obj in adnexa:
        tone = "gonad" if "ovary" in obj.name else "route"
        if "fibria" in obj.name:
            tone = "gland"
        colorize(obj,mats[tone])
    retained = {"body_of_uterus", "lower_uterine_segment", "fundus_of_uterus",
                "anterior_wall_of_uterus", "posterior_wall_of_uterus", "cornua", "cervix", "vagina", "cervicovaginal_junction"}
    pelvis = load_meshes(**INPUTS['pelvis-f'], select=lambda n: n.removeprefix('VH_F_') in retained)
    for obj in pelvis:
        tone = "neck" if "cervi" in obj.name else "reproductive tissue"
        colorize(obj,mats[tone])


def nearest(mesh, xyz):
    p = Vector(xyz)
    return min((v.co.copy() for v in mesh.data.vertices),key=lambda v:(v-p).length_squared)


def male():
    mats = materials()
    gonads = load_meshes(**INPUTS['testes'])
    organs = load_meshes(**INPUTS['urethra-m'],select=lambda n:n.startswith(("Prostate ", "Urethra ", "Urinary bladder ")))
    for obj in gonads+organs:
        role = obj.name.split()[0].split('.')[0]
        tone = {"Epididymis":"reproductive tissue","Testis":"gonad","Prostate":"gland",
                "Urethra":"route","Urinary":"context"}[role]
        colorize(obj,mats[tone])
    urethra = next(o for o in organs if o.name.startswith("Urethra"))
    for sign,side in [(-1,"r"),(1,"l")]:
        ep = next(o for o in gonads if o.name.startswith('Epididymis.'+side))
        tail = min((v.co.copy() for v in ep.data.vertices),key=lambda p:p.z)
        def p(x,y,z):
            return (x*sign/1000, y/1000, z/1000)
        junction = p(9,36,837)
        outlet = nearest(urethra,p(1,13,821))
        tube(f"Ductus deferens.{side}",[tail,p(24,-43,757),p(33,-40,793),p(45,-36,835),
             p(46,-14,851),p(37,19,855),p(22,34,850),junction],.0016,mats["route"])
        # Lobulated, blind-ended gland. The folded tube tapers into a short duct.
        gland = [p(30,40,857),p(28,45,860),p(24,47,857),p(28,48,853),
                 p(23,47,851),p(24,45,847),p(19,43,846),p(18,40,843)]
        tube(f"Seminal vesicle.{side}",gland,.0036,mats["vesicular secretion"])
        tube(f"Vesicular duct.{side}",[gland[-1],p(14,39,840),junction],.0015,mats["vesicular secretion"])
        tube(f"Ejaculatory duct.{side}",[junction,p(7,32,833),p(4,25,828),outlet],.00125,mats["route"])


if __name__ == "__main__":
    output = Path(sys.argv[sys.argv.index('--')+1]).resolve()
    output.mkdir(parents=True,exist_ok=False)
    for name,make in [('female',female),('male',male)]:
        bpy.ops.wm.read_factory_settings(use_empty=True)
        make()
        bpy.ops.outliner.orphans_purge(do_recursive=True)
        export(output,name)
