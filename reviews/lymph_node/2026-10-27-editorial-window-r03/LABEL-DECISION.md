# Vascular label decision — HRA male lymph node v1.2

**Use “Source vascular network (identity unresolved)”.** Preserve the original
node name, provider labels and ontology fields in the source and derivative.
Do not rename the network to blood or lymph on the strength of its pink color
or branching appearance.

The pinned source GLB (`7b047002cbb1dc06f37baa441783390d76cdb444b6144d6caa623923707953fd`)
names the node `Yao_blood_vasculature`, while its extras say `Lymph vasculature`,
`UBERON:0004536`. Those are conflicting source annotations, not two independently
validated identifications.

Primary evidence checked on 2026-10-27:

- [HRA v1.2 release record](https://github.com/hubmapconsortium/ccf-releases/blob/main/v1.2/markdown/ref-organs/lymph-node-male.md),
  Git blob `b362a06c6eaa8505825423850e07310118c32eba`, and
  [DataCite metadata](https://github.com/hubmapconsortium/ccf-releases/blob/main/v1.2/xml/3dref_lymph_node_m.xml),
  blob `7ddf1800c3c24737b44037a5c6e1cfd39b04d4bd`: creators, DOI,
  version and CC BY 4.0 are documented; neither supplies a mesh-specific correction.
- [Provider ASCT-B lymph-node table](https://github.com/hubmapconsortium/ccf-releases/blob/main/v1.2/asct-b/ASCT-B_NIH_Lymph_Node.csv),
  blob `2930b142546308d3d37611014f57b4ec156bc072`: distinguishes blood
  arterioles/venules from lymphatic vessels and sinuses. It does not assign the
  disputed network's mesh vertices to one of those systems.
- [Columbia histology lymph-node specimens](https://histologylab.ctl.columbia.edu/lab08/lymph-nodes/):
  blood and efferent lymphatic vessels occur in the hilar region; paracortical
  venules and lymphatic sinuses are distinct. Their coexistence prevents using
  location alone to adjudicate this mesh.

The available evidence supports an explicit unresolved label. Definitive
relabeling needs a provider erratum or a validated source-to-structure mapping.
Follicle and paracortex names are also provider annotations, supported as general
regions by the anatomy references; no histological ground truth or specialist
acceptance is inferred for these particular surfaces.

Citation: Kristen Browne; Heidi Schlehlein. 2022. *3D Reference Organ for Lymph
Node, Male v1.2*. [DOI 10.48539/HBM299.VVXH.634](https://doi.org/10.48539/HBM299.VVXH.634).
CC BY 4.0. Any display-window changes are editorial omissions, with no provider
endorsement or clinical claim. No reference photographs or histology images
are copied by this decision.
