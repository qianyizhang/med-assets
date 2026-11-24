# Body Systems

Use the ordinary [Anatomy Gallery preview](../../sites/anatomy-gallery/README.md#restore-and-build-locally) at `/#/use-cases/systems`. The [display index](display/index.json) is the maintained collection export. It binds the eleven systems, each matched pair and its original source image hashes. The Site's delivery index records the exact WebP bytes. Each source row contains a label and a local path. When a source has moved, the third value keeps its link valid at the pinned review revision.

The [Body Systems use-case brief](../../docs/gallery/use-cases/body-systems.md) owns the learner journey and display requirements.

The [dated Body Systems survey](../../sites/body-systems-survey/README.md) owns its report, optional 3D viewer, render recipes and teaching backup. After rebuilding the report and selecting the reviewed plates, run the exporter from the repository root with Pillow installed.

```sh
python3.12 sites/body-systems-survey/export_gallery.py
```

The exporter validates the selected PNGs against their render receipts and writes the display WebPs, collection index and Site delivery entries. Verify the display in the ordinary Gallery and preserve the original image identities when moving or replacing a plate. Restore the archived report through its [member manifest](../../sites/body-systems-survey/README.md#restore-the-media).

The Reproductive left-pickup stop uses the [shared ovary lesson](../ovary-tubal-context/README.md) for pelvic orientation, enlarged HRA-derived views and the source comparison. The display index preserves the original survey plates.
