// Compare the delivered case geometry with the acquisition recipe in its original millimetre frame.
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFile, writeFile } from 'node:fs/promises';
import { resolve, sep } from 'node:path';
import { pathToFileURL } from 'node:url';

const root = pathToFileURL(resolve(process.argv[2]) + sep);
const catalogue = await readFile(new URL('abdomen-tours.js', root), 'utf8');
globalThis.abdomenTours = JSON.parse(catalogue.slice(catalogue.indexOf('[')).trim().replace(/;$/, ''));
globalThis.fetch = async (url) => new Response(await readFile(new URL(url)));
const {createCaseModel} = await import(new URL('cases/vascular/playable-scene.js', root));
const {getTube} = await import(new URL('cases/vascular/playable-model.js', root));
const records = JSON.parse(await readFile(new URL('cases.json', import.meta.url)));
const result = [];
for (const record of records.filter(row => row.family === 'carotid')) {
  const model = await createCaseModel(record);
  model.anatomy.traverse(({isMesh, name, geometry}) => {
    const match = /^(Right|Left) (CCA|ICA|ECA|IJV|VA)( lumen)?$/.exec(name);
    if (!isMesh || !match) return;
    const [,side,vessel,lumen] = match;
    const positions = geometry.attributes.position;
    const rings = [];
    // The first ascending run is the outside of the tested component.
    for (let start=0;start<positions.count;start+=40) {
      const z=positions.getZ(start);
      if (rings.length && z<=rings.at(-1).z) break;
      rings.push({z,start});
    }
    let maxError=0, maxZ=0;
    for(let i=1;i<rings.length;i++) {
      const a=rings[i-1],b=rings[i],steps=Math.ceil((b.z-a.z)/.2);
      for(let k=0;k<=steps;k++) {
        const t=k/steps,z=a.z+(b.z-a.z)*t;
        const tube=getTube(record,side,z,vessel);
        assert.ok(tube, record.id+'/'+name+' unbound station '+z);
        const cx=lumen?tube.lx:tube.x,cy=lumen?tube.ly:tube.y;
        const rx=lumen?tube.lrx:tube.rx,ry=lumen?tube.lry:tube.ry;
        const shift=side==='Right'?-19:19;
        const sample=(get,j)=>get.call(positions,a.start+j)*(1-t)+get.call(positions,b.start+j)*t;
        for(let j=0;j<40;j++) {
          const next=(j+1)%40;
          // Include chord midpoints where the tessellated ellipse is most vulnerable.
          for(const half of [0,.5]) {
            const angle=(j+half)*Math.PI/20;
            const x=sample(positions.getX,j)*(1-half)+sample(positions.getX,next)*half;
            const y=sample(positions.getY,j)*(1-half)+sample(positions.getY,next)*half;
            const error=Math.hypot(x+cx+shift+rx*Math.cos(angle), y+cy+ry*Math.sin(angle));
            if(error>maxError){maxError=error;maxZ=z;}
          }
        }
      }
    }
    assert.ok(maxError<.05, record.id+'/'+name+': contour error '+maxError.toFixed(3)+' mm');
    const hash=createHash('sha256').update(Buffer.from(positions.array.buffer)).update(Buffer.from(geometry.index.array.buffer)).digest('hex');
    result.push({case:record.id,part:name,maxError,maxZ,meshSha256:hash});
  });
  model.dispose();
}
if(process.argv[3]) await writeFile(process.argv[3],JSON.stringify(result,null,2)+'\n');
console.log(result.length+' wall and lumen surfaces checked on a 0.2 mm axial grid; peak contour discrepancy '+Math.max(...result.map(row=>row.maxError)).toFixed(3)+' mm');
