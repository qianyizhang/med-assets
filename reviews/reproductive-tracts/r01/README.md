# Reproductive tracts · 19 November 2026

Restore the local screenshots from the [body-systems teaching backup](../../../sites/body-systems-survey/README.md#restore-the-media).

[Assembly, sources and replay](../../../assemblies/reproductive-tracts/r01/README.md). Two fresh builds produced identical female and male GLBs. A clean reimport of each supplied every screenshot and [bilateral measurements](contacts.json).

| Export | GLB SHA-256 | Editable BLEND SHA-256 |
|---|---|---|
| Female, 19 meshes | `f5f58c4c4ccdb27a72b9cf1d2ff06a9c08d7240da01bca86ce5faef61f731817` | `12cce492d942f059302766f47083e43b98988be6c137b44a9d52d2db5262296d` |
| Male, 15 meshes | `278f42a5717e63ac3e44aa17a083c9b2794fa62691cf5dc8c537888f8999dffa` | `8204642d53cc3a67a61753a2cc03a8b53801bae9e886bae55820b2655946e7c3` |

| Question | Isometric | Straight |
|---|---|---|
| How do the tract and ovaries sit together? | [Female overview](female/context-iso.png) | [Anterior](female/context-ortho.png) |
| Where does pickup occur? | [Left adnexa](female/left-pickup-iso.png) | [Left fimbriae and ovary](female/left-pickup-ortho.png) |
| Where do both tubes meet the uterus? | [Uterine horns](female/uterine-entry-iso.png) | [Posterior](female/uterine-entry-ortho.png) |
| How do the vasa approach the posterior bladder? | [Male overview](male/context-iso.png) | [Posterior](male/context-ortho.png) |
| Where does the male tract continue to the outlet? | [Route with overlying organs hidden](male/route-iso.png) | [Lateral](male/route-ortho.png) |
| How does a vesicle contribute secretion? | [Left gland, branch and ejaculatory duct isolated](male/left-confluence-iso.png) | [Anterior](male/left-confluence-ortho.png) |

**Technical.** Both isthmus–horn contacts lie within 0.035 mm by nearest vertex. The retained 2.28/2.49 mm ovary–fimbria separations demonstrate an open pickup relationship. Initially omitting the lower uterine segment produced a 5.845 mm body–cervix gap. Restoring the source segment gave coincident sampled vertices at both adjacent surfaces. The largest sampled male branch proximity was 1.129 mm at the thicker vesicle-to-duct transition. The measured tail-to-vas distances were 0.118 mm and ejaculatory-to-urethral distances 0.139 mm on each side. Duct checks use a local 7 mm search around the designated junction. Distances establish local adjacency, without proving luminal union.

**Visual.** Inspected six clean-import matched pairs. Ovaries, tubal arches and uterine entry are visible. The straight view separates the bilateral horns better than the overlapping oblique angle. Uterine walls and fundus close an apparent anterior defect seen in an earlier partial selection. In the male, the prostate hides part of the ducts. The separate route view exposes their convergence, and the posterior view shows both vesicles. A lateral camera superimposes symmetric vasa. The oblique and posterior views separate them. [Female image bindings](female/renders.json) and [male image bindings](male/renders.json).

**Anatomy.** Reference-screened for regional teaching. Female registration rests on native HRA coordinates and bilateral geometric proximity. The male epididymis and urethra retain upstream limitations. New vesicles and duct routes are schematic. Specialist and clinical validation remain open.

**Runtime.** Blender clean import, mesh selection and offline rendering exercised. Browser runtime unverified.
