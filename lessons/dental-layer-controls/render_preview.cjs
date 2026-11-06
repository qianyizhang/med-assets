const fs=require('node:fs'),vm=require('node:vm'),path=require('node:path'),crypto=require('node:crypto'),assert=require('node:assert/strict');
const sha=data=>crypto.createHash('sha256').update(data).digest('hex');
const C=require('./controller.js');
const D=__dirname,out=path.join(D,'output');fs.mkdirSync(out,{recursive:true});
const bytes=fs.readFileSync(process.argv[2]);assert.equal(sha(bytes),'90006e54c2b9f79f6c201397a50f92228d9ad6fa4450f20e0ad20c5fe70c19f7');const ctx={TextDecoder,Uint8Array,Float32Array,Uint32Array,Uint8ClampedArray,DataView};vm.createContext(ctx);vm.runInContext(fs.readFileSync(path.join(D,'renderer.js'),'utf8')+';this.parse=parseGLB;this.tx=transform;this.raster=rasterize;this.fit=fixedEnvelopeCamera;',ctx);
const parts=ctx.parse(bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.byteLength)).map(p=>({...p,label:p.name.split('/').pop()}));
const controller=C.createController(parts.map(p=>({label:p.label,matrix:C.IDENTITY})));
const colours={enamel:[224,223,201],dentin:[211,168,80],pulp:[222,82,126],bone:[115,145,148]};
const w=630,h=440,camera=ctx.fit(parts,w,h,C.OFFSETS),records=[];
let pixels;const canvas={width:w,height:h,clientWidth:w,clientHeight:h,getContext:()=>({createImageData:(w,h)=>({data:new Uint8ClampedArray(w*h*4)}),putImageData:image=>pixels=image.data})};
const actions=[{name:'source',reveal:0,hold:1000}];
for(let i=1;i<=12;i++)actions.push({name:'reveal-'+i,reveal:i/12,hold:80});
actions.push({name:'separated',reveal:1,hold:1500});
for(const label of C.LABELS)actions.push({name:label,reveal:1,isolate:label,hold:1500});
actions.push({name:'all',reveal:1,hold:800},{name:'reset',reveal:0,hold:1500});
for(let i=0;i<actions.length;i++){
 const a=actions[i];
 if(a.name==='source'||a.name==='reset')controller.dispatch({type:'reset'});
 else if(a.name==='all')controller.dispatch({type:'all'});
 else if(a.isolate)controller.dispatch({type:'isolate',label:a.isolate});
 else controller.dispatch({type:'reveal',value:a.reveal});
 const r=new Map(controller.resolve().map(p=>[p.label,p]));const scene=parts.flatMap(p=>r.get(p.label).visible?p.primitives.map(pr=>({pos:ctx.tx(pr.pos,r.get(p.label).matrix),idx:pr.idx,color:colours[p.label],alpha:1})):[]);
 const count=ctx.raster(scene,canvas,camera,false);fs.writeFileSync(path.join(out,'pixels-'+i+'.rgba'),Buffer.from(pixels));records.push({...a,index:i,triangles:count,state:controller.snapshot(),width:w,height:h});
}
fs.writeFileSync(path.join(out,'preview-frames.json'),JSON.stringify({sourceSha256:sha(bytes),scripts:Object.fromEntries(['controller.js','renderer.js','render_preview.cjs'].map(f=>[f,sha(fs.readFileSync(path.join(D,f)))])),camera,records,resetPixelsExact:fs.readFileSync(path.join(out,'pixels-0.rgba')).equals(fs.readFileSync(path.join(out,'pixels-19.rgba')))},null,2));console.log('Rendered '+records.length+' exact controller states with full source triangles');
