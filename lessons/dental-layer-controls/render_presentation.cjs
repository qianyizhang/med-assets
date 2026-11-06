/* Actual app/controller/parser/rasterizer pixels, DOM/Canvas/RAF doubles. No browser screenshot. */
const {start}=require('./app-harness.cjs');
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),assert=require('node:assert/strict');
const out=process.argv[2];if(!out)throw Error('Usage: DENTAL_SOURCE=exact.glb node render_presentation.cjs OUTPUT_DIR');fs.mkdirSync(out,{recursive:true});
const sha=data=>crypto.createHash('sha256').update(data).digest('hex');
(async()=>{
 const h=await start(),records=[],baseline=h.pixels();
 const capture=(name,label)=>{const pixels=h.pixels();fs.writeFileSync(path.join(out,name+'.rgba'),pixels);records.push({name,label,width:630,height:440,pixelSha256:sha(pixels),evidence:h.evidence()});};
 const edit=(id,value)=>{h.ids['#'+id].value=value;h.ids['#'+id].fire(id.startsWith('colour-')?'input':'change');};
 capture('original','Original | default camera and editorial RGB');
 edit('colour-enamel','#66b6c8');edit('colour-bone','#9170ad');h.flush();capture('palette','Updated | palette only, matched original camera');
 h.ids['#reset'].fire('click');h.flush();
 for(const [id,value] of [['camera-yaw','.65'],['camera-pitch','1.0'],['camera-zoom','.9'],['target-0','.03']])edit(id,value);
 h.flush();capture('camera','Updated | camera only, original palette');
 edit('colour-enamel','#66b6c8');edit('colour-bone','#9170ad');h.flush();capture('combined','Updated | camera and palette edits');
 const saved=h.ctx.window.dentalAuthoring.save(),reopened=await start({script:saved});assert.deepEqual(h.pixels(),reopened.pixels());
 fs.writeFileSync(path.join(out,'edited-script.json'),saved);
 h.ids['#play'].fire('click');h.advance(4500);h.ids['#reset'].fire('click');h.advance(9000);capture('reset','Reset | interrupted playback, original pixels exact');
 assert.deepEqual(h.pixels(),baseline);assert.notEqual(records[0].pixelSha256,records[1].pixelSha256);assert.notEqual(records[0].pixelSha256,records[2].pixelSha256);
 fs.writeFileSync(path.join(out,'presentation-frames.json'),JSON.stringify({kind:'actual-app CPU pixel evidence, not browser screenshots',sourceSha256:records[0].evidence.sourceSha256,resetPixelsExact:true,reopenPixelsExact:true,scripts:Object.fromEntries(['authoring.js','app.js','app-harness.cjs','renderer.js','controller.js','render_presentation.cjs'].map(f=>[f,sha(fs.readFileSync(path.join(__dirname,f)))])),records},null,2)+'\n');
})();
