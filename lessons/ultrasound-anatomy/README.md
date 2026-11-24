# Ultrasound Anatomy · Abdomen

The first Gallery stop asks the learner to find the gallbladder along the liver edge. Open **Use Cases → Ultrasound Anatomy → Abdomen** in the local candidate. Choose a marker in the synthetic grayscale, reveal the matching section, then open the asset review and return to the same stop. The tour and asset review use separate routes. [Collection brief](../../docs/gallery/use-cases/ultrasound-anatomy.md) · [Route contract](../../docs/gallery/routes-and-api.md#page-links)

## Pose and source

[abdomen-gallbladder.json](abdomen-gallbladder.json) defines the fixed pose, frame, projection and exercise markers. The recipe reads the pinned s1233 liver and gallbladder segmentation files and shared 1.5 mm RAS grid from the [Workshop input record](../../assemblies/workshop-s1233/inputs.json). The authored contact sits near the anterior body boundary at RAS (72, 298.9, 333.7) mm. The ray center points posteriorly in axial slice 195. The 68° field displays 125 mm of radial depth, with patient right at image left. The contact is an illustration choice within the case frame.

The separately authored [anterior body locator](../../body/2d-v4/whole-body-anatomy-v4-spatial/README.md) has an approximate right upper abdominal probe marker. That atlas has its own schematic frame. The asset review keeps the [Body Systems assembly](../body-systems/README.md) and the [gallbladder model study](../../reviews/teaching-assessments/target-risk/README.md) as contextual evidence, with links to their exact media. The model's authored duct and cutaway anatomy remain separate from the sampled mask.

The two views sample the same label boundaries. The grayscale uses illustrative brightness, boundary highlights and texture. Only liver and gallbladder use sampled tissue labels. The near field and other tissues are graphic approximations. Use this view for the named landmark exercise. Independent ultrasound reference review is still needed for scanner appearance, the walls, and the modeled probe placement.

## Replay and identity

Use Python 3.12, NumPy 2.3.5 and Pillow 12.2.0 with libwebp 1.6.0. The masks are the exact public TotalSegmentator v2.0.1 files in s1233's segmentations directory. Credit Jakob Wasserthal, TotalSegmentator contributors and University Hospital Basel. Preserve the [Workshop terms](../../body/anatomy-workshop-r1/docs/licenses/NOTICE.md) for the derivative.

```sh
uv run --no-project --python 3.12 --with numpy==2.3.5 --with Pillow==12.2.0 \
  python lessons/ultrasound-anatomy/render_abdomen.py --masks "$S1233_MASK_DIR" \
  --output .artifacts/ultrasound-abdomen-replay
```

The renderer verifies both compressed inputs, their grid, the pose's slice position, and the markers' label occupancy before writing. Compare both regenerated WebPs with the [candidate delivery index](../../sites/anatomy-gallery/app/src/content/assets/local-delivery.json). That index pins the exact read routes and file identities. The existing body image is copied into the build only after a SHA-256 check. The local Gallery can prove the learner action and preserve the alternate view if media is unavailable. Public delivery requires its own selection and asset admission.
