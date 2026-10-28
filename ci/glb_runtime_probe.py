#!/usr/bin/env python3
"""Bounded, normal-Firefox CI GLB probe. No browser preferences/install/security fallback."""
import base64, collections, hashlib, http.server, json, math, os
from pathlib import Path
import re, secrets, shutil, signal, struct, subprocess, sys, tempfile, threading, time
import urllib.parse, urllib.request, zlib
import webgl_probe as base
import lymph_diagnostics as diagnostics

HERE=Path(__file__).resolve().parent
RECIPE=HERE.parent/'tools/lymph_node/editorial_window_r03'
OUT=Path.cwd()/'glb-runtime-results'
HOSTS={'raw.githubusercontent.com','media.githubusercontent.com','heart-anatomy-imaging-lab.landy123007.chatgpt.site'}
MAX_DOWNLOAD=10*1024*1024
MAX_POST=4*1024*1024
FRAME_IDS=(['lymph-full','lymph-capsule-hidden','lymph-restored']+
 ['lymph-source-lit-reverse','lymph-candidate-lit-front','lymph-candidate-lit-reverse',
  'lymph-source-normal-front','lymph-source-normal-back','lymph-candidate-normal-front','lymph-candidate-normal-back']+diagnostics.ORBIT_IDS+diagnostics.CONTROL_IDS+
 [f'heart-full-{i}' for i in range(4)]+['heart-paused','heart-exact-loop']+
 [f'heart-valves-{i}' for i in range(4)]+['heart-restored'])

def dump(name,value):
 OUT.mkdir(exist_ok=True);(OUT/name).write_text(json.dumps(value,indent=2)+'\n')

def permitted_url(url):
 p=urllib.parse.urlsplit(url)
 if p.scheme!='https' or p.hostname not in HOSTS or p.username or p.password or p.port not in (None,443):
  raise ValueError('Download URL outside reviewed HTTPS public hosts')
 return url

class ScopedRedirect(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,req,fp,code,msg,headers,newurl):
  permitted_url(newurl)
  return super().redirect_request(req,fp,code,msg,headers,newurl)

def download_inputs(fixture,work):
 receipts=[];opener=urllib.request.build_opener(ScopedRedirect());deadline=time.monotonic()+120
 assert len(fixture['resources'])==7
 for item in fixture['resources']:
  expected=item['bytes'];assert 0<expected<=MAX_DOWNLOAD
  relative=Path(item['path']);assert not relative.is_absolute() and '..' not in relative.parts
  url=permitted_url(item['url']);started=time.monotonic()
  request=urllib.request.Request(url,headers={'User-Agent':'med-assets-scoped-runtime-probe','Accept-Encoding':'identity'})
  with opener.open(request,timeout=30) as response:
   assert response.status==200;permitted_url(response.url)
   content_length=response.headers.get('Content-Length')
   if content_length:assert int(content_length)==expected, 'Unexpected advertised byte count'
   chunks=[];total=0
   while True:
    if time.monotonic()-started>60 or time.monotonic()>deadline:raise TimeoutError('Bounded resource download deadline')
    chunk=response.read(min(65536,expected+1-total))
    if not chunk:break
    chunks.append(chunk);total+=len(chunk)
    if total>expected:raise ValueError('Download exceeds exact reviewed size')
   data=b''.join(chunks);digest=hashlib.sha256(data).hexdigest()
   assert len(data)==expected and digest==item['sha256'], 'Downloaded size/SHA-256 mismatch'
   path=work/relative;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
   receipts.append({**item,'actualBytes':len(data),'actualSHA256':digest,'resolvedURL':response.url,
    'contentType':response.headers.get('Content-Type'),'contentEncoding':response.headers.get('Content-Encoding'),'seconds':round(time.monotonic()-started,3)})
  dump('download-provenance.json',receipts)

def verify_generated(path, expected_bytes, expected_sha):
 # Explicitly bounded independently of the 10 MiB network limit.
 if not isinstance(expected_bytes,int) or not 0<expected_bytes<=16*1024*1024:
  raise ValueError('Generated size outside local bound')
 if not path.is_file() or path.stat().st_size != expected_bytes:
  raise ValueError('Generated size mismatch: '+path.name)
 digest=hashlib.sha256(path.read_bytes()).hexdigest()
 if digest != expected_sha:raise ValueError('Generated SHA-256 mismatch: '+path.name)
 return {'bytes':expected_bytes,'sha256':digest}

def reconstruct(fixture,work):
 spec=fixture['lymphCandidate']; source=work/'assets/lymph.glb'
 intermediate=work/'r03'; compact=work/'compact'
 for script,args in [('build.py',['--source',str(source),'--output',str(intermediate)]),
                     ('display_repair.py',['--input',str(intermediate/'lymph-node-editorial-window-r03.glb'),'--output',str(compact)])]:
  if script=='display_repair.py':
   r03=verify_generated(intermediate/'lymph-node-editorial-window-r03.glb',spec['intermediateBytes'],spec['intermediateSha256'])
   source_map=verify_generated(intermediate/'triangle-source-map.json',spec['sourceMapBytes'],spec['sourceMapSha256'])
  subprocess.run([sys.executable,str(RECIPE/script),*args],check=True,timeout=120,stdout=subprocess.DEVNULL)
 # Receipts contain temporary paths; bound and hash them, but do not expose them.
 receipt_hashes={}
 for path in (intermediate/'build-receipt.json',compact/'build-receipt.json'):
  if not path.is_file() or not 0<path.stat().st_size<=128*1024:raise ValueError('Generated receipt exceeds bound')
  receipt_hashes[path.parent.name]=hashlib.sha256(path.read_bytes()).hexdigest()
 candidate=compact/'prepared-display-repair.glb'
 verified=verify_generated(candidate,spec['bytes'],spec['sha256'])
 target=work/spec['path'];target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(candidate,target)
 verify_generated(target,spec['bytes'],spec['sha256'])
 dump('reconstruction-provenance.json',{'sourceSha256':next(x['sha256'] for x in fixture['resources'] if x.get('id')=='lymph'),
  'intermediate':r03,'sourceMap':source_map,'candidate':verified,'localReceiptSHA256':receipt_hashes,
  'retainedComparisonSha256':spec['retainedComparisonSha256'],'note':spec['identityNote']})

def png(width,height,rgb):
 assert len(rgb)==width*height*3
 def chunk(k,p):return struct.pack('>I',len(p))+k+p+struct.pack('>I',zlib.crc32(k+p)&0xffffffff)
 rows=b''.join(b'\0'+rgb[y*width*3:(y+1)*width*3] for y in range(height))
 return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>2I5B',width,height,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(rows))+chunk(b'IEND',b'')

def decode_xwd(data):
 if len(data)<100:raise ValueError('Truncated XWD')
 h=struct.unpack('>25I',data[:100]);header,version,fmt,depth,width,height,offset,order=h[:8]
 bpp,stride,visual,red,green,blue,ncolors=h[11],h[12],h[13],h[14],h[15],h[16],h[19]
 if not(version==7 and fmt==2 and depth==24 and offset==0 and bpp==32 and visual==4 and order in (0,1)):
  raise ValueError('Unsupported XWD layout')
 if not(100<=header<=4096 and 1<=width<=4096 and 1<=height<=4096 and width*4<=stride<=32768 and ncolors<=65536):
  raise ValueError('Invalid XWD bounds')
 start=header+ncolors*12
 if len(data)<start+stride*height or (red,green,blue)!=(0xff0000,0xff00,0xff):raise ValueError('Invalid XWD pixels/masks')
 rgb=bytearray(width*height*3)
 for y in range(height):
  row=data[start+y*stride:start+y*stride+width*4];target=y*width*3
  rgb[target:target+width*3:3]=row[(2 if order==0 else 1)::4]
  rgb[target+1:target+width*3:3]=row[(1 if order==0 else 2)::4]
  rgb[target+2:target+width*3:3]=row[(0 if order==0 else 3)::4]
 return width,height,bytes(rgb)

def changed(a,b,tolerance=2):
 assert len(a)==len(b)
 return sum(any(abs(a[i+k]-b[i+k])>tolerance for k in range(3)) for i in range(0,len(a),4))

def verify_snapshot(row,fixture,work,previous,diagnostic_baseline=None):
 index=len(previous);assert index<len(FRAME_IDS) and row['id']==FRAME_IDS[index], 'Unexpected snapshot sequence'
 name=row['id']
 if name in diagnostics.NORMAL_IDS+diagnostics.CONTROL_IDS:
  diagnostics.require(diagnostic_baseline is not None,'Missing diagnostic baseline')
  diagnostics.validate_frame(row,diagnostic_baseline)
 assert row['width']==row['height']==512 and row['glError']==0 and row['contextLost'] is False
 resource=fixture['lymphCandidate'] if row['asset']=='lymphCandidate' else next(x for x in fixture['resources'] if x.get('id')==row['asset'])
 assert row['assetSHA256']==resource['sha256']
 visible=row['visibleNodes'];assert len(visible)==fixture[row['asset']]['meshes']
 visibility={x['node']:x['visible'] for x in visible};assert len(visibility)==len(visible)
 if row['asset'] in ('lymph','lymphCandidate'):
  assert {x['node']:x['name'] for x in visible}=={x['node']:x['name'] for x in fixture['lymph']['layers']}
  assert all(v is (not(name=='lymph-capsule-hidden' and i==2)) for i,v in visibility.items())
 else:
  assert set(visibility)==set(range(247))
  assert all(v is (i in fixture['heart']['valveNodes'] if name.startswith('heart-valves-') else True) for i,v in visibility.items())
 assert row['rendererInfo']['calls']>0 and row['rendererInfo']['triangles']>0
 raw=base64.b64decode(row.pop('rgbaBase64'),validate=True);assert len(raw)==512*512*4
 assert all(x==255 for x in raw[3::4]), 'Unexpected framebuffer alpha'
 assert hashlib.sha256(raw).hexdigest()==row['pixelSHA256']
 corner=raw[:4];presence=sum(any(abs(raw[i+k]-corner[k])>2 for k in range(3)) for i in range(0,len(raw),4))
 assert presence>500, 'Independent readback has no meaningful asset pixels'
 image=row.pop('canvasPNG');assert image.startswith('data:image/png;base64,')
 image=base64.b64decode(image.split(',',1)[1],validate=True)
 assert image[:8]==b'\x89PNG\r\n\x1a\n' and struct.unpack('>II',image[16:24])==(512,512)
 (OUT/(name+'.canvas.png')).write_bytes(image)
 compare=None;minimum=None;maximum=None
 if name=='lymph-capsule-hidden':compare='lymph-full';minimum=100
 elif name=='lymph-restored':compare='lymph-full';maximum=0
 elif name=='lymph-candidate-lit-front':compare='lymph-full';minimum=100
 elif name=='lymph-candidate-lit-reverse':compare='lymph-source-lit-reverse'
 elif name=='lymph-candidate-normal-front':compare='lymph-source-normal-front'
 elif name=='lymph-source-normal-back':compare='lymph-source-normal-front';minimum=100
 elif name=='lymph-candidate-normal-back':compare='lymph-candidate-normal-front';minimum=100
 elif name in ('heart-full-1','heart-full-2'):compare='heart-full-0';minimum=50
 elif name=='heart-full-3':compare='heart-full-0';maximum=10
 elif name=='heart-paused':compare='heart-full-1';maximum=0
 elif name in ('heart-exact-loop','heart-restored'):compare='heart-full-0';maximum=0
 elif name in ('heart-valves-1','heart-valves-2'):compare='heart-valves-0';minimum=20
 elif name=='heart-valves-3':compare='heart-valves-0';maximum=10
 if name in diagnostics.ORBIT_IDS:
  if name.endswith('-back'):compare=name.removesuffix('-back')+'-front'
  elif name.startswith('lymph-candidate-'):compare=name.replace('lymph-candidate-','lymph-source-',1)
 difference=diagnostics.control_difference(name,raw,previous,changed)
 if name in diagnostics.CONTROL_IDS:compare='lymph-candidate-normal-front'
 if compare:
  difference=changed(raw,previous[compare])
  if minimum is not None:assert difference>=minimum, 'Independent pixel change too small'
  if maximum is not None:assert difference<=maximum, 'Independent restore/loop/pause pixel mismatch'
 if row['asset']=='heart':
  phase=1 if name=='heart-paused' else int(name[-1]) if re.fullmatch(r'heart-(full|valves)-[0-3]',name) else 0
  expected={x['node']:x for x in fixture['heart']['tracks']};seen=collections.Counter()
  assert len(row['morphs'])==fixture['heart']['morphRenderMeshes']
  for actual in row['morphs']:
   spec=expected[actual['node']];assert actual['name']==spec['name']
   assert math.isfinite(actual['value']) and abs(actual['value']-spec['values'][phase])<1e-5
   seen[actual['node']]+=1
  assert set(seen)==set(expected) and all(v==expected[k]['renderPrimitives'] for k,v in seen.items())
 # Page is waiting for this same-origin response, keeping its rendered state stable.
 time.sleep(.25);xwd=(work/'framebuffer/Xvfb_screen0').read_bytes();w,h,rgb=decode_xwd(xwd)
 display=png(w,h,rgb);(OUT/(name+'.display.png')).write_bytes(display)
 rect=row['displayRect'];x,y=rect['x'],rect['y'];assert rect['width']==rect['height']==512
 assert isinstance(x,int) and isinstance(y,int) and 0<=x<=w-512 and 0<=y<=h-512, 'Canvas outside captured display'
 crop=b''.join(rgb[((y+dy)*w+x)*3:((y+dy)*w+x+512)*3] for dy in range(512))
 matched=0;maximumDifference=0
 for dy in range(512):
  for dx in range(512):
   a=((511-dy)*512+dx)*4;b=(dy*512+dx)*3
   delta=max(abs(raw[a+k]-crop[b+k]) for k in range(3));maximumDifference=max(maximumDifference,delta)
   if delta<=3:matched+=1
 fraction=matched/(512*512);(OUT/(name+'.display-crop.png')).write_bytes(png(512,512,crop))
 receipt={'id':name,'displayMatch':fraction>=.98,'displayMatchingFraction':fraction,'maxDisplayChannelDifference':maximumDifference,
  'displaySHA256':hashlib.sha256(display).hexdigest(),'xwdSHA256':hashlib.sha256(xwd).hexdigest(),
  'independentNonBackgroundPixels':presence,'independentChangedPixels':difference,'comparisonFrame':compare}
 dump(name+'.json',{**row,'capture':receipt})
 assert fraction>=.98, 'Display screenshot does not match actual GL readback'
 previous[name]=raw
 return receipt

def inside(firefox,work):
 fixture=json.loads((HERE/'glb-runtime-fixture.json').read_text());nonce=secrets.token_hex(12)
 profile=work/'profile';profile.mkdir();home=work/'home';home.mkdir()
 received=threading.Event();report={};previous={};receipts=[];server_errors=[];diagnostic_baseline={}
 importmap=json.dumps({'imports':{'three':'./vendor/build/three.module.js'}})
 html=f'''<!doctype html><html lang="en"><meta charset="utf-8"><title>Exact GLB runtime probe</title>
 <link rel="stylesheet" href="style.css"><h1>Exact-hash GLB runtime probe</h1>
 <p>Software CI rendering and deterministic scene API state — NOT native UI or clinical validation.</p>
 <h2 id="phase">Loading verified resources…</h2><div class="row"><canvas width="512" height="512"></canvas><pre id="status">Starting…</pre></div>
 <script type="importmap" nonce="{nonce}">{importmap}</script><script type="module" src="probe.mjs"></script></html>'''.encode()
 css=b'body{background:#fff;color:#111;font:16px sans-serif;margin:20px}h1{font-size:22px;margin:0}h2{font-size:17px;margin:12px 0}.row{display:flex;gap:20px}canvas{width:512px;height:512px;display:block}pre{font:13px monospace;white-space:pre-wrap;max-width:460px}'
 files={'/':(html,'text/html'),'/style.css':(css,'text/css'),'/probe.mjs':((HERE/'glb_runtime_probe.mjs').read_bytes(),'text/javascript'),
  '/fixture.json':((HERE/'glb-runtime-fixture.json').read_bytes(),'application/json'),
  '/lymph_diagnostics.mjs':((HERE/'lymph_diagnostics.mjs').read_bytes(),'text/javascript')}
 for item in fixture['resources']:
  files['/'+item['path']]=((work/item['path']).read_bytes(),'text/javascript' if item['path'].endswith('.js') else 'model/gltf-binary' if item['path'].endswith('.glb') else 'text/plain')
 candidate=fixture['lymphCandidate'];files['/'+candidate['path']]=((work/candidate['path']).read_bytes(),'model/gltf-binary')
 class Handler(http.server.BaseHTTPRequestHandler):
  def log_message(self,*args):pass
  def do_GET(self):
   key=self.path.removeprefix('/'+nonce)
   if not self.path.startswith('/'+nonce+'/') or key not in files:self.send_error(404);return
   data,mime=files[key];self.send_response(200);self.send_header('Content-Type',mime)
   self.send_header('Content-Length',str(len(data)));self.send_header('Cache-Control','no-store')
   self.send_header('Content-Security-Policy',f"default-src 'none'; script-src 'self' 'nonce-{nonce}'; style-src 'self'; connect-src 'self'; img-src 'self' blob:; base-uri 'none'; frame-ancestors 'none'; form-action 'none'")
   self.end_headers();self.wfile.write(data)
  def do_POST(self):
   origin=f'http://127.0.0.1:{self.server.server_port}';key=self.path.removeprefix('/'+nonce+'/')
   if not self.path.startswith('/'+nonce+'/') or key not in ('snapshot','complete') or self.headers.get('Origin')!=origin or self.headers.get('Content-Type')!='application/json':self.send_error(403);return
   length=int(self.headers.get('Content-Length','0'))
   if not 0<length<=MAX_POST or received.is_set():self.send_error(413);return
   try:
    value=json.loads(self.rfile.read(length))
    if key=='snapshot':
     if value['id']=='lymph-source-normal-front':diagnostic_baseline.update({key:value[key] for key in ('camera','culling')})
     result=verify_snapshot(value,fixture,work,previous,diagnostic_baseline or None);receipts.append(result)
    else:report['value']=value;dump('browser-report.json',value);received.set();result={'accepted':True}
    data=json.dumps(result).encode();self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
   except Exception as error:
    server_errors.append(str(error));dump('server-errors.json',server_errors);self.send_error(400,'Probe evidence check failed')
 server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler);threading.Thread(target=server.serve_forever,daemon=True).start()
 env={k:os.environ[k] for k in ('PATH','USER','LOGNAME','LANG','DISPLAY','XAUTHORITY') if k in os.environ}
 env.update(HOME=str(home),XDG_CONFIG_HOME=str(work/'config'),XDG_CACHE_HOME=str(work/'cache'),XDG_DATA_HOME=str(work/'data'))
 argv=[str(firefox),'--no-remote','--profile',str(profile),'--new-window',f'http://127.0.0.1:{server.server_port}/{nonce}/']
 dump('launch.json',{'argv':argv,'environmentKeys':sorted(env),'profileInitiallyEmpty':not list(profile.iterdir()),'customPreferenceFilesWritten':False,'headless':False,'automationFramework':None})
 browser=None;outcome={'status':'inconclusive','nativeUIInteractionQA':False,'wholeSiteQA':False,'clinicalQA':False,'hardwarePerformanceQA':False}
 try:
  with (OUT/'firefox.log').open('wb') as log:
   browser=subprocess.Popen(argv,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True);deadline=time.monotonic()+240
   while not received.wait(.25):
    if browser.poll() is not None:raise RuntimeError('Firefox exited before complete report')
    if time.monotonic()>deadline:raise TimeoutError('No complete browser report within 240 seconds')
   value=report['value'];dump('capture-receipts.json',receipts)
   assert value.get('schema')==1, 'Unexpected browser report schema'
   assert value.get('passed') is True, value.get('error','Browser reported failed')
   assert value.get('browser',{}).get('webdriver') is False, 'Unexpected WebDriver-enabled report'
   assert not value.get('errors') and not server_errors and all(c.get('passed') is True for c in value['checks'])
   assert list(previous)==FRAME_IDS and [r['id'] for r in receipts]==FRAME_IDS and len(value['frames'])==len(FRAME_IDS)
   assert all(r['displayMatch'] for r in receipts)
   normals=diagnostics.validate_normals(value,fixture)
   sheet,cells=diagnostics.contact_sheet(previous,png)
   (OUT/'lymph-diagnostics.svg').write_bytes(sheet)
   dump('lymph-diagnostics.json',{'status':'sampled-diagnostics-passed','normalPolicy':value['normalPolicy'],
    'samples':value['orbitSamples'],'normalDiagnostics':normals,'cells':cells,
    'contactSheetSHA256':hashlib.sha256(sheet).hexdigest(),
    'controls':[r for r in receipts if r['id'] in diagnostics.CONTROL_IDS],
    'scope':'Four fixed views; GL culling state and deliberate normal/winding mutations. Not all-view correctness or anatomical/vascular identity.',
    'attribution':diagnostics.ATTRIBUTION,
    'sourceComparison':'Source anomalies are retained observations. Matching source/candidate speckling alone establishes neither its cause nor normal/winding correctness.'})
   outcome.update(status='passed',reason='Exact-input render states, bounded normal/facing mutations, deterministic morph/layer state, framebuffer changes and visible display match verified',frameCount=len(receipts))
 except Exception as error:outcome.update(status='failed',reason=str(error))
 finally:
  if browser and browser.poll() is None:
   os.killpg(browser.pid,signal.SIGTERM)
   try:browser.wait(timeout=10)
   except subprocess.TimeoutExpired:os.killpg(browser.pid,signal.SIGKILL);browser.wait(timeout=5)
  server.shutdown();server.server_close()
  prefs=profile/'prefs.js';selected=[]
  if prefs.exists():selected=[line for line in prefs.read_text(errors='replace').splitlines() if any('"'+k in line for k in base.SECURITY_KEYS)]
  dump('profile-provenance.json',{'userJSExists':(profile/'user.js').exists(),'selectedGeneratedPreferenceLines':selected,'note':'Not a full effective-default/sandbox attestation. No profile uploaded.'})
  log=(OUT/'firefox.log').read_text(errors='replace') if (OUT/'firefox.log').exists() else ''
  warnings=[s for s in log.splitlines() if 'sandbox' in s.lower() and any(w in s.lower() for w in ('fail','disabled','not supported'))]
  if warnings:outcome.update(status='inconclusive',reason='Sandbox warning requires review; no weakening attempted',sandboxWarnings=warnings)
  dump('outcome.json',outcome)
 return 0 if outcome['status']=='passed' else 2

def main():
 OUT.mkdir(exist_ok=True);base.OUT=OUT
 if os.geteuid()==0:raise RuntimeError('Refusing root browser')
 if os.environ.get('GITHUB_ACTIONS')!='true':raise RuntimeError('Authorized GitHub Actions job only')
 if len(sys.argv)==4 and sys.argv[1]=='--inside-xvfb':return inside(Path(sys.argv[2]),Path(sys.argv[3]))
 for binary in ('firefox','Xvfb','xvfb-run','xauth','dpkg-query'):
  if not shutil.which(binary):raise RuntimeError(f'Missing preinstalled dependency {binary}; no installation attempted')
 firefox=Path('/usr/lib/firefox/firefox');assert firefox.is_file()
 provenance=base.provenance(firefox)
 actual=Path('/etc/firefox/syspref.js');content=actual.read_bytes();assert len(content)<=65536
 dump('runner-syspref.json',{'path':str(actual),'bytes':len(content),'sha256':hashlib.sha256(content).hexdigest(),'text':content.decode('utf-8'),'readOnly':True})
 integrity=provenance['firefoxPackageIntegrity'];assert integrity['exit']==0
 assert all(line.endswith(' c /etc/firefox/syspref.js') for line in integrity['stdout'].splitlines()), 'Unexpected packaged Firefox changes'
 fixture=json.loads((HERE/'glb-runtime-fixture.json').read_text())
 dump('test-provenance.json',{'githubSHA':os.environ.get('GITHUB_SHA'),'files':{p.name:{'sha256':base.sha(p),'bytes':p.stat().st_size} for p in [HERE/'webgl_probe.py',Path(__file__),HERE/'glb_runtime_probe.mjs',HERE/'lymph_diagnostics.mjs',HERE/'lymph_diagnostics.py',HERE/'glb-runtime-fixture.json',*[RECIPE/p for p in ('build.py','gltf_source.py','check.py','import_audit.py','display_repair.py')]]},'frameIDs':FRAME_IDS})
 with tempfile.TemporaryDirectory(prefix='glb-runtime-') as temporary:
  work=Path(temporary);(work/'framebuffer').mkdir();download_inputs(fixture,work);reconstruct(fixture,work)
  args=['xvfb-run','--auto-servernum','--server-args',f'-screen 0 1280x1024x24 -nolisten tcp -fbdir {work}/framebuffer',sys.executable,str(Path(__file__).resolve()),'--inside-xvfb',str(firefox),str(work)]
  with (OUT/'xvfb.log').open('wb') as log:return subprocess.run(args,stdout=log,stderr=subprocess.STDOUT,timeout=300,check=False).returncode

if __name__=='__main__':
 try:sys.exit(main())
 except Exception as error:
  dump('harness-error.json',{'status':'inconclusive','error':str(error),'noSecurityFallbackAttempted':True});print(f'Probe stopped safely: {error}',file=sys.stderr);sys.exit(2)
