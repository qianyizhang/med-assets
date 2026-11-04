/* Source-preserving GLB parser and Canvas2D rasterizer, reused from the private specimen explorer. */
const I=[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1];
const mul=(a,b)=>{const c=new Array(16).fill(0);for(let r=0;r<4;r++)for(let k=0;k<4;k++)for(let q=0;q<4;q++)c[k*4+r]+=a[q*4+r]*b[k*4+q];return c};
const trs=n=>{if(n.matrix)return n.matrix;let [x,y,z,w]=n.rotation||[0,0,0,1],[a,b,c]=n.scale||[1,1,1],[tx,ty,tz]=n.translation||[0,0,0];return [(1-2*y*y-2*z*z)*a,(2*x*y+2*z*w)*a,(2*x*z-2*y*w)*a,0,(2*x*y-2*z*w)*b,(1-2*x*x-2*z*z)*b,(2*y*z+2*x*w)*b,0,(2*x*z+2*y*w)*c,(2*y*z-2*x*w)*c,(1-2*x*x-2*y*y)*c,0,tx,ty,tz,1]};
const transform=(p,m)=>{let o=new Float32Array(p.length);for(let i=0;i<p.length;i+=3){let x=p[i],y=p[i+1],z=p[i+2];o[i]=m[0]*x+m[4]*y+m[8]*z+m[12];o[i+1]=m[1]*x+m[5]*y+m[9]*z+m[13];o[i+2]=m[2]*x+m[6]*y+m[10]*z+m[14]}return o};
function parseGLB(buf){let v=new DataView(buf);if(v.getUint32(0,true)!==0x46546c67)throw Error('Invalid GLB');let o=12,j,bin;while(o<buf.byteLength){let n=v.getUint32(o,true),t=v.getUint32(o+4,true);if(t===0x4e4f534a)j=JSON.parse(new TextDecoder().decode(new Uint8Array(buf,o+8,n)));if(t===0x004e4942)bin=o+8;o+=8+n}if(!j||!bin)throw Error('GLB data missing');
function acc(id){let a=j.accessors[id],bv=j.bufferViews[a.bufferView],ct=a.componentType,n={SCALAR:1,VEC2:2,VEC3:3,VEC4:4,MAT4:16}[a.type],size={5120:1,5121:1,5122:2,5123:2,5125:4,5126:4}[ct],read={5120:'getInt8',5121:'getUint8',5122:'getInt16',5123:'getUint16',5125:'getUint32',5126:'getFloat32'}[ct],p=bin+(bv.byteOffset||0)+(a.byteOffset||0),stride=bv.byteStride||n*size,out=ct===5126?new Float32Array(a.count*n):new Uint32Array(a.count*n);if(a.sparse)throw Error('Sparse accessor unsupported');for(let k=0;k<a.count;k++)for(let l=0;l<n;l++)out[k*n+l]=v[read](p+k*stride+l*size,true);return out}
let parts=[];function walk(id,parent){let n=j.nodes[id],world=mul(parent,trs(n));if(n.mesh!==undefined){let part={name:n.name||`Part ${id}`,extras:n.extras||{},primitives:[]};for(let p of j.meshes[n.mesh].primitives){if(p.mode!==undefined&&p.mode!==4)continue;let pos=transform(acc(p.attributes.POSITION),world),idx=p.indices===undefined?Uint32Array.from({length:pos.length/3},(_,i)=>i):acc(p.indices);part.primitives.push({pos,idx});}parts.push(part)}for(let c of n.children||[])walk(c,world)}for(let n of j.scenes[j.scene||0].nodes)walk(n,I);return parts}

function rasterize(scene,canvas,camera,dragging){
const ctx=canvas.getContext('2d');const {yaw,pitch,zoom,center,extent}=camera;const w=Math.round(canvas.clientWidth),h=Math.round(canvas.clientHeight);if(!w||!h)return;if(canvas.width!==w||canvas.height!==h){canvas.width=w;canvas.height=h}let image=ctx.createImageData(w,h),pixels=image.data,zbuf=new Float32Array(w*h).fill(-Infinity),overlay=new Uint8ClampedArray(w*h*4),oz=new Float32Array(w*h).fill(-Infinity);
const sc=.85*Math.min(w,h)/extent*zoom,cy=Math.cos(yaw),sy=Math.sin(yaw),cp=Math.cos(pitch),sp=Math.sin(pitch);let total=0;
for(const pr of scene){const pos=pr.pos,idx=pr.idx,proj=new Float32Array(pos.length),isOverlay=pr.alpha<1,target=isOverlay?overlay:pixels,depth=isOverlay?oz:zbuf;for(let i=0;i<pos.length;i+=3){let x=pos[i]-center[0],y=pos[i+1]-center[1],z=pos[i+2]-center[2],rx=x*cy+z*sy,rz=-x*sy+z*cy;proj[i]=w/2+rx*sc;proj[i+1]=h/2-(y*cp-rz*sp)*sc;proj[i+2]=(y*sp+rz*cp)*sc}let count=idx.length/3;total+=count;let step=dragging?Math.max(1,Math.ceil(count/35000)):1;for(let f=0;f<count;f+=step){let a=idx[f*3]*3,b=idx[f*3+1]*3,c=idx[f*3+2]*3;const x1=proj[a],y1=proj[a+1],z1=proj[a+2],x2=proj[b],y2=proj[b+1],z2=proj[b+2],x3=proj[c],y3=proj[c+1],z3=proj[c+2];const area=(y2-y3)*(x1-x3)+(x3-x2)*(y1-y3);if(Math.abs(area)<1e-10)continue;const minx=Math.max(0,Math.floor(Math.min(x1,x2,x3))),maxx=Math.min(w-1,Math.ceil(Math.max(x1,x2,x3))),miny=Math.max(0,Math.floor(Math.min(y1,y2,y3))),maxy=Math.min(h-1,Math.ceil(Math.max(y1,y2,y3)));if(maxx<minx||maxy<miny)continue;let nx=(y2-y1)*(z3-z1)-(z2-z1)*(y3-y1),ny=(z2-z1)*(x3-x1)-(x2-x1)*(z3-z1),nz=(x2-x1)*(y3-y1)-(y2-y1)*(x3-x1),norm=Math.hypot(nx,ny,nz)||1;let light=.48+.52*Math.abs((nx*-.3-ny*.45+nz*.84)/norm);const red=Math.round(pr.color[0]*light),green=Math.round(pr.color[1]*light),blue=Math.round(pr.color[2]*light),ia=1/area;for(let y=miny;y<=maxy;y++)for(let x=minx;x<=maxx;x++){let aa=((y2-y3)*(x+.5-x3)+(x3-x2)*(y+.5-y3))*ia,bb=((y3-y1)*(x+.5-x3)+(x1-x3)*(y+.5-y3))*ia,cc=1-aa-bb;if(aa<0||bb<0||cc<0)continue;let z=aa*z1+bb*z2+cc*z3,q=y*w+x;if(z>depth[q]){depth[q]=z;q*=4;target[q]=red;target[q+1]=green;target[q+2]=blue;target[q+3]=255}}}}
if(scene.some(p=>p.alpha<1))for(let i=0;i<pixels.length;i+=4)if(overlay[i+3]){if(pixels[i+3]){pixels[i]=pixels[i]*.65+overlay[i]*.35;pixels[i+1]=pixels[i+1]*.65+overlay[i+1]*.35;pixels[i+2]=pixels[i+2]*.65+overlay[i+2]*.35}else{pixels[i]=overlay[i];pixels[i+1]=overlay[i+1];pixels[i+2]=overlay[i+2];pixels[i+3]=110}}
ctx.putImageData(image,0,0);return total;}

function fixedEnvelopeCamera(parts,w,h,offsets) {
    if(!Number.isFinite(w)||!Number.isFinite(h)||w<=0||h<=0) throw new Error("Invalid viewport dimensions.");
    const camera={yaw:.35,pitch:1.15,zoom:1,center:[0,0,0],extent:1};
    // Fit the union of source and fully separated positions, then keep camera fixed for controls.
    const pts=[];
    for(const part of parts)for(const primitive of part.primitives)for(let i=0;i<primitive.pos.length;i+=3) {
      const p=Array.from(primitive.pos.slice(i,i+3)),off=offsets[part.label];
      pts.push(p,p.map((v,k)=>v+off[k]));
    }
    const lo=[Infinity,Infinity,Infinity],hi=[-Infinity,-Infinity,-Infinity];
    for(const p of pts)for(let k=0;k<3;k++){lo[k]=Math.min(lo[k],p[k]);hi[k]=Math.max(hi[k],p[k]);}
    camera.center=lo.map((v,k)=>(v+hi[k])/2);
    let xmin=Infinity,xmax=-Infinity,ymin=Infinity,ymax=-Infinity;
    const cy=Math.cos(camera.yaw),sy=Math.sin(camera.yaw),cp=Math.cos(camera.pitch),sp=Math.sin(camera.pitch);
    for(const p of pts){const [x,y,z]=p.map((v,k)=>v-camera.center[k]);const rx=x*cy+z*sy,rz=-x*sy+z*cy,ry=y*cp-rz*sp;xmin=Math.min(xmin,rx);xmax=Math.max(xmax,rx);ymin=Math.min(ymin,ry);ymax=Math.max(ymax,ry);}
    const min=Math.min(w,h);
    camera.extent=Math.max((xmax-xmin)*min/w,(ymax-ymin)*min/h)*1.03;

    return camera;
}
