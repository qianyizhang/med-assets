// A single source-bound inspection; generic camera rules remain unchanged.
export const ID='joints__z-knee-r01';
export const SHA='6dcc793e4132e62e4962e504bef0d595bb2e7d3a31881137244f31eadbb53aad';
export const HIDDEN=Object.freeze(['Articular capsule of knee joint.r','Infrapatellar fat pad.r','Femur.r','Patella.r']);
export const VIEW=Object.freeze({position_three:[-0.32581961154937744,1.1794161796569824,0.9643691182136536],target_three:[-0.07581962645053864,0.4294162392616272,-0.03563088923692703],up_three:[0,1,0]});
export function eligible(record){return record?.id===ID&&record.source?.sha256===SHA;}
export function inspectionView(record){
 if(!eligible(record))throw Error('Unsupported knee inspection source');
 const c=record.cameraContract,v=c?.views?.find(x=>x.file==='deep-oblique.png');
 if(c?.glb_sha256!==SHA||c.ortho_vertical_span!==0.25||!v||JSON.stringify(v.hidden_for_inspection_only)!==JSON.stringify(HIDDEN)||Object.keys(VIEW).some(k=>JSON.stringify(v[k])!==JSON.stringify(VIEW[k])))throw Error('Knee inspection camera mismatch');
 return v;
}
export function createKneeInspection(record,root,onChange=()=>{}){
 const view=inspectionView(record),all=[];root.traverse(o=>all.push(o));
 const originals=new Map(all.map(o=>[o,o.visible]));let active=false;
 function resolve(){return HIDDEN.map(name=>{const matches=all.filter(o=>o.userData?.source_object_name===name);if(matches.length!==1||!matches[0].isMesh)throw Error('Missing or ambiguous knee inspection binding: '+name);return matches[0];});}
 resolve(); // Validate the complete set before offering the control.
 function restore(){for(const [o,visible] of originals)o.visible=visible;active=false;onChange();}
 return {view,get active(){return active;},enter(){const targets=resolve();restore();for(const o of targets)o.visible=false;active=true;onChange();},restore};
}
export function inspectionText(lang,active){const zh=lang==='zh';return {
 button:zh?'深层审查（隐藏4个结构）':'Deep inspection (hide 4 structures)',
 reset:zh?'恢复外观 / 重置':'Restore exterior / Reset',
 note:active?(zh?'深层审查模式：隐藏右膝关节囊、髌下脂肪垫、股骨和髌骨，以观察来源中的交叉韧带与半月板。仅供教学审查；模型与下载文件未改变。':'Deep inspection: articular capsule, infrapatellar fat pad, femur and patella are hidden to inspect source cruciates and menisci. Educational inspection only; model and download remain unchanged.'):(zh?'外观模式：保留全部原始可见结构。深层审查可临时隐藏4个具名结构；可随时恢复。':'Exterior mode: all original visibility is preserved. Deep inspection can temporarily hide 4 named structures; restore at any time.')};}
