import * as THREE from './.local/vendor/build/three.module.js';
import {breath, COPY} from './state.mjs';
export const CAMERAS={mechanics:{position:[.27,.17,.68],target:[0,.055,0],height:.37},airway:{position:[.075,.165,.33],target:[0,.123,-.014],height:.151}};
const v=p=>new THREE.Vector3(...p);
function material(color,opacity=1){return new THREE.MeshStandardMaterial({color,roughness:.85,metalness:0,transparent:opacity<1,opacity,side:THREE.DoubleSide,depthWrite:opacity>=1});}
function tube(points,radius,color,opacity=1){return new THREE.Mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(points.map(v)),36,radius,7,false),material(color,opacity));}
export function createLessonScene(models, manifest){
 const scene=new THREE.Scene();scene.background=new THREE.Color('#152d35');
 scene.add(new THREE.HemisphereLight('#fff7ed','#718c94',2.3));const key=new THREE.DirectionalLight('#fff6e8',3.4);key.position.set(.4,.7,.8);scene.add(key);
 const lungs=new THREE.Group();scene.add(lungs);
 for(const id of ['lungLeft','lungRight']){const root=models[id].scene;root.traverse(o=>{if(o.isMesh){o.material=material(id==='lungLeft'?'#d79a8b':'#c58f85');o.name='Lung · '+o.name;}});lungs.add(root);}
 const airwayOpen=models.tracheaOpen.scene,airwayCutaway=models.tracheaCutaway.scene;scene.add(airwayOpen,airwayCutaway);
 for(const root of [airwayOpen,airwayCutaway])root.traverse(o=>{if(o.isMesh){const arr=Array.isArray(o.material)?o.material:[o.material];o.material=arr.map((m,i)=>material(m.name.includes('inner shell')?'#bd7b70':m.name.includes('cut face')?'#ead1ab':'#dfc8a4'));if(o.material.length===1)o.material=o.material[0];}});
 const diaphragm=new THREE.Mesh(new THREE.PlaneGeometry(.36,.18,40,24),material('#61b6b6',.8));diaphragm.name='Authored diaphragm guide';scene.add(diaphragm);
 const ribs=new THREE.Group();ribs.name='Authored rib guides';scene.add(ribs);
 for(let i=0;i<5;i++){const y=-.035+i*.04;const pts=[];for(let k=0;k<=24;k++){const x=-.17+k*.34/24;pts.push([x,y+.013*(1-(x/.17)**2),-.10-.023*(1-(x/.17)**2)]);}ribs.add(tube(pts,.0012,'#88a2a5',.45));}
 const routes=Object.values(manifest.route).map(points=>new THREE.CatmullRomCurve3(points.map(v)));
 const particles=new THREE.Group();particles.name='Authored airflow markers';scene.add(particles);
 for(let path=0;path<3;path++)for(let n=0;n<5;n++){const dot=new THREE.Mesh(new THREE.SphereGeometry(.0017,10,8),material('#75e3dc'));dot.userData={path,n};particles.add(dot);}
 const ports=new THREE.Group();ports.name='Editorial airway ports';scene.add(ports);
 for(const [name,p] of Object.entries(manifest.ports)){const o=new THREE.Mesh(new THREE.SphereGeometry(.0021,12,8),material('#f3cb82'));o.position.copy(v(p.position));o.name='Port · '+name;ports.add(o);}
 return {scene,lungs,airwayOpen,airwayCutaway,diaphragm,ribs,routes,particles,ports,manifest};
}
export function applyLessonState(view,state){
 const b=breath(state),route=state.stage===1;
 view.lungs.traverse(o=>{if(!o.isMesh)return;if(o.morphTargetInfluences)o.morphTargetInfluences.fill(b.amplitude);o.material.opacity=route?.12:1;o.material.transparent=route;o.material.depthWrite=!route;});
 view.airwayOpen.visible=!route;view.airwayCutaway.visible=route;view.ribs.visible=!route;view.diaphragm.visible=!route;view.ports.visible=route;
 const a=view.diaphragm.geometry.attributes.position;
 for(let i=0;i<a.count;i++){const x=a.getX(i),z=-.09+Math.floor(i/41)*.18/24;const dx=(Math.abs(x)-.085)/.087;const dome=Math.max(0,1-dx*dx)*Math.max(0,1-(z/.10)**2);a.setXYZ(i,x,-.091+.045*dome*(1-.4*b.amplitude)-b.diaphragmDrop,z);}
 a.needsUpdate=true;view.diaphragm.geometry.computeVertexNormals();view.ribs.scale.x=1+.045*b.amplitude;view.ribs.position.y=.004*b.amplitude;
 view.particles.visible=Math.abs(b.phaseFlow)>.04;
 for(const dot of view.particles.children){let p=(state.breathClock*.35+dot.userData.n/5)%1;if(b.phaseFlow<0)p=1-p;dot.position.copy(view.routes[dot.userData.path].getPoint(p));}
 view.scene.updateMatrixWorld(true);return b;
}
export function sceneLabels(state,manifest){const c=COPY[state.language];return state.stage===1?Object.entries(manifest.ports).map(([id,p])=>({id,text:c[p.label],position:p.position})):[{id:'diaphragm',text:c.diaphragm,position:[.13,-.07-.018*breath(state).amplitude,.075]},{id:'ribs',text:c.ribs,position:[-.16,.10,-.10]}];}
