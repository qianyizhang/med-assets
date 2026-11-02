// Pure adapter/security contract. No independent model registry.
export function selectRecord(data,assetId,candidateId='baseline') {
 const asset=data.assets.find(x=>x.id===assetId);if(!asset)throw Error('Unknown asset ID');
 if(candidateId==='baseline'&&asset.hasBaseline===false)throw Error('Select a reviewed candidate for this new structure');
 if(candidateId==='baseline')return {asset,id:'baseline',source:asset.source,gates:asset.gates,evidenceIds:asset.evidenceIds||[],name:asset.name};
 const c=(data.candidates||[]).find(x=>x.id===candidateId&&x.assetId===assetId);if(!c)throw Error('Unknown candidate ID');
 if(c.reviewable!==true)throw Error('Candidate not released for review');
 return {...c,asset};
}
export function allowedModelURL(source,baseURL){
 if(!/^[a-f0-9]{64}$/.test(source?.sha256||''))throw Error('Missing source SHA256');
 const path=source.file;if(typeof path!=='string'||/[\\%?#]/.test(path))throw Error('Invalid model path');
 const url=new URL(path,baseURL),base=new URL(baseURL);
 if(url.origin!==base.origin||url.username||url.password||!['http:','https:'].includes(url.protocol))throw Error('Model must be same-origin');
 if(!['/body/3d/assets/','/review/candidates/','/models/'].some(prefix=>url.pathname.startsWith(prefix))||!(source.encoding==='gzip'?url.pathname.endsWith('.glb.gz'):url.pathname.endsWith('.glb')))throw Error('Model path outside allowlist');
 return url;
}
export function inspectGLB(buffer){
 const v=new DataView(buffer);if(buffer.byteLength<20||v.getUint32(0,true)!==0x46546c67||v.getUint32(4,true)!==2||v.getUint32(8,true)!==buffer.byteLength)throw Error('Invalid GLB 2 container');
 let json=null,p=12;
 while(p<buffer.byteLength){if(p+8>buffer.byteLength)throw Error('Invalid chunk');const len=v.getUint32(p,true),kind=v.getUint32(p+4,true);p+=8;if(len%4||p+len>buffer.byteLength)throw Error('Invalid chunk length');if(kind===0x4e4f534a){if(json)throw Error('Multiple JSON chunks');json=JSON.parse(new TextDecoder().decode(new Uint8Array(buffer,p,len)).trim())}p+=len;}
 if(!json||json.asset?.version!=='2.0')throw Error('Missing glTF 2 JSON');
 // Self-contained GLBs only. Reject all image/buffer URI fetches, including remote/data.
 for(const item of [...json.buffers||[],...json.images||[]])if(item.uri!==undefined)throw Error('External/data resource URI is not permitted; use embedded GLB buffers');
 return json;
}
export async function decodeTransport(buffer,source){
 const expected=source.bytes;if(expected!==undefined&&(!Number.isInteger(expected)||expected<20||expected>128*1024*1024))throw Error('Invalid declared model size');
 const view=new DataView(buffer);const isGLB=buffer.byteLength>=4&&view.getUint32(0,true)===0x46546c67;
 if(source.encoding!=='gzip'||isGLB){if(expected&&buffer.byteLength!==expected)throw Error('Source byte count mismatch');return {bytes:buffer,mode:source.encoding==='gzip'?'browser-decoded-gzip':'raw-glb'}}
 if(buffer.byteLength<2||view.getUint8(0)!==0x1f||view.getUint8(1)!==0x8b)throw Error('Invalid gzip transport');
 if(!globalThis.DecompressionStream)throw Error('Browser decompression unavailable; use static evidence');
 const limit=expected||128*1024*1024,reader=new Blob([buffer]).stream().pipeThrough(new DecompressionStream('gzip')).getReader(),chunks=[];let count=0;
 try{for(;;){const {value,done}=await reader.read();if(done)break;count+=value.byteLength;if(count>limit){await reader.cancel();throw Error('Decompressed model exceeds declared size')}chunks.push(value)}}finally{reader.releaseLock()}
 if(expected&&count!==expected)throw Error('Decompressed model size mismatch');const out=new Uint8Array(count);let at=0;for(const c of chunks){out.set(c,at);at+=c.byteLength}return {bytes:out.buffer,mode:'client-decoded-gzip'};
}

export function cameraSpec(record){
 const c=record.cameraContract;if(!c)return null;
 if(c.glb_sha256!==record.source.sha256)throw Error('Camera/source hash mismatch');
 const vector=v=>Array.isArray(v)&&v.length===3&&v.every(x=>Number.isFinite(x)&&Math.abs(x)<100000);
 if(!Number.isFinite(c.ortho_vertical_span)||c.ortho_vertical_span<=0||c.ortho_vertical_span>100)throw Error('Invalid camera span');
 if(c.sourceViews){const views={};for(const [i,v] of c.views.entries()){if((v.ortho_vertical_span!==undefined&&(!Number.isFinite(v.ortho_vertical_span)||v.ortho_vertical_span<=0||v.ortho_vertical_span>100))||i>2||!vector(v.position_three)||!vector(v.target_three)||!vector(v.up_three)||!(v.hidden_for_inspection_only||[]).every(n=>typeof n==='string'&&n.length<200))throw Error('Invalid source inspection view');views[['front','back','left'][i]]=v;}if(!Object.keys(views).length)throw Error('Missing source views');const initial=Object.keys(views).find(k=>views[k].file===c.primary_view)||'front';return {span:c.ortho_vertical_span,views,initial,sourceViews:true};}
 const views={};for(const [key,file] of Object.entries({front:'anterior.png',back:'posterior.png',left:'lateral.png'})){
  const v=c.views.find(x=>x.file===file);if(!v||!vector(v.position_three)||!vector(v.target_three)||!vector(v.up_three)||(v.hidden_for_inspection_only||[]).length)throw Error('Unsupported regional camera view');views[key]=v;
 }
 return {span:c.ortho_vertical_span,views};
}
