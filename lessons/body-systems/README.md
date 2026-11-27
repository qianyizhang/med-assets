# Body Systems

Use the ordinary [Anatomy Gallery preview](../../sites/anatomy-gallery/README.md#restore-and-build-locally) at `/#/use-cases/systems`. The [display index](display/index.json) is the maintained collection export. It binds the eleven systems, each matched pair and its original source image hashes. The Site's delivery index records the exact WebP bytes. Each source row contains a label and a local path. When a source has moved, the third value keeps its link valid at the pinned review revision.

The [Body Systems use-case brief](../../docs/gallery/use-cases/body-systems.md) owns the learner journey and display requirements.

The [dated Body Systems survey](../../sites/body-systems-survey/README.md) owns its report, optional 3D viewer, render recipes and teaching backup. After rebuilding the report and selecting the reviewed plates, run the exporter from the repository root with Pillow installed.

```sh
python3.12 sites/body-systems-survey/export_gallery.py
```

The exporter validates the selected PNGs against the survey plans and receipts. It writes the display WebPs, collection index, [replay bindings](display/replay-bindings.json) and Site delivery entries. When a source PNG matches its approved identity, it preserves the verified WebP bytes. A missing or invalid approved WebP requires exact reconstruction or restoration. Each replay binding uses the system, plate kind and plate ID. It records the survey scene and view, receipt identity, ordered PNG hashes and original mesh inputs. The index hash also remains bound to the [reviewed stops](reviewed-stops.json).

Seven tracked source GLBs have exact AssetKit recipe pins. The twelve archived meshes keep their teaching-media member identities. The two optional s1233 compositions keep their original Workshop recipe, build receipt and mask audit identities. The ordinary Gallery verifies the tracked bindings and WebP delivery without restoring survey inputs. Restore dated replay through the [teaching archive](../../sites/body-systems-survey/README.md#restore-the-media) and the [optional Workshop build](../../assemblies/workshop-s1233/README.md).

The optional 3D actions for Left vesical and Female context use the [pelvic layer config](../../sites/anatomy-gallery/app/src/content/gallery/pelvic-lesson-layers.json). Their native pins follow the selected assessments, actual rendered-layer selectors and source frame. The ordinary plate stays available independently. Use `assetkit impact` with the exact export key to trace the live and recipe uses. Recipe pins carry no runtime load.

Check the replay bindings against local survey receipts with:

```sh
python3.12 sites/body-systems-survey/export_gallery.py --check-replay-bindings
```

The Reproductive left-pickup stop uses the [shared ovary lesson](../ovary-tubal-context/README.md) for pelvic orientation, enlarged HRA-derived views and the source comparison. The display index preserves the original survey plates.
