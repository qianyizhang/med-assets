import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp,writeFile,readFile,rm,realpath} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {uploadRepositoryAssets,groups} from '../tools/r2_upload.mjs';
const hash=bytes=>createHash('sha256').update(bytes).digest('hex');
async function fixture(t,count=3){
  const root=await realpath(await mkdtemp(join(tmpdir(),'r2-upload-test-')));t.after(()=>rm(root,{recursive:true,force:true}));
  const assets=[];const objects=new Map();
  for(let i=0;i<count;i++){
    const body=Buffer.from('glTF-payload-'+i),name='model-'+i+'.glb';
    await writeFile(join(root,name),body);
    assets.push({path:name,name,sha256:hash(body),bytes:body.length,mediaType:'model/gltf-binary'});
  }
  const git=(...args)=>execFileSync('git',['-C',root,...args],{encoding:'utf8'}).trim();
  git('init','-q');git('add','.');git('-c','user.name=Fixture','-c','user.email=fixture@example.invalid','commit','-qm','fixture');
  const manifest={assets,repositoryPayloads:{revision:git('rev-parse','HEAD'),count,bytes:assets.reduce((sum,x)=>sum+x.bytes,0)}};
  const calls=[];
  const fetchImpl=async(url,options)=>{
    calls.push({url,method:options.method||'GET'});assert.equal(options.redirect,'error');
    const asset=assets.find(x=>url.endsWith('/'+x.name));assert.ok(asset);
    if(options.method==='PUT'){
      let body=Buffer.alloc(0);for await(const chunk of options.body)body=Buffer.concat([body,chunk]);
      assert.equal(hash(body),asset.sha256);assert.equal(options.headers['content-length'],String(body.length));
      objects.set(asset.sha256,body);
      return Response.json({sha256:asset.sha256,bytes:asset.bytes});
    }
    assert.equal(options.cache,'no-store');
    return new Response(objects.get(asset.sha256));
  };
  return {root,manifest,objects,calls,fetchImpl,statePath:join(root,'state.json'),token:'fixture-token-'.repeat(4)};
}

test('complete streaming upload/readback and explicit resume retain exact identities',async t=>{
  const f=await fixture(t);const result=await uploadRepositoryAssets(f);
  assert.equal(result.verified,3);assert.equal(result.bytes,f.manifest.repositoryPayloads.bytes);
  const state=JSON.parse(await readFile(f.statePath,'utf8'));assert.equal(state.verified.length,3);
  f.calls.length=0;const resumed=await uploadRepositoryAssets(f);
  assert.equal(resumed.verified,3);assert.ok(f.calls.every(x=>x.method==='GET'));
});

test('readback corruption stops the run after its current bounded group and retains verified progress',async t=>{
  const f=await fixture(t,5);const original=f.fetchImpl;
  f.fetchImpl=async(url,options)=>{
    if(!options.method&&url.endsWith('model-0.glb'))return new Response('corrupt');
    return original(url,options);
  };
  await assert.rejects(uploadRepositoryAssets(f),/readback checksum/);
  assert.equal(f.calls.filter(x=>x.method==='PUT').length,4);
  const state=JSON.parse(await readFile(f.statePath,'utf8'));assert.equal(state.verified.length,3);
  assert.ok(!f.calls.some(x=>x.url.endsWith('model-4.glb')));
});

test('changed local/Git identities and unexpected destinations fail before network work',async t=>{
  const f=await fixture(t);let calls=0;f.fetchImpl=async()=>{calls++;throw Error('unexpected network');};
  await assert.rejects(uploadRepositoryAssets({...f,origin:'https://untrusted.invalid'}),/destination/);
  await writeFile(join(f.root,'model-0.glb'),'changed');
  await assert.rejects(uploadRepositoryAssets(f),/Local payload changed/);assert.equal(calls,0);
  f.manifest.assets[0].sha256='0'.repeat(64);
  await assert.rejects(uploadRepositoryAssets(f),/pinned Git payload/);assert.equal(calls,0);
});

test('quota/permission failure has no automatic retry or next group',async t=>{
  const f=await fixture(t,5);let calls=0;
  f.fetchImpl=async()=>{calls++;return new Response('denied',{status:403});};
  await assert.rejects(uploadRepositoryAssets(f),/HTTP 403/);assert.equal(calls,4);
});

test('batch accounting enforces exact object and total byte bounds',()=>{
  const small=Array.from({length:70},()=>({bytes:1_000_000}));assert.deepEqual(groups(small).map(x=>x.length),[32,32,6]);
  assert.equal(groups([{bytes:42_497_262},{bytes:30_000_000}]).length,2);
  assert.throws(()=>groups([{bytes:64_000_001}]),/bound/);
  assert.throws(()=>groups(small,0),/bounds/);
});
