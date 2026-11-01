"""Guarded context-loss repair after the existing lifecycle-v2 package; no fetch."""
from pathlib import Path
import argparse
import hashlib
import json

LIFECYCLE_SOURCE = 'd11cffd8a69ee32cc70ccd6712064b5e5f4c8c0f9f710614453007c640461b1e'
LIFECYCLE_MODULE = '2e2b67adb61140feefa64ffae50207258aa507bb555ebe8549c6b7b0989e8969'
# Optional exact PR191 composition; its code is not a dependency of this package.
CAMERA_SOURCE = '855b9555acad27bdeb29876d02e3a72216fd659ed772dfa29cd166e16ffc9dc7'
CAMERA_MODULE = 'dcce015f6b0778337756ceaaa1f64aabed7e5db0137b17b62290e8bc4138be0f'
MODULE = 'context-loss.mjs'


def patched(raw):
    if hashlib.sha256(raw).hexdigest() not in (LIFECYCLE_SOURCE, CAMERA_SOURCE):
        raise ValueError('Expected exact lifecycle-v2 source, optionally composed with camera reset')
    text = raw.decode()
    replacements = (
        ('const lifecycle=createViewerLifecycle(window);',
         'let contextGuard=null;\nconst lifecycle=createViewerLifecycle(window);'),
        ('function paint(){',
         "function paint(){if(contextGuard?.lost)renderContextRecovery($('#error'),lang,()=>location.reload(),()=>lifecycle.disposed);"),
        ('lifecycle.own(()=>{controls.dispose();renderer.dispose()});',
         "lifecycle.own(()=>{controls.dispose();renderer.dispose()});contextGuard=watchContextLoss(canvas,lifecycle,()=>{state='blocked';$('#viewport').hidden=true;$('#controls').hidden=true;$('#controls').style.display='none';paint()});"),
        ("await lifecycle.wait(new GLTFLoader(manager).parseAsync(bytes,''))",
         "await contextGuard.wait(lifecycle.wait(new GLTFLoader(manager).parseAsync(bytes,'')))"),
        ("state='ready';paint();", "contextGuard.check();state='ready';paint();"),
        ("if(!disposed){state='blocked';", "if(!disposed&&!contextGuard?.lost){state='blocked';"),
    )
    for old, new in replacements:
        if text.count(old) != 1:
            raise ValueError('Expected unique context-loss integration anchor: ' + old)
        text = text.replace(old, new, 1)
    return ("import {watchContextLoss,renderContextRecovery} from './context-loss.mjs';\n" + text).encode()


def apply(directory):
    target = Path(directory)
    source = target / 'candidate.js'
    raw = source.read_bytes()
    output = patched(raw)
    dependencies = {'viewer-lifecycle.mjs': LIFECYCLE_MODULE}
    if hashlib.sha256(raw).hexdigest() == CAMERA_SOURCE:
        dependencies['camera-reset.mjs'] = CAMERA_MODULE
    for name, expected in dependencies.items():
        path = target / name
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError('Missing or changed exact dependency: ' + name)
    module = target / MODULE
    if module.exists():
        raise ValueError('Context-loss module already exists; use a fresh source copy')
    payload = (Path(__file__).parent / MODULE).read_bytes()
    module.write_bytes(payload)
    source.write_bytes(output)
    return {name: hashlib.sha256((target / name).read_bytes()).hexdigest()
            for name in ('candidate.js', MODULE)}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('review_dir', type=Path)
    print(json.dumps(apply(parser.parse_args().review_dir), indent=2))
