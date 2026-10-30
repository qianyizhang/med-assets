# HRA ovary and tubal context intake

Four exact official exports supply a coarse bilateral ovary–tubal-end subset:
ovaries v1.3 and fallopian tubes v1.2, each source-labelled left/right. The
[manifest](source-manifest.json) pins all 14 acquired files by repository commit,
URL, size, SHA-256 and Git blob SHA-1. Original bytes and source-specific metadata,
crosswalks and attribution are retained. See [credits and license](ATTRIBUTION.md).

The ten mesh leaves explicitly identify `#VHFemaleOrgans` in both native GLB
extras and the pinned female mapping v1.10. Source names, labels and ontology
representations match; all source nodes use default identity transforms.
The [frame evidence](frame-evidence.json) records that preflight. Native positions
were inspected together without fitting. This supports co-rendering the selected
subset, not a claim of confirmed patient orientation or anatomical completeness.
L/R remain source labels.

The mapping CSV has no header. Its eight columns are anatomical_structure_of,
source_spatial_entity, node_name, label, ontology_id, representation_of, node_type,
single_organ_export. The two ovary surfaces are coarse (214 and 207 vertices).
The eight tube leaves retain their exact names, including the upstream `fibria`
spelling. No follicles, ovarian/suspensory ligaments or mesovarium are acquired.
The ligament/mesovarium mapping rows refer to a different, unacquired export;
they are not geometry in this package.

The [builder](../../../../tools/ovary_tubal/build.py) fails if any acquired byte
identity changes and checks source spatial identifiers before combining. It
recovers every original JSON array and complete BIN chunk from the combined
artifact after reversing only index/offset rebasing. There is no mesh fitting,
surface repair, connection, animation transfer or resampling.
