// CPU helper tests, not a WebGL sensitivity pass. Run with node --test.
import {test} from 'node:test';
import assert from 'node:assert/strict';
import {auditGeometry,validNormals,mutateGeometry} from '../../ci/lymph_diagnostics.mjs';
class Attribute {
 constructor(array,itemSize){this.array=new Float32Array(array);this.itemSize=itemSize;this.count=array.length/itemSize;}
 getX(i){return this.array[i*this.itemSize];} getY(i){return this.array[i*this.itemSize+1];} getZ(i){return this.array[i*this.itemSize+2];}
 setX(i,x){this.array[i*this.itemSize]=x;}
 setXYZ(i,x,y,z){this.array.set([x,y,z],i*this.itemSize);}
 clone(){return new Attribute(this.array,this.itemSize);}
}
function triangle() {
 return {attributes:{position:new Attribute([0,0,0,1,0,0,0,1,0],3),normal:new Attribute([0,0,1,0,0,1,0,0,1],3)},
  index:new Attribute([0,1,2],1), getAttribute(key){return this.attributes[key];},
  setAttribute(key,value){this.attributes[key]=value;},getIndex(){return this.index;},setIndex(value){this.index=value;}};
}
test('nonzero unit, finite, and referenced normal checks are distinct',()=>{
 const g=triangle();assert.equal(validNormals(auditGeometry(g)),true);
 for(const [normal,key] of [[[0,0,0],'zero'],[[0,0,2],'nonunit'],[[NaN,0,1],'nonfinite']]) {
  g.attributes.normal.setXYZ(0,...normal);const r=auditGeometry(g);
  assert.equal(r[key],1);assert.equal(validNormals(r),false);
 }
});
test('negated loaded normals stay unit but oppose triangle facing; exact restore',()=>{
 const g=triangle(),original=g.attributes.normal,positions=g.attributes.position,index=g.index;
 const restore=mutateGeometry(g,'negated-normals'),r=auditGeometry(g);
 assert.equal(validNormals(r),true);assert.equal(r.opposedNormalCorners,3);
 assert.deepEqual(Array.from(original.array),[0,0,1,0,0,1,0,0,1]);
 assert.equal(g.attributes.position,positions);assert.equal(g.index,index);
 restore();assert.equal(g.attributes.normal,original);assert.equal(auditGeometry(g).opposedNormalCorners,0);
});
test('reversed winding changes indices, preserves normals and restores exact object',()=>{
 const g=triangle(),original=g.index,normal=g.attributes.normal;
 const restore=mutateGeometry(g,'reversed-winding');
 assert.deepEqual(Array.from(g.index.array),[0,2,1]);assert.deepEqual(Array.from(original.array),[0,1,2]);
 assert.equal(g.attributes.normal,normal);assert.equal(auditGeometry(g).opposedNormalCorners,3);
 restore();assert.equal(g.index,original);assert.equal(auditGeometry(g).opposedNormalCorners,0);
});
test('degenerate geometry is counted; out of range indices and unknown controls fail',()=>{
 const g=triangle();g.index.setX(2,1);assert.equal(auditGeometry(g).degenerateTriangles,1);
 g.index.setX(2,99);assert.throws(()=>auditGeometry(g),/Invalid triangle index/);
 assert.throws(()=>mutateGeometry(g,'anything'),/Unknown negative control/);
});
