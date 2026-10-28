// Inject the existing reviewed renderer/loader/snapshot path; never launch a browser.
// Deterministic scene API exercise, not native UI or whole-Site acceptance.
export async function runEsophagus({THREE, GLTFLoader, renderer, scene, camera, snapshot, check, fixture}) {
  const assert=(ok,message)=>{if(!ok)throw Error(message);};
  const digest=async bytes=>Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)),n=>n.toString(16).padStart(2,'0')).join('');
  const gl=renderer.getContext();
  const read=()=>{const p=new Uint8Array(512*512*4);gl.readPixels(0,0,512,512,gl.RGBA,gl.UNSIGNED_BYTE,p);return p;};
  const panel=document.createElement('aside');panel.style.cssText='width:440px;font:18px sans-serif;line-height:1.4;color:#111;background:white';
  document.querySelector('.row').append(panel);
  const oldStatus=document.querySelector('#status');const oldDisplay=oldStatus.style.display;oldStatus.style.display='none';
  const initial={position:camera.position.clone(),quaternion:camera.quaternion.clone(),up:camera.up.clone(),left:camera.left,right:camera.right,top:camera.top,bottom:camera.bottom,near:camera.near,far:camera.far};
  const assets=[],extras=[];
  function legend(language){
    panel.replaceChildren();panel.lang=language==='zh'?'zh-CN':'en';
    const labels=fixture.layers.map(l=>`${l.number}  ${l[language]}`);
    for(const text of [fixture.notices[language],fixture.context[language],...labels,fixture.attribution]){
      const p=document.createElement('p');p.textContent=text;panel.append(p);
    }
    const r=panel.getBoundingClientRect();
    return {language,labels,notice:fixture.notices[language],context:fixture.context[language],attribution:fixture.attribution,
      rect:{x:Math.round(window.mozInnerScreenX+r.left),y:Math.round(window.mozInnerScreenY+r.top),width:r.width,height:r.height}};
  }
  function view(transverse){
    camera.up.set(0,0,-1);camera.left=camera.bottom=transverse?-.0165:-.0335;camera.right=camera.top=-camera.left;
    camera.near=.00001;camera.far=2;
    camera.position.copy(new THREE.Vector3(0,.0225,0)).add(transverse?new THREE.Vector3(0,.3,0):new THREE.Vector3(.85,1.1,1.7).normalize().multiplyScalar(.3));
    camera.lookAt(0,.0225,0);camera.updateProjectionMatrix();camera.updateMatrixWorld(true);
  }
  async function load(variant){
    const resource=fixture[variant];
    const response=await fetch(resource.path,{credentials:'omit',redirect:'error'});assert(response.ok,'Esophagus input HTTP failure');
    const bytes=await response.arrayBuffer();assert(bytes.byteLength===resource.bytes&&await digest(bytes)===resource.sha256,'Exact esophagus bytes required');
    const dv=new DataView(bytes);assert(dv.getUint32(0,true)===0x46546c67&&dv.getUint32(4,true)===2&&dv.getUint32(8,true)===bytes.byteLength&&dv.getUint32(16,true)===0x4e4f534a,'GLB header');
    const doc=JSON.parse(new TextDecoder().decode(bytes.slice(20,20+dv.getUint32(12,true))));
    assert(doc.nodes.length===5&&doc.meshes.length===5&&doc.materials.length===5&&!doc.animations?.length&&!doc.images?.length&&!doc.extensionsRequired?.length&&doc.buffers.length===1&&!doc.buffers[0].uri,'Bounded embedded static GLB');
    const manager=new THREE.LoadingManager();manager.setURLModifier(()=>{throw Error('External esophagus resource forbidden');});
    const model=await new GLTFLoader(manager).parseAsync(bytes,'');
    const nodes=new Map(),transforms=new Map(),materials=[];
    model.scene.traverse(o=>transforms.set(o,JSON.stringify([o.position.toArray(),o.quaternion.toArray(),o.scale.toArray()])));
    for(const l of fixture.layers){
      const node=await model.parser.getDependency('node',l.node);nodes.set(l.node,node);
      assert(doc.nodes[l.node].name===l.name&&doc.nodes[l.node].mesh===l.mesh&&doc.nodes[l.node].extras.layer_order_inside_out===l.number,'Source layer mapping');
      assert(node.isMesh&&node.geometry.index.count===4620,'One loaded mesh / 1540 triangles per compartment');
      const material=node.material,rgba=l[variant+'RGBA'];
      const loaded=[...material.color.toArray(),material.opacity];
      check(loaded.every((x,i)=>Math.abs(x-rgba[i])<1e-7)&&material.name===l.name&&material.side===THREE.DoubleSide&&material.metalness===0&&Math.abs(material.roughness-.7200000286102295)<1e-7,`${variant}: loaded material ${l.number}`);
      materials.push({number:l.number,name:material.name,rgba:loaded,metalness:material.metalness,roughness:material.roughness,doubleSided:material.side===THREE.DoubleSide});
    }
    const asset={id:resource.id,resource,model,doc,nodes,transforms,meshCount:5,morphCount:0,materials};assets.push(asset);return asset;
  }
  const extra=(asset,language='en')=>({legend:legend(language),materials:asset.materials});
  try {
    let candidate,transversePixels;
    for(const variant of ['baseline','candidate']){
      const asset=await load(variant);scene.add(asset.model.scene);view(false);
      await snapshot(`esophagus-${variant}-oblique`,asset,extra(asset),variant==='candidate'?'esophagus-baseline-oblique':null,variant==='candidate'?64:null);
      view(true);await snapshot(`esophagus-${variant}-transverse`,asset,extra(asset),variant==='candidate'?'esophagus-baseline-transverse':null,variant==='candidate'?64:null);
      if(variant==='candidate')transversePixels=read();
      for(const layer of fixture.layers){
        for(const [i,node] of asset.nodes)node.visible=i===layer.node;
        await snapshot(`esophagus-${variant}-layer-${layer.number}`,asset,extra(asset),variant==='candidate'?`esophagus-baseline-layer-${layer.number}`:null,variant==='candidate'?64:null);
      }
      for(const node of asset.nodes.values())node.visible=true;
      scene.remove(asset.model.scene);if(variant==='candidate')candidate=asset;
    }
    scene.add(candidate.model.scene);view(true);scene.updateMatrixWorld(true);
    const anchors=fixture.layers.map(l=>{
      const point=new THREE.Vector3(...l.anchor),ndc=point.clone().project(camera),ray=new THREE.Raycaster();ray.setFromCamera(new THREE.Vector2(ndc.x,ndc.y),camera);
      const hit=ray.intersectObjects([...candidate.nodes.values()],true)[0];
      assert(hit&&hit.object===candidate.nodes.get(l.node),'Numbered anchor misses its loaded compartment');
      return {number:l.number,hitNode:l.node,point:l.anchor,pixel:[Math.round((ndc.x+1)*256),Math.round((1-ndc.y)*256)]};
    });
    // Grayscale is derived from real lit readPixels, not baseColorFactor or swatches.
    const sheet=document.createElement('canvas');sheet.width=sheet.height=512;const ctx=sheet.getContext('2d');const rgba=ctx.createImageData(512,512);
    for(let y=0;y<512;y++)for(let x=0;x<512;x++){
      const s=((511-y)*512+x)*4,t=(y*512+x)*4;
      const lum=Math.round(.2126*transversePixels[s]+.7152*transversePixels[s+1]+.0722*transversePixels[s+2]);
      rgba.data.set([lum,lum,lum,255],t);
    }
    ctx.putImageData(rgba,0,0);ctx.textAlign='center';ctx.textBaseline='middle';ctx.font='bold 16px sans-serif';
    for(const a of anchors){const [x,y]=a.pixel;ctx.fillStyle='#111';ctx.strokeStyle='#fff';ctx.lineWidth=1;ctx.beginPath();ctx.arc(x,y,10,0,2*Math.PI);ctx.fill();ctx.stroke();ctx.fillStyle='#fff';ctx.fillText(String(a.number),x,y);}
    const texture=new THREE.CanvasTexture(sheet);texture.colorSpace=THREE.SRGBColorSpace;texture.minFilter=texture.magFilter=THREE.NearestFilter;
    const material=new THREE.MeshBasicMaterial({map:texture,toneMapped:false,depthTest:false,depthWrite:false});
    const quad=new THREE.Mesh(new THREE.PlaneGeometry(.033,.033),material);quad.position.set(0,.0225,0);quad.quaternion.copy(camera.quaternion);quad.frustumCulled=false;
    extras.push(quad);scene.remove(candidate.model.scene);scene.add(quad);
    const graySourceSHA256=await digest(transversePixels);
    for(const language of ['en','zh'])await snapshot(`esophagus-candidate-gray-${language}`,candidate,{...extra(candidate,language),anchors,graySourceSHA256,diagnostic:'display-luma from actual transverse framebuffer; numbered overlay'});
    scene.remove(quad);scene.add(candidate.model.scene);candidate.nodes.get(4).visible=false;
    await snapshot('esophagus-candidate-hidden',candidate,extra(candidate),'esophagus-candidate-transverse',64);
    candidate.nodes.get(4).visible=true;
    await snapshot('esophagus-candidate-restored',candidate,extra(candidate),'esophagus-candidate-transverse',null,0);
  } finally {
    for(const asset of assets){scene.remove(asset.model.scene);asset.model.scene.traverse(o=>{if(o.isMesh){o.geometry.dispose();o.material.dispose();}});}
    for(const o of extras){scene.remove(o);o.geometry.dispose();o.material.map.dispose();o.material.dispose();}
    panel.remove();oldStatus.style.display=oldDisplay;
    camera.position.copy(initial.position);camera.quaternion.copy(initial.quaternion);camera.up.copy(initial.up);
    for(const key of ['left','right','top','bottom','near','far'])camera[key]=initial[key];camera.updateProjectionMatrix();
  }
}
