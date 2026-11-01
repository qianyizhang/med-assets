"""Private source-bound cached-navigation patch. No fetch, Git or publication."""
from pathlib import Path
import hashlib
import json
import argparse

BASE_SHA = '9214093398033ab75beeec8c273d1f85a28408ee6096f3fe0bb91723ecc6f80b'
MODULE = 'viewer-lifecycle.mjs'


def patched(raw):
    if hashlib.sha256(raw).hexdigest() != BASE_SHA:
        raise ValueError('candidate.js does not match canonical v40 baseline')
    text = raw.decode()
    replacements = [
        ("let lang='en',data,record,state='loading',fit=()=>{},cleanup=()=>{};", "const lifecycle=createViewerLifecycle(window);\nlet lang='en',data,record,state='loading',fit=()=>{},cleanup=()=>lifecycle.fail();"),
        ("$('#language').onclick=()=>{lang=", "$('#language').onclick=()=>{if(lifecycle.disposed)return;lang="),
        ("el.onclick=()=>fit(el.dataset.view)", "el.onclick=()=>{if(!lifecycle.disposed&&!lifecycle.failed)fit(el.dataset.view)}"),
        ("await fetch('review-data.json',{credentials:'omit'})", "await lifecycle.wait(fetch('review-data.json',{credentials:'omit'}))"),
        ("await res.json()", "await lifecycle.wait(res.json())"),
        ("await fetch(url,{credentials:'omit',redirect:'error'})", "await lifecycle.wait(fetch(url,{credentials:'omit',redirect:'error'}))"),
        ("await decodeTransport(await response.arrayBuffer(),record.source)", "await lifecycle.wait(decodeTransport(await lifecycle.wait(response.arrayBuffer()),record.source))"),
        ("await crypto.subtle.digest('SHA-256',bytes)", "await lifecycle.wait(crypto.subtle.digest('SHA-256',bytes))"),
        ("window.addEventListener('pagehide',()=>URL.revokeObjectURL(downloadURL),{once:true})", "lifecycle.own(()=>URL.revokeObjectURL(downloadURL),'document')"),
        ("await Promise.all([import('../vendor/three.module.js'),import('../vendor/OrbitControls.js'),import('../body/3d/vendor/GLTFLoader.js')])", "await lifecycle.wait(Promise.all([import('../vendor/three.module.js'),import('../vendor/OrbitControls.js'),import('../body/3d/vendor/GLTFLoader.js')]))"),
        ("cleanup=()=>{controls.dispose();renderer.dispose()};", "lifecycle.own(()=>{controls.dispose();renderer.dispose()});"),
        ("await new GLTFLoader(manager).parseAsync(bytes,'')", "await lifecycle.wait(new GLTFLoader(manager).parseAsync(bytes,''))"),
        ("const resize=()=>{renderer.setSize", "const resize=()=>{if(lifecycle.disposed||lifecycle.suspended||lifecycle.failed)return;renderer.setSize"),
        ("const observer=new ResizeObserver(resize);observer.observe(wrap);resize();fit();let raf;function frame(){controls.update();renderer.render(scene,camera);raf=requestAnimationFrame(frame)}frame();cleanup=()=>{cancelAnimationFrame(raf);observer.disconnect();controls.dispose();renderer.dispose()};window.addEventListener('pagehide',cleanup,{once:true});", "const observer=new ResizeObserver(resize);resize();fit();let raf=null,running=false,generation=0;function suspend(){running=false;generation++;if(raf!==null)cancelAnimationFrame(raf);raf=null;observer.disconnect()}function frame(token){if(!running||token!==generation||lifecycle.disposed||lifecycle.suspended)return;controls.update();renderer.render(scene,camera);if(running&&token===generation)raf=requestAnimationFrame(()=>frame(token))}lifecycle.own(suspend);lifecycle.attach({suspend,resume(){if(running||lifecycle.disposed)return;running=true;const token=++generation;observer.observe(wrap);resize();frame(token)}});"),
        ("}catch(err){cleanup();state='blocked';", "}catch(err){const disposed=lifecycle.disposed;cleanup();if(!disposed){state='blocked';"),
        ("console.warn('Isolated viewer:',err.message);}", "console.warn('Isolated viewer:',err.message);}}"),
    ]
    for old, new in replacements:
        if text.count(old) != 1:
            raise ValueError('Expected unique source integration anchor: '+old)
        text = text.replace(old, new, 1)
    return ("import {createViewerLifecycle} from './viewer-lifecycle.mjs';\n"+text).encode()


def apply(directory):
    target = Path(directory)
    source = target/'candidate.js'
    output = patched(source.read_bytes())
    if (target/MODULE).exists():
        raise ValueError('Lifecycle module already exists; use a fresh source copy')
    module = (Path(__file__).parent/MODULE).read_bytes()
    (target/MODULE).write_bytes(module)
    source.write_bytes(output)
    return {name: hashlib.sha256((target/name).read_bytes()).hexdigest() for name in ('candidate.js', MODULE)}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('review_dir',type=Path)
    print(json.dumps(apply(p.parse_args().review_dir),indent=2))
