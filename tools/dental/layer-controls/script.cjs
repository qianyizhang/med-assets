/* Offline script creation/validation against exact source bytes. No downloads. */
const fs=require('node:fs'),vm=require('node:vm'),crypto=require('node:crypto');
const C=require('./controller.js'),factory=require('./authoring.js');
const context={TextDecoder,Uint8Array,Float32Array,Uint32Array,DataView};
vm.createContext(context);vm.runInContext(fs.readFileSync(__dirname+'/renderer.js','utf8'),context);
const A=factory(C,context.fixedEnvelopeCamera);
const [mode,source,file]=process.argv.slice(2);
if(!['create','check'].includes(mode)||!source||!file) throw Error('Usage: node script.cjs create|check SOURCE.glb SCRIPT.json');
const bytes=fs.readFileSync(source);
if(bytes.length!==A.SOURCE.bytes||crypto.createHash('sha256').update(bytes).digest('hex')!==A.SOURCE.sha256) throw Error('Exact hydrated FDI31 source required.');
const parts=context.parseGLB(bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.byteLength)).map(p=>({...p,label:p.name.split('/').pop()}));
if(mode==='create') {
 const controller=A.fresh(parts,()=>0);controller.setTimeline(A.SHOT);
 fs.writeFileSync(file,A.serialize(controller,parts,630,440),{flag:'wx'});
} else A.load(fs.readFileSync(file,'utf8'),parts,()=>0);
console.log(mode==='create'?'Created source-bound script.':'Script validated; reopening is paused.');
