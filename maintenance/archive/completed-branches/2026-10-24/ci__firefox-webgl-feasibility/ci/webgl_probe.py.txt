#!/usr/bin/env python3
"""Bounded CI-only probe. No installs, WebDriver, browser preferences or GL flags."""
import base64
import hashlib
import http.server
import json
import os
from pathlib import Path
import secrets
import shutil
import signal
import struct
import subprocess
import sys
import tempfile
import threading
import time
import zlib

OUT = Path.cwd() / "webgl-probe-results"
SECURITY_KEYS = ("security.", "webgl.", "gfx.", "layers.", "fission.",
                 "browser.safebrowsing.", "general.config.", "remote.", "marionette.")
HTML = b'''<!doctype html><html lang="en"><meta charset="utf-8">
<title>Stock Firefox WebGL probe</title><link rel="stylesheet" href="style.css">
<h1>WebGL triangle probe</h1><p>Headed browser / fresh profile / no graphics overrides</p>
<div class="row"><section><h2>WebGL2</h2><canvas id="webgl2" width="256" height="256"></canvas></section>
<section><h2>WebGL1</h2><canvas id="webgl" width="256" height="256"></canvas></section></div>
<pre id="status">Running actual shader draw and framebuffer readback...</pre>
<script src="probe.js" defer></script></html>'''
CSS = b'body{background:#fff;color:#111;font:16px sans-serif;margin:24px}.row{display:flex;gap:24px}h1{font-size:24px}h2{font-size:18px}canvas{display:block;width:256px;height:256px}pre{white-space:pre-wrap;max-width:700px;font-size:12px}'
JS = r'''"use strict";
(async () => {
  const report = {schema:1, userAgent:navigator.userAgent, webdriver:navigator.webdriver,
    devicePixelRatio, results:[], errors:[]};
  addEventListener('error', e => report.errors.push(String(e.message)));
  addEventListener('unhandledrejection', e => report.errors.push(String(e.reason)));
  for (const kind of ['webgl2','webgl']) {
    const canvas = document.getElementById(kind);
    const r = {kind, status:'unavailable', creationErrors:[], contextLost:false};
    report.results.push(r);
    canvas.addEventListener('webglcontextcreationerror', e => r.creationErrors.push(e.statusMessage));
    canvas.addEventListener('webglcontextlost', () => {r.contextLost=true;r.status='context-lost';});
    try {
      const gl = canvas.getContext(kind, {alpha:false, antialias:false, preserveDrawingBuffer:true});
      if (!gl) continue;
      r.version = gl.getParameter(gl.VERSION);
      r.renderer = gl.getParameter(gl.RENDERER);
      r.vendor = gl.getParameter(gl.VENDOR);
      r.attributes = gl.getContextAttributes();
      const debug = gl.getExtension('WEBGL_debug_renderer_info');
      if (debug) {
        r.unmaskedRenderer = gl.getParameter(debug.UNMASKED_RENDERER_WEBGL);
        r.unmaskedVendor = gl.getParameter(debug.UNMASKED_VENDOR_WEBGL);
      }
      const modern = kind === 'webgl2';
      const vertex = modern ? '#version 300 es\nin vec2 p;void main(){gl_Position=vec4(p,0.,1.);}' : 'attribute vec2 p;void main(){gl_Position=vec4(p,0.,1.);}';
      const color = modern ? 'vec4(0.1,0.8,0.3,1.)' : 'vec4(0.8,0.2,0.7,1.)';
      const fragment = modern ? '#version 300 es\nprecision highp float;out vec4 c;void main(){c='+color+';}' : 'precision highp float;void main(){gl_FragColor='+color+';}';
      const compile = (type, source) => {
        const shader = gl.createShader(type); gl.shaderSource(shader,source); gl.compileShader(shader);
        if (!gl.getShaderParameter(shader,gl.COMPILE_STATUS)) throw Error(gl.getShaderInfoLog(shader));
        return shader;
      };
      const program = gl.createProgram();
      gl.attachShader(program,compile(gl.VERTEX_SHADER,vertex));
      gl.attachShader(program,compile(gl.FRAGMENT_SHADER,fragment)); gl.linkProgram(program);
      if (!gl.getProgramParameter(program,gl.LINK_STATUS)) throw Error(gl.getProgramInfoLog(program));
      gl.useProgram(program); gl.bindBuffer(gl.ARRAY_BUFFER,gl.createBuffer());
      gl.bufferData(gl.ARRAY_BUFFER,new Float32Array([-.8,-.8,.8,-.8,0,.8]),gl.STATIC_DRAW);
      const pos = gl.getAttribLocation(program,'p');gl.enableVertexAttribArray(pos);
      gl.vertexAttribPointer(pos,2,gl.FLOAT,false,0,0);gl.viewport(0,0,256,256);
      gl.disable(gl.DITHER);gl.clearColor(.05,.07,.12,1);gl.clear(gl.COLOR_BUFFER_BIT);
      gl.drawArrays(gl.TRIANGLES,0,3);gl.finish();
      const pixels = new Uint8Array(256*256*4);gl.readPixels(0,0,256,256,gl.RGBA,gl.UNSIGNED_BYTE,pixels);
      r.glError = gl.getError();r.contextLost = gl.isContextLost();
      r.targetRGB = modern ? [26,204,77] : [204,51,179];
      const matches = (i,target) => target.every((c,k)=>Math.abs(pixels[i+k]-c)<=2);
      r.trianglePixels=0;r.backgroundPixels=0;
      for (let i=0;i<pixels.length;i+=4) {
        if(matches(i,r.targetRGB)) r.trianglePixels++;
        if(matches(i,[13,18,31])) r.backgroundPixels++;
      }
      r.centerRGBA=Array.from(pixels.slice((128*256+128)*4,(128*256+128)*4+4));
      r.cornerRGBA=Array.from(pixels.slice(0,4));
      r.status = r.glError===gl.NO_ERROR && !r.contextLost && r.trianglePixels>18000 && r.trianglePixels<23000 && r.backgroundPixels>40000 ? 'passed' : 'pixel-check-failed';
      r.canvasPNG = canvas.toDataURL('image/png');
    } catch(e) {r.status='error';r.error=String(e.stack||e);}
  }
  document.getElementById('status').textContent = JSON.stringify({results:report.results.map(({canvasPNG,...r})=>r)},null,2);
  await new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)));
  await fetch('report', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(report)});
})().catch(e=>{document.getElementById('status').textContent=String(e.stack||e);});
'''.encode()


def dump(name, value):
    OUT.mkdir(exist_ok=True)
    (OUT / name).write_text(json.dumps(value, indent=2) + "\n")


def command(args, timeout=10):
    p = subprocess.run(args, text=True, capture_output=True, timeout=timeout, check=False)
    return {"argv": args, "exit": p.returncode, "stdout": p.stdout, "stderr": p.stderr}


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def xwd_to_png(data, target):
    """Convert Xvfb's documented XWD snapshot; reject unsupported layouts."""
    if len(data) < 100:
        raise ValueError('Truncated XWD header')
    h = struct.unpack('>25I', data[:100])
    header, version, fmt, depth, width, height, offset, order = h[:8]
    bpp, stride, visual, red, green, blue, ncolors = h[11],h[12],h[13],h[14],h[15],h[16],h[19]
    if not (version==7 and fmt==2 and depth==24 and offset==0 and bpp==32 and visual==4 and order in (0,1)):
        raise ValueError(f'Unsupported XWD layout: {h}')
    if not (100<=header<=4096 and 1<=width<=4096 and 1<=height<=4096 and width*4<=stride<=32768 and ncolors<=65536):
        raise ValueError('Invalid XWD bounds')
    start = header+ncolors*12
    if len(data)<start+stride*height or (red,green,blue)!=(0xff0000,0xff00,0xff):
        raise ValueError('Truncated XWD or unsupported RGB masks')
    raw=bytearray();counts={"webgl2":0,"webgl":0}
    targets={"webgl2":(26,204,77),"webgl":(204,51,179)}
    for y in range(height):
        raw.append(0)
        for x in range(width):
            i=start+y*stride+x*4
            p=int.from_bytes(data[i:i+4], 'little' if order==0 else 'big')
            rgb=((p>>16)&255,(p>>8)&255,p&255)
            raw.extend(rgb)
            for kind,color in targets.items():
                if all(abs(a-b)<=3 for a,b in zip(rgb,color)):
                    counts[kind]+=1
    def chunk(kind,payload):
        return struct.pack('>I',len(payload))+kind+payload+struct.pack('>I',zlib.crc32(kind+payload)&0xffffffff)
    png=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>2I5B',width,height,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(raw))+chunk(b'IEND',b'')
    Path(target).write_bytes(png)
    return {"width":width,"height":height,"triangleColorPixels":counts,"sha256":hashlib.sha256(png).hexdigest()}


def provenance(firefox):
    evidence={"uid":os.geteuid(),"imageOS":os.environ.get('ImageOS'),"imageVersion":os.environ.get('ImageVersion'),
              "githubSHA":os.environ.get('GITHUB_SHA'),"firefoxPath":str(firefox),
              "firefoxVersion":command([str(firefox),'--version']),
              "packages":command(['dpkg-query','-W','-f=${Package}\t${Version}\n','firefox','xvfb','xauth','libgl1-mesa-dri','libegl-mesa0']),
              "firefoxPackageIntegrity":command(['dpkg','-V','firefox'], timeout=60),"files":{},"preferenceOverrides":{}}
    for name in ('firefox','firefox-bin','libxul.so','omni.ja','browser/omni.ja','application.ini','platform.ini'):
        path=firefox.parent/name
        if path.is_file(): evidence['files'][name]={"bytes":path.stat().st_size,"sha256":sha(path)}
    policies=[Path('/etc/firefox/policies/policies.json'),Path('/etc/firefox/policies.json'),firefox.parent/'distribution/policies.json',firefox.parent/'browser/distribution/policies.json']
    evidence['policyFilesPresent']=[str(p) for p in policies if p.exists()]
    candidates=list((firefox.parent/'defaults/pref').glob('*.js'))+list((firefox.parent/'browser/defaults/preferences').glob('*.js'))
    candidates+=list(Path('/etc/firefox').rglob('*.js')) if Path('/etc/firefox').exists() else []
    suspicious=[]
    for p in candidates:
        content=p.read_text(errors='replace')
        lines=[line.strip() for line in content.splitlines() if not line.strip().startswith(('//','/*','*')) and any(key in line for key in SECURITY_KEYS)]
        evidence['preferenceOverrides'][str(p)]={"sha256":sha(p),"securityRelatedLines":lines}
        suspicious.extend(lines)
    evidence['securityRelatedOverrideDetected']=bool(suspicious)
    dump('provenance.json',evidence)
    if evidence['policyFilesPresent'] or suspicious:
        raise RuntimeError('Pre-existing policy/security preference override found; do not alter it. Review provenance.json.')
    return evidence


def inside_xvfb(firefox, work):
    profile=work/'profile';profile.mkdir()
    home=work/'home';home.mkdir()
    received=threading.Event();report_box={};nonce=secrets.token_hex(12)
    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self,*args): pass
        def do_GET(self):
            payload={'/':(HTML,'text/html'),'/probe.js':(JS,'text/javascript'),'/style.css':(CSS,'text/css')}
            key=self.path.removeprefix('/'+nonce)
            if not self.path.startswith('/'+nonce+'/') or key not in payload:
                self.send_error(404);return
            body,mime=payload[key];self.send_response(200)
            self.send_header('Content-Type',mime+'; charset=utf-8')
            self.send_header('Content-Length',str(len(body)))
            self.send_header('Content-Security-Policy',"default-src 'none'; script-src 'self'; style-src 'self'; connect-src 'self'; base-uri 'none'; frame-ancestors 'none'; form-action 'none'")
            self.end_headers();self.wfile.write(body)
        def do_POST(self):
            origin=f'http://127.0.0.1:{self.server.server_port}'
            if self.path!='/'+nonce+'/report' or self.headers.get('Origin')!=origin or self.headers.get('Content-Type')!='application/json':
                self.send_error(403);return
            length=int(self.headers.get('Content-Length','0'))
            if not 0<length<262144 or received.is_set():self.send_error(413);return
            try: report=json.loads(self.rfile.read(length))
            except (ValueError,UnicodeError):self.send_error(400);return
            report_box['value']=report;self.send_response(204);self.end_headers();received.set()
    server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    url=f'http://127.0.0.1:{server.server_port}/{nonce}/'
    # A narrow environment excludes CI credentials and inherited browser/GL overrides.
    env={k:os.environ[k] for k in ('PATH','USER','LOGNAME','LANG','DISPLAY','XAUTHORITY') if k in os.environ}
    env.update(HOME=str(home),XDG_CONFIG_HOME=str(work/'config'),XDG_CACHE_HOME=str(work/'cache'),XDG_DATA_HOME=str(work/'data'))
    argv=[str(firefox),'--no-remote','--profile',str(profile),'--new-window',url]
    dump('launch.json',{"argv":argv,"environmentKeys":sorted(env),"profileInitiallyEmpty":not list(profile.iterdir()),
                        "customPreferenceFilesWritten":False,"headless":False,"automationFramework":None})
    outcome={"status":"inconclusive","reason":"No report yet","interactionQA":False,"glbQA":False}
    browser=None
    try:
        with (OUT/'firefox.log').open('wb') as log:
            browser=subprocess.Popen(argv,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
            deadline=time.monotonic()+90
            while not received.wait(.25):
                if browser.poll() is not None: raise RuntimeError(f'Firefox exited {browser.returncode} before report')
                if time.monotonic()>deadline: raise RuntimeError('No browser report in 90 seconds (possible first-run UI or unavailable display)')
            report=report_box['value']
            if report.get('schema')!=1 or report.get('webdriver') is not False or len(report.get('results',[]))!=2:
                raise RuntimeError('Malformed report or unexpected WebDriver-enabled browser')
            for r in report['results']:
                image=r.pop('canvasPNG',None)
                if image:
                    if r['kind'] not in ('webgl2','webgl') or not image.startswith('data:image/png;base64,'):raise RuntimeError('Invalid canvas image')
                    (OUT/(r['kind']+'-canvas.png')).write_bytes(base64.b64decode(image.split(',',1)[1],validate=True))
            dump('webgl-report.json',report)
            # Two rAFs occur before POST; allow compositor to present, without UI automation.
            time.sleep(1)
            capture=(work/'framebuffer/Xvfb_screen0').read_bytes()
            (OUT/'display.xwd').write_bytes(capture)
            screen=xwd_to_png(capture,OUT/'display.png');dump('screenshot-pixels.json',screen)
            modern=next(r for r in report['results'] if r['kind']=='webgl2')
            if modern['status']=='unavailable':outcome.update(status='unsupported',reason='WebGL2 context unavailable; no fallback flags or preferences attempted')
            elif modern['status']!='passed' or report['errors']:outcome.update(status='failed',reason='WebGL2 draw/readback or page error')
            elif screen['triangleColorPixels']['webgl2']<10000:outcome.update(status='inconclusive',reason='Readback passed but triangle not visible in display screenshot (possibly first-run UI)')
            else:outcome.update(status='passed',reason='WebGL2 shader draw, readPixels, canvas PNG and Xvfb displayed triangle confirmed')
    except Exception as exc:
        outcome.update(status='inconclusive',reason=str(exc))
        raise
    finally:
        if browser and browser.poll() is None:
            os.killpg(browser.pid,signal.SIGTERM)
            try:browser.wait(timeout=10)
            except subprocess.TimeoutExpired:os.killpg(browser.pid,signal.SIGKILL);browser.wait(timeout=5)
        server.shutdown();server.server_close()
        # Read only this newly created profile. Never upload it, credentials, or all prefs.
        selected=[]
        prefs=profile/'prefs.js'
        if prefs.exists():
            selected=[line for line in prefs.read_text(errors='replace').splitlines() if any('"'+key in line for key in SECURITY_KEYS)]
        dump('profile-provenance.json',{"userJSExists":(profile/'user.js').exists(),"selectedGeneratedPreferenceLines":selected,
                                       "note":"Read-only post-run evidence; generated prefs are not a full effective-default or sandbox audit."})
        log=(OUT/'firefox.log').read_text(errors='replace') if (OUT/'firefox.log').exists() else ''
        warnings=[line for line in log.splitlines() if 'sandbox' in line.lower() and any(w in line.lower() for w in ('fail','disabled','not supported'))]
        if warnings:outcome.update(status='inconclusive',reason='Sandbox warning requires review; no weakening attempted',sandboxWarnings=warnings)
        dump('outcome.json',outcome)
    return 0 if outcome['status']=='passed' else 2


def main():
    OUT.mkdir(exist_ok=True)
    if os.geteuid()==0: raise RuntimeError('Refusing root browser')
    # Never run on the assistant cloud browser or a desktop: separate authorized CI only.
    if os.environ.get('GITHUB_ACTIONS')!='true':raise RuntimeError('This probe may run only in its reviewed GitHub Actions job')
    if len(sys.argv)==4 and sys.argv[1]=='--inside-xvfb':
        return inside_xvfb(Path(sys.argv[2]),Path(sys.argv[3]))
    for binary in ('firefox','Xvfb','xvfb-run','xauth','dpkg-query'):
        if not shutil.which(binary):raise RuntimeError(f'Missing preinstalled dependency: {binary}; no installation attempted')
    firefox=Path('/usr/lib/firefox/firefox')
    if not firefox.is_file():raise RuntimeError('Expected runner Firefox package binary missing; review provenance instead of downloading')
    provenance(firefox)
    with tempfile.TemporaryDirectory(prefix='webgl-probe-') as temporary:
        work=Path(temporary);(work/'framebuffer').mkdir()
        args=['xvfb-run','--auto-servernum','--server-args',f'-screen 0 1280x1024x24 -nolisten tcp -fbdir {work}/framebuffer',
              sys.executable,str(Path(__file__).resolve()),'--inside-xvfb',str(firefox),str(work)]
        with (OUT/'xvfb.log').open('wb') as log:
            p=subprocess.run(args,stdout=log,stderr=subprocess.STDOUT,timeout=150,check=False)
        return p.returncode


if __name__=='__main__':
    try:sys.exit(main())
    except Exception as exc:
        dump('harness-error.json',{"status":"inconclusive","error":str(exc),"noSecurityFallbackAttempted":True})
        print(f'Probe stopped safely: {exc}',file=sys.stderr);sys.exit(2)
