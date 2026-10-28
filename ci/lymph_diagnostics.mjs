// Bounded renderer diagnostics. No geometry is repaired or exported.
export const samples = [
 {id:'front', direction:[1,.5,2]},
 {id:'right', direction:[2,.5,-1]},
 {id:'reverse', direction:[-1,-.5,-2]},
 {id:'left', direction:[-2,.5,1]},
];
export const normalPolicy = {zeroEpsilon:1e-6, unitTolerance:1e-3};
const require = (test,message) => {if(!test)throw Error(message);};

// Count referenced vertices only. Face/normal disagreement is descriptive:
// smoothing, folded/open surfaces and inherited duplicates can cause it.
export function auditGeometry(geometry) {
 const p=geometry.attributes.position,n=geometry.attributes.normal,index=geometry.index;
 require(p && n && n.itemSize===3 && n.count===p.count,'Missing/mismatched loaded NORMAL');
 const count=index?index.count:p.count;
 require(count>0 && count%3===0,'Invalid triangle count');
 const vertex=i=>index?index.getX(i):i;
 const xyz=(a,i)=>[a.getX(i),a.getY(i),a.getZ(i)];
 const used=new Set();for(let i=0;i<count;i++) {
  const v=vertex(i);require(Number.isInteger(v)&&v>=0&&v<p.count,'Invalid triangle index');used.add(v);
 }
 const report={referencedVertices:used.size,nonfinite:0,zero:0,nonunit:0,
  minLength:null,maxLength:null,triangles:count/3,degenerateTriangles:0,opposedNormalCorners:0};
 for(const i of used) {
  const v=xyz(n,i);if(!v.every(Number.isFinite)){report.nonfinite++;continue;}
  const length=Math.hypot(...v);
  report.minLength=report.minLength===null?length:Math.min(report.minLength,length);
  report.maxLength=report.maxLength===null?length:Math.max(report.maxLength,length);
  if(length<=normalPolicy.zeroEpsilon)report.zero++;
  else if(Math.abs(length-1)>normalPolicy.unitTolerance)report.nonunit++;
 }
 for(let i=0;i<count;i+=3) {
  const ids=[vertex(i),vertex(i+1),vertex(i+2)],a=xyz(p,ids[0]),b=xyz(p,ids[1]),c=xyz(p,ids[2]);
  require([...a,...b,...c].every(Number.isFinite),'Nonfinite triangle');
  const u=b.map((x,k)=>x-a[k]),v=c.map((x,k)=>x-a[k]);
  const face=[u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]];
  const length=Math.hypot(...face);
  if(length===0){report.degenerateTriangles++;continue;}
  for(const id of ids) {
   const normal=xyz(n,id),dot=normal.reduce((sum,x,k)=>sum+x*face[k],0);
   if(Number.isFinite(dot) && dot < -1e-6*length*Math.hypot(...normal))report.opposedNormalCorners++;
  }
 }
 return report;
}
export function validNormals(report) {
 return report.referencedVertices>0 && report.nonfinite===0 && report.zero===0 && report.nonunit===0;
}

// Clone attributes, preserving the exact original objects for finally/restoration.
// These mutations alter data consumed by the real renderer, never RGB buffers.
export function mutateGeometry(geometry,kind) {
 if(kind==='negated-normals') {
  const original=geometry.getAttribute('normal'),mutated=original.clone();
  for(let i=0;i<mutated.count;i++)mutated.setXYZ(i,-original.getX(i),-original.getY(i),-original.getZ(i));
  geometry.setAttribute('normal',mutated);
  return ()=>geometry.setAttribute('normal',original);
 }
 require(kind==='reversed-winding','Unknown negative control');
 const original=geometry.getIndex();require(original && original.count%3===0,'Indexed triangles required for winding control');
 const mutated=original.clone();
 for(let i=0;i<mutated.count;i+=3){mutated.setX(i+1,original.getX(i+2));mutated.setX(i+2,original.getX(i+1));}
 geometry.setIndex(mutated);
 return ()=>geometry.setIndex(original);
}
