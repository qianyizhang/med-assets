# Source and derivative attribution

**Z-Anatomy — The libre 3D atlas of anatomy — CC BY-SA 4.0.**
**BodyParts3D — The Database Center for Life Science — CC BY-SA 2.1 Japan** (historical attribution retained by Z-Anatomy).

Original model: Kousaku Okubo. Z-Anatomy design/3D/anatomy: Gauthier Kervyn. Blender add-on author credited by project: Marcin Zielinski.

- Official project: https://github.com/Z-Anatomy/Models-of-human-anatomy
- Official license: https://github.com/Z-Anatomy/Models-of-human-anatomy/blob/master/License.txt
- License: https://creativecommons.org/licenses/by-sa/4.0/
- Original archive: https://raw.githubusercontent.com/Z-Anatomy/Models-of-human-anatomy/master/Z-Anatomy.zip
- Archive SHA256: `e029688545627bd0214b269e1063143abb580aad72b2c2445d6d8a9a0d9da736`
- Original `Startup.blend` SHA256: `9f08a17ea0115fed80b2a73ecdf0a1bc2ab2f6956f37c593ce23d513ea35afcd`

The included native `.blend` subsets preserve selected provider object datablocks and dependencies; evaluated OBJ files are separately identified derivatives, not original provider OBJ. The source archive's Python/add-on code was not executed or installed. Inspection/extraction used existing Blender with `--factory-startup --disable-autoexec`.

The source project lists kidney and inner-ear noncommercial exceptions. Neither kidney/inner-ear tissue geometry nor their images are included. Selected arterial, heart-region and vertebral source objects are attributed under the project's stated CC BY-SA 4.0 license; full provider license/README retained. The source's additional Brainder/White matter and cranial-nerve acknowledgments remain in License.txt; do not infer a per-object origin where the provider does not state one.

## Changes / license of derived files

Aortic r01 selects 15 named original curve objects, evaluates original geometry in original native world coordinates, and applies an illustrative red material. Aortic r02 merges six numerically coincident adjoining curve endpoints with matching radii, retaining original control points and incoming/outgoing Bézier handles, then increases longitudinal/bevel sampling. No new anatomical paths or vessel lumina are invented. Open end rims and intersecting branch surfaces remain. Source definitions, change metrics, exact-export checks and screenshot hashes accompany the derivative.

Aortic model derivatives and rendered evidence are distributed under **CC BY-SA 4.0**. Retain attribution, license link and change description, and distribute adaptations under the same license. Do not relabel these Z-Anatomy derivatives CC BY 4.0 based on the later license of independent BodyParts3D downloads.
