# Food and secretion routes

Restore the local Blender scene and GLB files from the [body-systems teaching backup](../../../sites/body-systems-survey/README.md#restore-the-media).

Open [the GLB](digestive-route.glb) or [the editable Blender scene](digestive-route.blend). The plate at left shows source exteriors of the upper abdomen and bowel. The plate at right traces the lumen with a simplified surface. Follow the numbered **Food** meshes from mouth to anal outlet. Isolate any one to inspect its two open ends. Select **Accessory** with Food 01 or Food 05 to see the parotid duct enter the mouth or bile and pancreatic secretions enter the descending duodenum.

## Selection and placement

The [Workshop](../../../body/anatomy-workshop-r1/README.md) supplies stomach, liver, pancreas and gallbladder exteriors from the same case. Its alternate stomach section omits gastric inlet and outlet. The [small](../../../models/small-intestine/exports/source-candidate-v4/README.md) and [large bowel](../../../models/large-intestine/exports/source-candidate-v4/README.md) provide 55 and 10 disconnected exterior components, respectively. Those candidates preserve more of the morphology than a swept surface. Neither selection establishes a single open lumen. The separate esophageal wall section and parotid study show regional detail. The existing [biliary diagram](../../../diagrams/biliary_pathway/exports/r01/README.md) supplies the confluence plan. The route plate adds an editable sequence, with the organ exteriors available alongside for comparison. This assembly owns the additions and serves the body-systems survey.

Blender metres, +X patient left, −Y anterior, +Z superior. In glTF these become +X left, +Y superior, +Z anterior. Both plates face the reader with patient right at screen left. Workshop translation in Blender is (−0.105, 0, +0.335) m. Both BP3D bowel meshes are translated (−0.105, 0, −0.910) m. Each source group retains its internal orientation and scale. These separated groups and the right-hand plate have no cross-dataset registration. Textures, gastric variants and bowel motion are omitted from this static matte composition. Relative heights between plates have no metric meaning.

The right plate uses named illustrative segments and an abbreviated intestinal course. In build.py, FOOD specifies the cross-sections in millimetres. The transverse colon passes anteriorly. The two ducts converge into a short common channel entering Food 05. Saliva exemplifies one parotid route. These route and opening shapes are authored. The bile and pancreatic ducts share one illustrative drainage pattern. Physiological variation, complete salivary drainage, wall thickness, mucosa, bowel packing and peristalsis are outside scope.

## Inputs and reuse

[Input paths and SHA-256](inputs.json) bind the six exterior GLBs. Workshop source surfaces derive from Jakob Wasserthal and TotalSegmentator contributors, University Hospital Basel, TotalSegmentator v2.0.1 under CC BY 4.0. [Dataset and modification notice](../../../body/anatomy-workshop-r1/docs/licenses/NOTICE.md). BodyParts3D © The Database Center for Life Science, CC Attribution 4.0 International. [Full source and derivative notice](../../../sources/datasets/bodyparts3d/bowel-studies-4.0/ATTRIBUTION.md). Changes in this composition include separate group translations, matte materials and a static bowel pose. No external reference illustration was copied. The clinical reference for route order and secretions is [NIDDK, Your Digestive System & How It Works](https://www.niddk.nih.gov/health-information/digestive-diseases/digestive-system-how-it-works).

## Replay

At the repository root with Blender 5.2.3 and Python 3.12, choose fresh output directories. The build refuses an existing output or mismatched source bytes.

```sh
blender -b --factory-startup --disable-autoexec --python-exit-code 1 -P assemblies/digestive-route/r01/build.py -- .artifacts/digestive-replay
python3.12 assemblies/digestive-route/r01/check.py .artifacts/digestive-replay/digestive-route.glb
blender -b --factory-startup --disable-autoexec --python-exit-code 1 -P tools/render_teaching.py -- --glb .artifacts/digestive-replay/digestive-route.glb --views assemblies/digestive-route/r01/views.json --output .artifacts/digestive-render-replay
```

[Review, five image pairs and measured joins](../../../reviews/digestive-route/r01/README.md)
