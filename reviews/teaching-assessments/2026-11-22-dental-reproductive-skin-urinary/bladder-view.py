"""Compare the source-context and focused base from the same exact GLB."""
import bpy
import json
from pathlib import Path
import runpy
import sys
from mathutils import Vector

root = Path.cwd()
output = Path(sys.argv[sys.argv.index('--') + 1]).resolve()
output.mkdir(parents=True, exist_ok=False)
helper = runpy.run_path('reviews/teaching-assessments/2026-11-21-form-followup/render.py')
model = 'models/bladder/exports/hra-female-context-r03/bladder_hra_female_context_r03.glb'
expected = '91f04d1c831a61944da116184f389461517587c90c91fd94e199fba1619aa6b9'
scene, objects, neutral = helper['open_export'](root, (model, expected, 2449600), 21)
scene.cycles.samples = 24
scene.cycles.use_denoising = True
scene.render.resolution_x = scene.render.resolution_y = 720
focus = [o for name,o in objects.items() if any(x in name for x in ('bladder_base', 'bladder_neck', 'trigone', 'ureteral_orifice'))]
assert len(focus) == 5
target, span = helper['crop'](focus)
rows = []
for key, direction in [('back-up',(0,1,.85)), ('front-up',(.4,-1,.85)), ('top-side',(.55,.3,1))]:
    for mode, visible in [('full',list(objects.values())),('base',focus)]:
        rows.extend(helper['capture'](scene, neutral, output, mode, visible, target, span*1.38,
                                      [(key,direction,('palette',))]))
receipt = {'asset': {'path': model, **helper['identity'](root / model)}, 'views': rows}
(output/'bladder-view.json').write_text(json.dumps(receipt, indent=2)+'\n')
