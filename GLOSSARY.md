# med-assets glossary

Shared terms for the public gallery and the anatomical relationships it presents.

## Gallery and surfaces

**Anatomy Gallery** is the unified public teaching-asset Site. **Surface** is a destination within it. **Model Survey** is the dated catalogue imported by Anatomy Gallery and retained in its archive.

| Canonical term | Meaning |
| --- | --- |
| Asset | An independently reusable work, such as a model, assembly, diagram or generator. Several use cases can use the same asset. |
| Asset Library | The Gallery’s curated index of publicly listable, reusable assets. An **asset page** brings together one asset’s revisions, parts, capabilities, uses and available exports. |
| Use Cases | Surface for authored teaching experiences. A **use case** answers a learner’s question. A **collection** groups related use cases. A **lesson stop** is one step within a use case. |
| Teaching | The learner’s view of a use case, such as a system assembly, diagram or ultrasound sweep presented for a particular question. |
| Development | The author’s view of the same use case. It connects a stop or keyframe to the exact assets and parts involved, open questions and evidence for decisions. |
| Experiments & Archive | Collection within Use Cases for retained public experiments and historical teaching material. An entry identifies its purpose, status and limitations. |
| Compare | Gallery tool for inspecting differences. A **comparison session** explores a question. A **saved review** records a dated finding with its exact inputs, decisive evidence and limits. |
| 3D Stage | Gallery tool for composing, inspecting, saving and exporting a 3D scene. |
| Asset lineage | The source and revision history of one asset. A family groups related lineages for discovery. |
| Asset revision | An identified iteration within a lineage. An **export** is a specific representation of that revision. **Recommended** identifies the revision selected by its maintainer. |
| Asset release | A revision issued for consumers of the asset. Its semantic version describes compatibility with earlier releases of that asset. |
| Teaching assessment | Four scores for a named learner task on an exact export. An exemption keeps the observed score and records its permitted use and reopening condition. |
| Collection teaching check | An action reviewed in its delivered lesson view or scene. The collection reports which required actions pass and which remain blocked. |
| 3D scene | One or more asset revisions composed for interactive display, including their placement, visible parts and appearance. |
| Scene preset | A saved, versioned configuration that reopens a scene in its intended view and state. Its persistent link identifies that preset revision. |
| Poster | A still image representing a view. A Stage-exported poster identifies the scene preset that produced it. |

## Anatomy and spatial alignment

**Anatomical frame**

A coordinate system with a defined origin, axes, anatomical directions,
laterality, and units.

**Native frame**

The anatomical frame retained from a specific source.

**Shared frame**

A frame in which multiple assets have documented relative positions,
orientations, and scale. The evidence may come from the original source
or from registration to a common reference.

**Registration**

Alignment of assets to a shared frame using corresponding anatomy. A
registration specifies the transformations that establish their relative
placement.

**Pose**

The configuration of articulated structures at a particular state, such as
the knee at 20° of flexion.

## Ultrasound acquisition

| Term | Meaning |
| --- | --- |
| Probe pose | Position and orientation of the transducer relative to the patient, including its contact point and indicator direction. Orbiting the viewing camera preserves the probe pose. |
| Scan plane | The two-dimensional slice through the anatomy defined by the beam direction and the lateral axis of the probe. |
| Imaging field | The part of the scan plane sampled by the probe. In the thyroid tour a linear array samples parallel lines across a rectangle of specified width and depth. |
| Imaging sector | A fan-shaped imaging field produced by a curved or phased array. Its opening angle and depth determine how much of the slice appears in the image. |
| Anatomical section | The anatomy intersected by the scan plane. Labels identify structures in that slice. |
| B-mode rendering | Formation of a grayscale ultrasound image from modeled tissues in the imaging field. Brightness represents modeled echo strength. |
| Simulated B-mode frame | One grayscale image rendered for a specific case, probe pose and instant. |
| Labeled tissue overlay | A map of the tissues in the anatomical section, aligned to the corresponding pixels of the simulated B-mode frame. |
| Tour | A teaching sequence that groups related sweeps. A full exam tour follows one case from referral through acquisitions to an impression. |
| Sweep | An ordered movement through probe poses. A **keyframe** identifies a named view in the sweep. A phase describes a portion of the movement, such as finding the acoustic window or rotating the probe. |
| Reference keyframe | A named pose in a sweep with a corresponding acquired ultrasound for comparison. A reference from another case illustrates the view and retains its own scale and anatomy. |

## Gallery presentation

**System assembly**

The gallery overview showing structures together with the placement and scale
documented for that grouping. A system can have more than one assembly plate
when its regions or variants have separate frames.

**Asset detail**

A focused gallery presentation of a structure, junction, route, or pose.
A detail can use an independent viewing scale or depict a schematic.

**View**

The camera direction and projection used to present an asset or assembly.

## Assembly status

**Partial assembly**

A system assembly with documented placement for selected structures or
regions of the intended system route.

**Illustrative placement**

An arrangement that uses staged positions or display scale to make a
teaching relationship visible.
