#!/usr/bin/env node
// Upload only manifest-declared, Git-pinned local bytes. Tokens arrive through stdin.
import {createHash} from 'node:crypto';
import {createReadStream,constants} from 'node:fs';
import {readFile,rename,mkdir,lstat,realpath,open,unlink} from 'node:fs/promises';
import {execFileSync} from 'node:child_process';
import {resolve,dirname,posix} from 'node:path';
import {fileURLToPath} from 'node:url';

const ORIGIN='https://med-assets-model-survey.landy123007.chatgpt.site';
const digest=bytes=>createHash('sha256').update(bytes).digest('hex');
const fileStream=path=>createReadStream(path,{flags:constants.O_RDONLY|constants.O_NOFOLLOW});
const pointer=/^version https:\/\/git-lfs.github.com\/spec\/v1\noid sha256:([a-f0-9]{64})\nsize ([1-9][0-9]*)\n$/u;

export function groups(objects,maxObjects=32,maxBytes=64_000_000){
  if(!Number.isSafeInteger(maxObjects)||maxObjects<1||!Number.isSafeInteger(maxBytes)||maxBytes<1)throw Error('Invalid batch bounds');
  const result=[];let batch=[],bytes=0;
  for(const object of objects){
    if(!Number.isSafeInteger(object.bytes)||object.bytes<1||object.bytes>maxBytes)throw Error('Object exceeds reviewed batch bound');
    if(batch.length&&(batch.length===maxObjects||bytes+object.bytes>maxBytes)){result.push(batch);batch=[];bytes=0;}
    batch.push(object);bytes+=object.bytes;
  }
  if(batch.length)result.push(batch);
  return result;
}

export async function checkedObjects(root,manifest){
  const revision=manifest.repositoryPayloads.revision;
  if(!/^[a-f0-9]{40}$/u.test(revision))throw Error('An exact source revision is required');
  const objects=manifest.assets.filter(asset=>asset.path||asset.paths?.length);
  if(objects.length!==manifest.repositoryPayloads.count)throw Error('Repository payload count differs');
  groups(objects); // Enforce resource bounds before reading any payload.
  const seen=new Set();let bytes=0;
  for(const object of objects){
    const name=object.path||object.paths[0];
    if(typeof name!=='string'||posix.isAbsolute(name)||posix.normalize(name)!==name||name.includes('\\')||/[\x00-\x1f]/u.test(name))throw Error('Unsafe payload source path');
    if(!/^[a-f0-9]{64}$/u.test(object.sha256)||!Number.isSafeInteger(object.bytes)||object.bytes<1||!/^[a-zA-Z0-9_.-]+$/u.test(object.name))throw Error('Invalid transport identity');
    if(seen.has(object.sha256))throw Error('Duplicate payload object');seen.add(object.sha256);
    const path=resolve(root,name);
    if(await realpath(path)!==path||!(await lstat(path)).isFile())throw Error('Payload path is not a regular unlinked file');
    const committed=execFileSync('git',['--no-lazy-fetch','show',revision+':'+name],{cwd:root,maxBuffer:65_000_000});
    const match=pointer.exec(committed.toString('utf8'));
    if(committed.subarray(0,20).toString().startsWith('version https://git-')&&!match)throw Error('Malformed committed LFS pointer');
    const expectedHash=match?.[1]||digest(committed),expectedSize=match?Number(match[2]):committed.length;
    if(expectedHash!==object.sha256||expectedSize!==object.bytes)throw Error('Manifest does not match the pinned Git payload: '+name);
    const hash=createHash('sha256');let count=0;
    for await(const chunk of fileStream(path)){hash.update(chunk);count+=chunk.length;}
    if(count!==object.bytes||hash.digest('hex')!==object.sha256)throw Error('Local payload changed: '+name);
    bytes+=count;
  }
  if(bytes!==manifest.repositoryPayloads.bytes)throw Error('Repository payload total differs');
  return objects;
}

export async function uploadRepositoryAssets({root,manifest,token,origin=ORIGIN,statePath,fetchImpl=fetch,onProgress=()=>{}}){
  if(origin.replace(/\/$/u,'')!==ORIGIN)throw Error('Unexpected R2 destination');
  if(typeof token!=='string'||token.length<32||token.length>256)throw Error('A bounded upload lease is required');
  const objects=await checkedObjects(root,manifest),batches=groups(objects);
  const fingerprint=digest(JSON.stringify(manifest));
  let state={revision:manifest.repositoryPayloads.revision,manifestSha256:fingerprint,verified:[]};
  if(statePath){
    statePath=resolve(statePath);await mkdir(dirname(statePath),{recursive:true});
    if(await realpath(dirname(statePath))!==dirname(statePath))throw Error('Migration state directory traverses a link');
    for(const candidate of [statePath,statePath+'.tmp']){
      try{const info=await lstat(candidate);if(info.isSymbolicLink()||!info.isFile())throw Error('Migration state path is a link or special file');if(candidate.endsWith('.tmp'))throw Error('Migration temporary state already exists');}
      catch(error){if(error.code!=='ENOENT')throw error;}
    }
    try{const saved=JSON.parse(await readFile(statePath,'utf8'));if(saved.manifestSha256!==fingerprint)throw Error('Migration state belongs to another manifest');state=saved;}
    catch(error){if(error.code!=='ENOENT')throw error;}
  }
  const verified=new Set(state.verified);let completed=0,completeBytes=0;
  async function persist(){
    if(!statePath)return;
    await mkdir(dirname(statePath),{recursive:true});
    const temporary=statePath+'.tmp';
    const handle=await open(temporary,'wx',0o600);
    try{
      await handle.writeFile(JSON.stringify({...state,verified:[...verified]},null,2)+'\n');await handle.sync();
      await handle.close();await rename(temporary,statePath);
    }catch(error){await handle.close();await unlink(temporary);throw error;}
  }
  async function one(object){
    const url=ORIGIN+'/assets/'+object.sha256+'/'+object.name;
    if(!verified.has(object.sha256)){
      const body=fileStream(resolve(root,object.path||object.paths[0]));
      let response;
      try{response=await fetchImpl(url,{method:'PUT',redirect:'error',headers:{'content-length':String(object.bytes),'content-type':object.mediaType,'x-asset-upload-token':token},body,duplex:'half'});}
      finally{body.destroy();}
      if(response.status!==200)throw Error('R2 upload HTTP '+response.status+' for '+(object.path||object.name));
      const receipt=await response.json();
      if(receipt.sha256!==object.sha256||receipt.bytes!==object.bytes)throw Error('Upload receipt identity differs');
    }
    const response=await fetchImpl(url,{redirect:'error',cache:'no-store',headers:{'accept-encoding':'identity','cache-control':'no-cache'}});
    if(response.status!==200||!['identity',null].includes(response.headers.get('content-encoding')))throw Error('R2 readback status/encoding differs');
    let count=0;const hash=createHash('sha256');
    for await(const chunk of response.body){count+=chunk.length;if(count>object.bytes)throw Error('Readback exceeds pinned size');hash.update(chunk);}
    if(count!==object.bytes||hash.digest('hex')!==object.sha256)throw Error('R2 fresh readback checksum/size differs');
    verified.add(object.sha256);completed++;completeBytes+=count;
  }
  for(let i=0;i<batches.length;i++){
    const batch=batches[i];
    for(let start=0;start<batch.length;start+=4){
      const outcomes=await Promise.allSettled(batch.slice(start,start+4).map(one));
      await persist();
      const failed=outcomes.find(result=>result.status==='rejected');
      if(failed)throw failed.reason;
    }
    onProgress({batch:i+1,batches:batches.length,verified:completed,total:objects.length,bytes:completeBytes});
  }
  return {verified:completed,bytes:completeBytes,revision:state.revision,manifestSha256:fingerprint};
}

async function main(){
  if(process.stdin.isTTY)process.stdin.setRawMode(true);
  process.stdout.write('Ready for hidden R2 upload JSON on stdin\n');
  const input=await new Promise((accept,reject)=>{
    let body='';
    const read=chunk=>{
      body+=chunk;const end=body.indexOf('\n');if(end<0)return;
      process.stdin.off('data',read);process.stdin.pause();
      try{accept(JSON.parse(body.slice(0,end)));}catch{reject(Error('Invalid request JSON'));}
    };
    process.stdin.on('data',read);
    process.stdin.once('end',()=>reject(Error('Upload request ended before its JSON line')));
  });
  const manifest=JSON.parse(await readFile(input.manifestPath,'utf8'));
  const result=await uploadRepositoryAssets({...input,manifest,onProgress:value=>console.log(JSON.stringify(value))});
  console.log(JSON.stringify(result));
  if(process.stdin.isTTY)process.stdin.setRawMode(false);
}
if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url)){
  main().catch(error=>{if(process.stdin.isTTY)process.stdin.setRawMode(false);console.error('R2 migration stopped: '+error.message);process.exitCode=1;process.stdin.pause();});
}
