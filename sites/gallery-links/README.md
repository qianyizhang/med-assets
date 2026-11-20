# Adrenal gallery pilot

Open the local Model Survey at **Adrenal pair**. **Review this version** opens the BodyParts3D verification record with its original two preview images. **Related teaching study** opens the s1233 endocrine comparison within the complete Body Systems gallery. **Browse adrenal models** returns to the same expanded family from either destination.

The pilot uses the survey’s real React interface and pinned snapshot. The local verification page reads the migrated candidate record and links to the published viewer. The builder checks that the candidate ID, indexed model path, local GLB bytes and full SHA-256 identify the survey export. The related link uses the study’s stable refinement ID. Each export retains its own review.

## Run locally

Restore the [Model Survey framework, installed dependencies and snapshot](../model-survey/README.md) and [Body Systems gallery inputs](../body-systems-survey/README.md). The local preview’s split snapshot supplies the original embedded posters.

```sh
python3.12 sites/gallery-links/build.py
```

Open `.artifacts/body-systems-survey-2026-11-19/adrenal-pilot/model-survey.html` from disk. For interactive 3D use the [existing loopback server](../body-systems-survey/README.md#open-in-3d). Its browser check accepts `--with-gallery-pilot`. A pilot build enables the new handoff controls for this family. Regular survey builds retain the general family bookmarks and the existing FDI31 link. The hosted sites have their own publication process.
