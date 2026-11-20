# Migration to the unified gallery

**Draft implementation plan, 20 November 2026.** The destination for every public med-assets gallery experience is the existing Model Survey Site. This plan assigns content to its four surfaces. The [census](existing-visualizations.md) records existing experiences and their owners. The [glossary](../../GLOSSARY.md#gallery-and-surfaces) defines the destination terms. Storage services, repository evidence and private experiments keep their existing purposes.

## Destinations

| Existing experience | Destination and first acceptance check |
| --- | --- |
| Model Survey | Evolve in place into **Asset Library**. Keep family bookmarks, the FDI31 entry, exact downloads and the dedicated rubric link. A visitor can find two adrenal lineages, choose a revision and see its rating or **Unrated**. |
| Anatomy Verification | Give substantive findings a page in **Compare**, including single-revision checks against source evidence. Carry the candidate selection and evidence order from old bookmarks. Bring teaching-only pages such as oral spaces into **Use Cases**. Represent ledger statuses faithfully, including rejected or incomplete work. |
| Body & Heart | Give cardiac motion and imaging a flagship **Use Cases** page. Integrate the whole-body teaching material with Body Systems. Rebuild interactive views on the shared 3D scene, including the former studio. Prove a heart phase and slice still correspond after reload. Move scoped marrow and pelvic reviews to Compare and route downloads to exact Library exports. |
| Head & Neck Review | Combine the salivary location and duct course into a **Use Cases** stop. Link the exact glands and context exports in Library and the source crossing and limitations in Compare. This is the first complete legacy-host migration. |
| Airway Review | Give bronchial, tracheal and nasal studies revision-specific **Compare** pages. Add teaching views to respiratory Use Cases where they support the lesson. Preserve the distinction between trachea r05 and r06 and between the nasal airspace and its surrounding tissue. |
| Dental Review | Put the UFF specimen, dental tools and other public models in **Asset Library**. Give UFF extraction and FDI31 interface evidence separate **Compare** pages. Embed the UFF hard-tissue and void inspection as a preset with its limitations. Integrate dental lessons with Use Cases once their learning task works. |
| FDI31 Focus Review | Keep the existing retirement notice as a compatibility entry. Verify its links reach the exact Balanced specimen page and download after Library routing changes. The earlier interface study retains its own review identity. |
| Body Systems, One Breath and other local lessons | Bring Body Systems and substantial lessons such as One Breath into **Use Cases**. Preserve bilingual text, phase controls, evidence and static fallbacks. Fold arch identification, static locators and route diagrams into relevant teaching stops. Adrenal’s blind A/B study belongs in Compare. |
| Small collections, local prototypes and generated reports | Merge useful stops into a maintained use case. Collect distinct retained public experiments, such as a kidney locator trial or dental film treatment, in **Use Cases → Experiments & Archive**, with date, source and limitation. Omit duplicate shells, authoring harnesses and disposable renders from public navigation. Keep unique evidence with its package. The adrenal links pilot retires when the ordinary Site passes its round-trip checks. |

## Delivery order

1. **Account for assets and addresses.** The Library maintainer reconciles package records, scene inputs, atlas and lesson exports, existing catalogue entries and the Site delivery index. The tracked baseline at `22eb216` includes 146 GLB paths plus STL, OBJ and Blender files. Count lineages and revisions separately from file paths. Map each public asset to a discoverable Library entry, including historical revisions and public metadata-only entries. Map duplicate bytes to aliases. Record sources, authoring inputs, restricted files and internal fixtures with their owner and reason for exclusion. Keep missing public exports visible as unavailable. Success means every inventoried item has a disposition and every public scene object resolves to its revision or parent export.
2. **Prove the shared scene across the four surfaces.** The Site and Stage owners deliver one adrenal journey. Find r05 in Library, open the regional lesson, inspect r04/r05 in Compare, then reopen a pinned scene in Stage. Check exact model identity, part selection, camera, appearance, WebP poster, Back and direct reload. Exercise unavailable model and failed 3D load. Expose the poster and a return route. Start the planned ratings batch with Body Systems assets using the [rubric](../../guideline/asset-quality.md).
3. **Migrate Head & Neck end to end.** The study and Site owners publish its Library entries, lesson stop and saved review to the destination when authorized. Prove the source limitation survives the handoff. Check bookmarks and all nine manifest file addresses using the rules below. Use the resulting mapping and checks for other hosts.
4. **Move the remaining public experiences.** Import the Verification review directory and its fragments, then the Airway and Dental studies. Bring Body & Heart over in lesson-sized pieces, starting with one synchronized phase and slice. Test each specialist interaction in the shared scene before retiring the corresponding viewer. Classify the remaining small pages as a lesson stop, saved review, archive entry or retirement. An owner can keep an old route serving its experience while a required interaction is still missing.
5. **Retire old interfaces.** For each published address, record its destination or retirement notice, source owner and check result. Test old bookmarks with fragments in a browser and direct file consumers with their actual fetch rules. Publish redirects or notices only after their destinations pass. Complete consolidation when all maintained visitor journeys run on the unified Site, each old address has a tested disposition, and any remaining legacy endpoints serve compatibility only.

## Page addresses and file addresses

A page address opens an experience. A file address returns the bytes for a particular model or piece of evidence. For example, the [Head & Neck manifest](../../transport/manifests/7b3860f7d29b8cf4e19190dee4bf7499bbe69e9924c7057021460edc4239fe53.json) lists two GLBs and seven WebPs. The gland model entry identifies its original URL, repository path, 129,736 bytes and SHA-256 beginning `a53134ec`. Sending that request to an HTML retirement notice would break the download.

The following is a static comparison at `22eb216`. Group unique object URLs in the [transport manifests](../../transport/manifests/) by host and match each object's canonical `sha256` and `bytes` to an entry in the [Site delivery index](../../sites/model-survey/app/src/content/assets/r2-trial.json). A match identifies a recorded copy. Check live responses separately at cutover.

| Legacy host | Distinct file URLs in manifests | Matched in Site index |
| --- | ---: | ---: |
| Head & Neck Review | 9 | 9 |
| Airway Review | 13 | 13 |
| Dental Review | 28 | 24 |
| Anatomy Verification | 120 | 120 |
| Body & Heart | 19 | 19 |

The four unmatched Dental entries are the [mouth-mirror GLB and three PNGs](../../transport/manifests/96dfb7956224d3331b0a095f26e4d89f34e8d7a4c6054f8b52bc826b041dda45.json). Locate and verify those exact originals before retiring their delivery paths. The manifest counts establish historical addresses. Measure active consumption separately if needed.

For each wave, maintain a mapping from old URL (including any fragment) to new page, exact file or notice. Record expected media type and byte identity for files. New gallery pages load live 3D models from the Site’s hash-addressed R2 URLs. Serve migrated display images as WebP and preserve the original bytes at published evidence addresses. For compressed transport entries, check the recorded transport and decoded identities. [Display images](../../guideline/design.md#display-images) · [Delivery and backup](../../transport/README.md)

The [guarded LFS transport](../../tools/lfs_transport.py) reads digest-pinned manifests and refuses cross-origin redirects. For a legacy file URL used by that path, keep a compatible exact-byte response on the original host, or migrate the consumer through its own reviewed contract and verify it before retirement. Preserve historical manifests. A page redirect to the new Site can coexist with continued file delivery at the old paths.
