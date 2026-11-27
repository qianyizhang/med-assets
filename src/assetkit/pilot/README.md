# AssetKit Phase 1 Pilot (Abdomen / Liver + Ultrasound)

Self-contained pilot demonstrating native `concepts.json`, `assets.json`, and `consumer.json` without modifying any existing repository packages.

## Try It

```sh
# 1. Validate polyhierarchical concept DAG, assets, provenance, and consumer pins
uv run assetkit --repo src/assetkit/pilot --native-only validate

# 2. Check delivery economy (100% part/byte utilization, 3x reuse on liver-s1233, 0 bloat)
uv run assetkit --repo src/assetkit/pilot --native-only economy

# 3. Inspect exact runtime load bundle for the focal-lesion ultrasound case
uv run assetkit --repo src/assetkit/pilot --native-only bundle ultrasound:case:abdomen:focal-lesion

# 4. List open anatomy gaps
uv run assetkit --repo src/assetkit/pilot --native-only gaps --prefix ultrasound:

# 5. Trace impact before editing liver-s1233
uv run assetkit --repo src/assetkit/pilot --native-only impact liver-s1233

# 6. Resolve candidates for a consumer requirement
uv run assetkit --repo src/assetkit/pilot --native-only resolve ultrasound:sweep:abdomen:liver
```
