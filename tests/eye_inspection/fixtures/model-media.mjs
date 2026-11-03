import {allowedModelURL} from './candidate-contract.mjs';
// Generated together with the immutable map. No runtime host configuration.
export const MANIFEST_SHA256='06ca533a158274f23d71f95543b78df22c9234617b1b8950d5cbaa970621342c';
const ORIGIN='https://twciwvwencwa50yh.public.blob.vercel-storage.com';
const digest=async b=>[...new Uint8Array(await crypto.subtle.digest('SHA-256',b))].map(x=>x.toString(16).padStart(2,'0')).join('');
const hash=x=>typeof x==='string'&&/^[a-f0-9]{64}$/.test(x);
const size=x=>Number.isSafeInteger(x)&&x>=20&&x<=128*1024*1024;
export async function parseModelManifest(buffer){
 if(await digest(buffer)!==MANIFEST_SHA256)throw Error('Model manifest integrity mismatch');
 const m=JSON.parse(new TextDecoder().decode(buffer));if(m?.schema!==1||!m.objects||Array.isArray(m.objects))throw Error('Invalid model manifest');return m;
}
export function resolveModelTransport(source,baseURL,manifest){
 if(typeof source?.file==='string'&&/(^|\/)\.{1,2}(\/|$)/.test(source.file))throw Error('Noncanonical model path');
 const old=allowedModelURL(source,baseURL); // Never accept an arbitrary remote input URL.
 const e=manifest?.objects?.[old.pathname];
 if(!e||!hash(e.sha256)||!hash(e.transportSha256)||!size(e.bytes)||!size(e.transportBytes))throw Error('Model is not in trusted manifest');
 const gzip=source.encoding==='gzip';if(e.encoding!==(gzip?'gzip':'identity')||e.sha256!==source.sha256||(source.bytes!==undefined&&e.bytes!==source.bytes))throw Error('Model source/manifest mismatch');
 if(source.transportSha256!==undefined&&source.transportSha256!==e.transportSha256||source.transportBytes!==undefined&&source.transportBytes!==e.transportBytes)throw Error('Model transport/manifest mismatch');
 const expected=ORIGIN+'/sha256/'+e.transportSha256.slice(0,2)+'/'+e.transportSha256+(gzip?'.glb.gz':'.glb');
 if(e.url!==expected)throw Error('Invalid immutable model URL');
 if(!gzip&&(e.transportSha256!==e.sha256||e.transportBytes!==e.bytes))throw Error('Raw model identity mismatch');
 return {oldURL:old,url:new URL(expected),entry:e};
}
export async function verifyModelTransport(buffer,entry,contentEncoding=''){
 // Fetch decodes HTTP Content-Encoding before arrayBuffer(). A gzip file served
 // without HTTP encoding remains compressed; never inflate an already decoded GLB.
 const ce=contentEncoding.trim().toLowerCase();if(ce&&!['identity','gzip'].includes(ce))throw Error('Unsupported model content encoding');
 const isGLB=buffer.byteLength>=4&&new DataView(buffer).getUint32(0,true)===0x46546c67;
 const decodedByBrowser=entry.encoding==='gzip'&&ce==='gzip'&&isGLB;
 if(entry.encoding==='gzip'&&ce==='gzip'&&!isGLB)throw Error('HTTP gzip did not decode to GLB');
 const expectedBytes=decodedByBrowser?entry.bytes:entry.transportBytes,expectedHash=decodedByBrowser?entry.sha256:entry.transportSha256;
 if(buffer.byteLength!==expectedBytes)throw Error('Model transport byte count mismatch');
 if(await digest(buffer)!==expectedHash)throw Error('Model transport SHA256 mismatch');
 return {browserDecoded:decodedByBrowser,transportBytesVerified:!decodedByBrowser};
}
