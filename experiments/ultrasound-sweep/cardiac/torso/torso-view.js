import * as THREE from '../../vendor/build/three.module.js';
import {loadMesh} from '../../scene.js';
import {CARDIAC_VIEWS, probePlane} from '../heart-poses.js';
import {heartFrame} from '../heart-geometry.js';
import {bodyPoint, bodyDirection, heartAxes, heartOrigin} from './registration.js';

const vector = coordinates => new THREE.Vector3(...coordinates);
const radians = THREE.MathUtils.degToRad;
const material = (color, options = {}) => new THREE.MeshStandardMaterial({
  color, roughness: .64, ...options,
});
export const valveColors = { AV: '#ffc063', PV: '#c9dc9d' };
export const chamberColors = {LV: '#a2554b', RV: '#865057', LA: '#be7369', RA: '#8e6578'};
const smooth = THREE.MathUtils.smoothstep;

function surfaceOpacity(geometry, contact, reveal) {
  const positions = geometry.getAttribute('position');
  let color = geometry.getAttribute('color');
  if (!color) {
    color = new THREE.Float32BufferAttribute(new Float32Array(positions.count * 4), 4);
    geometry.setAttribute('color', color);
  }
  for (let i = 0; i < positions.count; i++) {
    const x = positions.getX(i), y = positions.getY(i), z = positions.getZ(i);
    // An anterior acoustic window retains the silhouette and intact contact
    // patch while revealing the atlas landmarks, heart and sector below it.
    const radius = Math.hypot((x - 21) / 127, (y - 1245) / 120);
    const front = smooth(z, 95, 160);
    const window = (1 - smooth(radius, .65, 1.2)) * front;
    const distance = Math.hypot(x-contact[0], y-contact[1], z-contact[2]);
    const contactPatch = (1 - smooth(distance, 7, 25)) * .43;
    const contactShade = 1 - .38 * Math.exp(-distance * distance / 180);
    color.setXYZW(i, contactShade, contactShade, contactShade, reveal ? Math.min(1, 1 - .65 * window + contactPatch) : 1);
  }
  color.needsUpdate = true;
}

function shellMesh(rings, ink, periodic) {
  const rows = rings.length, cols = rings[0].length;
  const idx = [];
  for (let r = 1; r < rows; r++) {
    for (let c = 0; c < cols - Number(!periodic); c++) {
      const a = (r - 1) * cols + c, b = (r - 1) * cols + (c + 1) % cols;
      idx.push(a, b, b+cols, a, b+cols, a+cols);
    }
  }
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.Float32BufferAttribute(new Float32Array(rows * cols * 3), 3));
  geo.setIndex(idx);
  const mesh = new THREE.Mesh(geo, ink);
  mesh.frustumCulled = false;
  updateShell(mesh, rings);
  return mesh;
}

function updateShell(mesh, rings) {
  const position = mesh.geometry.getAttribute('position');
  let index = 0;
  for (const row of rings) {
    for (const p of row) position.setXYZ(index++, p[0], p[1], p[2]);
  }
  position.needsUpdate = true;
  mesh.geometry.computeVertexNormals();
}

export function createRegisteredHeart(patient, initial = heartFrame(0)) {
  const group = new THREE.Group();
  // Use one registration for all tissue, arteries and the acoustic rig.
  group.matrix.makeBasis(...heartAxes.map(vector));
  group.matrix.setPosition(vector(heartOrigin));
  group.matrixAutoUpdate = false;
  patient.add(group);
  const shells = new Map();
  function drawShell(key, rings, color, periodic = true) {
    const current = shells.get(key);
    if (!current) {
      const mesh = shellMesh(rings, material(color, {side: THREE.DoubleSide}), periodic);
      mesh.name = key;
      shells.set(key, {mesh, rings});
      group.add(mesh);
    } else if (current.rings !== rings) {
      updateShell(current.mesh, rings);
      current.rings = rings;
    }
  }

  function update(frame) {
    for (const [name, chamber] of Object.entries(frame.chambers)) {
      drawShell(name, chamber.wall, chamberColors[name]);
    }
    for (const [name, vessel] of Object.entries(frame.vessels)) {
      // The inlet/outlet trunks provide directional context at torso scale.
      if (name === 'LVOT' || name === 'RVOT') continue;
      const venous = ['IVC', 'SVC', 'PA', 'RPA'].includes(name);
      vessel.wall.forEach((rings, index) => drawShell(name + '/' + index, rings, venous ? '#627c91' : '#aa6760'));
    }

    const ordinal = { AV: 0, PV: 0 };
    for (const { name, material, rings } of frame.details) {
      if (material !== 'leaflet' || !Object.hasOwn(ordinal, name)) continue;
      const valve = name === 'AV' ? 'Aortic' : 'Pulmonary';
      // These sampled patches have free boundaries. Wrapping the row would
      // create an artificial strip between the two commissures.
      drawShell(`${valve} valve cusp ${++ordinal[name]}`, rings, valveColors[name], false);
    }
  }
  update(initial);
  return {group, update};
}

export function phasedTransducer() {
  // A small phased-array head with the orientation mark on image-right. Local
  // +Y points from the lens toward the hand; the central beam is its opposite.
  const group = new THREE.Group();
  function piece(rows, ink) {
    const segments = 32;
    const positions = [], indices = [];
    for (const [height, across, front] of rows) {
      for (let j = 0; j < segments; j++) {
        const angle = 2*Math.PI*j/segments;
        const x = Math.cos(angle), z = Math.sin(angle);
        positions.push(across*Math.sign(x)*Math.abs(x)**.7, height, front*Math.sign(z)*Math.abs(z)**.7);
      }
    }
    for (let i = 1; i < rows.length; i++) {
      for (let j = 0; j < segments; j++) {
        const a = (i-1)*segments+j, b=(i-1)*segments+(j+1)%segments;
        indices.push(a, a+segments, b, b, a+segments, b+segments);
      }
    }
    const geo = new THREE.BufferGeometry();
    geo.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
    geo.setIndex(indices);
    geo.computeVertexNormals();
    group.add(new THREE.Mesh(geo, ink));
  }
  piece([[0,.4,.4],[.6,7.8,5.4],[1.7,9.7,7.1],[4.4,10,7.5]], material('#1b343e'));
  piece([[4.4,10,7.5],[8.5,10.4,8.2],[15,11.2,9],[21,10,8.6],
    [31,9.1,7.6],[47,8,6.5],[52,6.9,5.5],[55,4.2,4]],material('#f0eee4'));
  piece([[55,4.3,4],[60,4,3.8],[66,2.8,2.6],[68,2,2]],material('#66777d'));
  piece([[22.5,10.05,8.62],[23.6,10.04,8.6],[25.2,9.8,8.48]],
    material('#98a8a8'));
  const marker = new THREE.Mesh(new THREE.SphereGeometry(3.25, 12, 8), material('#007f72', {emissive: '#08382d'}));
  marker.position.set(10.2, 11.1, 1.1);
  group.add(marker);
  const stripe = [];
  for (let i = -8; i <= 8; i++) {
    const a = i*Math.PI/20;
    stripe.push(vector([10.55*Math.cos(a)**.7, 8.8, 8.4*Math.sign(a)*Math.abs(Math.sin(a))**.7]));
  }
  group.add(new THREE.Mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(stripe),20,1.45,8,false),
    material('#008176', {emissive:'#07332c'})));
  const path = new THREE.CatmullRomCurve3([[0,67,0],[0,77,0],[2,92,-3],[7,106,-9]].map(vector));
  group.add(new THREE.Mesh(new THREE.TubeGeometry(path, 20, 1.6, 9, false), material('#b0bebd')));
  group.traverse(mesh => {
    if (!mesh.material) return;
    mesh.material.transparent = true;
    mesh.renderOrder = 7;
  });
  group.scale.set(1.06,1.26,1.06);
  return group;
}

function scanRig(patient) {
  const probe = phasedTransducer();
  const fan = new THREE.Group();
  patient.add(probe,fan);
  let drawn;
  function setPlane(plane) {
    const origin = vector(bodyPoint(plane.origin));
    const outward = vector(bodyDirection(plane.down)).negate();
    const right = vector(bodyDirection(plane.right));
    probe.position.copy(origin);
    probe.quaternion.setFromRotationMatrix(new THREE.Matrix4().makeBasis(right, outward, right.clone().cross(outward)));
    if (drawn) {
      for (const mesh of drawn) {
        mesh.geometry.dispose();
        mesh.material.dispose();
        fan.remove(mesh);
      }
    }
    const arc = [];
    for (let i = 0; i <= 48; i++) {
      const a = (i/48*2-1)*plane.halfAngle;
      arc.push(vector(bodyPoint(plane.world(plane.depth*Math.sin(a),plane.depth*Math.cos(a)))));
    }
    const points = [origin, ...arc];
    const fill = new THREE.BufferGeometry().setFromPoints(points);
    fill.setIndex(arc.slice(1).flatMap((_, i) => [0, i+1, i+2]));
    const face = new THREE.Mesh(fill, new THREE.MeshBasicMaterial({
      color:'#16c0a4', transparent:true, opacity:.26, side:THREE.DoubleSide, depthWrite:false, depthTest:false,
    }));
    // Draw inside anatomy, then let the translucent skin occlude the sector.
    face.renderOrder = 2;
    const edgePath = new THREE.CurvePath();
    for (let i = 0; i < points.length; i++) {
      edgePath.add(new THREE.LineCurve3(points[i],points[(i+1)%points.length]));
    }
    const line = new THREE.Mesh(new THREE.TubeGeometry(edgePath,180,.58,5,false),
      new THREE.MeshBasicMaterial({color:'#48e5c9',transparent:true,opacity:.98,depthTest:false,depthWrite:false}));
    line.renderOrder = 3;
    const target = vector(bodyPoint(CARDIAC_VIEWS[plane.id].target));
    const axis = new THREE.Line(new THREE.BufferGeometry().setFromPoints([origin, target]),
      new THREE.LineDashedMaterial({color:'#adebd2',dashSize:3,gapSize:2,transparent:true,
        opacity:.92,depthTest:false,depthWrite:false}));
    axis.computeLineDistances(); axis.renderOrder = 3;
    drawn = [face,line,axis];
    fan.add(...drawn);
  }
  return {fan,setPlane};
}

function sideLabel(text, x) {
  const face = document.createElement('canvas');
  face.width = 160; face.height = 50;
  const ink = face.getContext('2d');
  ink.fillStyle = 'rgba(18,33,37,.86)';
  ink.beginPath(); ink.roundRect(1,1,158,48,13); ink.fill();
  ink.font = '600 27px system-ui'; ink.textAlign = 'center'; ink.textBaseline = 'middle';
  ink.fillStyle = '#f2eee6'; ink.fillText(text,80,25);
  const map = new THREE.CanvasTexture(face); map.colorSpace = THREE.SRGBColorSpace;
  const label = new THREE.Sprite(new THREE.SpriteMaterial({map, transparent:true,depthTest:false,depthWrite:false}));
  label.position.set(x,1348,140); label.scale.set(64,20,1); label.renderOrder=8;
  return label;
}

export function loadTorsoParts() {
  return Promise.all(['skin', 'bones', 'cartilage'].map(name =>
    loadMesh(name, new URL(name + '.raw', import.meta.url))));
}

export async function createTorsoView(canvas) {
  const parts = await loadTorsoParts();
  const renderer = new THREE.WebGLRenderer({canvas, antialias:true, alpha:false, powerPreference:'low-power'});
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.5));
  renderer.setClearColor('#15262a');
  const scene = new THREE.Scene();
  const camera = new THREE.OrthographicCamera(-300,300,220,-220,1,1700);
  scene.add(new THREE.HemisphereLight('#fff6e8','#9da4a3',1.64));
  const key = new THREE.DirectionalLight('#fff1d8',2.25);
  key.position.set(-400,1550,690); scene.add(key);
  key.target.position.set(0,1210,110); scene.add(key.target);
  const fill = new THREE.DirectionalLight('#c8e9eb',1.05);
  fill.position.set(500,1450,180); scene.add(fill);
  fill.target.position.copy(key.target.position); scene.add(fill.target);
  const patient = new THREE.Group();
  const pose = new THREE.Group();
  patient.position.set(0,-1200,-110);
  pose.position.set(0,1200,110);
  pose.add(patient); scene.add(pose);
  const [skinGeometry,boneGeometry,cartilageGeometry] = parts;
  const skin = new THREE.Mesh(skinGeometry, material('#c3977c',{
    vertexColors:true,transparent:true,depthWrite:false,side:THREE.FrontSide,roughness:.80,
  }));
  skin.renderOrder = 5;
  // BP3D models the full skin thickness. A front-surface depth pass keeps
  // the inside sheet from painting through the outer surface during orbit.
  const skinDepth = new THREE.Mesh(skinGeometry, new THREE.MeshBasicMaterial({
    colorWrite:false, transparent:true, depthWrite:true, side:THREE.FrontSide,
  }));
  skinDepth.renderOrder = 4;
  const bone = new THREE.Mesh(boneGeometry, material('#dbcbb0'));
  const cartilage = new THREE.Mesh(cartilageGeometry,material('#b8b19b'));
  patient.add(skinDepth,skin,bone,cartilage);
  const sides = [sideLabel('Patient R',-169), sideLabel('Patient L',169)];
  patient.add(...sides);
  const cardiac = createRegisteredHeart(patient), rig = scanRig(patient);
  // A rigid left-side roll illustrates positioning relative to the exam couch;
  // source anatomy retains its native shape in either posture.
  const couch = new THREE.Mesh(new THREE.PlaneGeometry(590,1010),material('#344b50'));
  couch.position.set(0,1260,-72); scene.add(couch);
  let width, height, previousId, previousTilt, previousPhase, previousReveal;
  return {
    render({viewId = 'a4c', phase = 0, tilt = 0, yaw = 12, pitch = 2, zoom = 1, close = false, reveal = true, frame} = {}) {
      if (!canvas.clientWidth || !canvas.clientHeight) return;
      if (width !== canvas.clientWidth || height !== canvas.clientHeight) {
        width=canvas.clientWidth; height=canvas.clientHeight;
        renderer.setSize(width,height,false);
      }
      const view = CARDIAC_VIEWS[viewId] ?? CARDIAC_VIEWS.a4c;
      const contact = bodyPoint(view.origin);
      if (previousId !== viewId || previousReveal !== reveal) {
        surfaceOpacity(skinGeometry,contact,reveal);
        bone.visible = cartilage.visible = cardiac.group.visible = rig.fan.visible = reveal;
        previousReveal=reveal;
      }
      if (previousId !== viewId || previousTilt !== tilt) {
        rig.setPlane(probePlane(tilt,viewId));
        previousId=viewId; previousTilt=tilt;
      }
      if (reveal && previousPhase !== phase) {
        cardiac.update(frame ?? heartFrame(phase));
        previousPhase = phase;
      }
      const lateral = view.group === 'Apical' || view.group === 'Parasternal';
      pose.rotation.y = radians(lateral ? 28 : 0);
      const target = close ? patient.localToWorld(vector(contact)) : new THREE.Vector3(0,1215,130);
      // Head-up anterior view of the recumbent torso. Orbit remains independent
      // of patient roll, heart phase and probe selection.
      const a = radians(yaw + (lateral ? 13 : 0)), b = radians(pitch);
      const radius = 760;
      camera.position.set(target.x+radius*Math.sin(a)*Math.cos(b),
        target.y+radius*Math.sin(b),target.z+radius*Math.cos(a)*Math.cos(b));
      const halfHeight = (close ? 112 : 213) / Math.max(.6,Math.min(2,zoom));
      camera.left = -halfHeight * width/height;
      camera.right = -camera.left;
      camera.top = halfHeight; camera.bottom = -halfHeight;
      camera.lookAt(target); camera.updateProjectionMatrix(); camera.updateMatrixWorld();
      const projected = sides.map(label => label.getWorldPosition(new THREE.Vector3()).project(camera));
      const separate = Math.abs(projected[0].x - projected[1].x) * width / 2 > 92;
      sides.forEach(label => { label.visible = separate && !close; });
      renderer.render(scene,camera);
    },
  };
}
