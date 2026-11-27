# AssetKit Phase 1 Pilot (Abdomen / Liver + Ultrasound)

Self-contained pilot demonstrating native `concepts.json`, `assets.json`, and `consumer.json` with three consumer examples. Its s1233 exports have declared sizes and part weights. The pilot contains their metadata only.

## Try It

```sh
# 1. Validate polyhierarchical concept DAG, assets, provenance, and consumer pins
uv run assetkit --repo src/assetkit/pilot --native-only validate

# 2. Check delivery economy using declared weights and three uses of liver-s1233
uv run assetkit --repo src/assetkit/pilot --native-only economy

# 3. Inspect the planned loads and missing payloads for the focal-lesion ultrasound case
uv run assetkit --repo src/assetkit/pilot --native-only bundle ultrasound:case:abdomen:focal-lesion

# 4. List open anatomy gaps
uv run assetkit --repo src/assetkit/pilot --native-only gaps --prefix ultrasound:

# 5. Trace impact before editing liver-s1233
uv run assetkit --repo src/assetkit/pilot --native-only impact liver-s1233

# 6. Resolve candidates for a consumer requirement
uv run assetkit --repo src/assetkit/pilot --native-only resolve ultrasound:sweep:abdomen:liver
```
