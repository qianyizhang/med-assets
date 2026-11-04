from pathlib import Path
import subprocess, json, wave, numpy as np
p=Path(__file__).parent; sr=48000; out=np.zeros((48*sr,2)); man=json.loads((p/'cue-manifest.json').read_text())
def read(f):
    with wave.open(str(f),'rb') as w:
        assert w.getframerate()==sr
        a=np.frombuffer(w.readframes(w.getnframes()),dtype='<i2').astype(float)/32768
        return a.reshape(-1,w.getnchannels())
for i,c in enumerate(man['cues']):
    inp=p/f'voice-{i+1}.wav'; length=float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',str(inp)]))
    available=c['end']-c['start']-.6
    tempo=max(1,length/available)
    ffilt=f'atempo={tempo},loudnorm=I=-19:TP=-3:LRA=7'
    dst=p/f'voice-{i+1}-normalized.wav'
    subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(inp),'-af',ffilt,'-ar',str(sr),'-ac','2',str(dst)],check=True)
    a=read(dst); start=c['start']+.3; idx=round(start*sr)
    out[idx:idx+len(a)]+=a
    c['narration_start']=start; c['narration_end']=round(start+len(a)/sr,3); c['tempo_adjustment']=tempo
with wave.open(str(p/'narration.wav'),'wb') as w:
    w.setnchannels(2);w.setsampwidth(2);w.setframerate(sr);w.writeframes((out*32767).astype('<i2').tobytes())
# Gently lower bed during spoken passages, lift it into pauses.
gain=np.ones(len(out))*.65
for c in man['cues']:
    t=np.arange(len(out))/sr
    fade=np.clip((t-(c['narration_start']-.25))/.25,0,1)*np.clip((c['narration_end']+.4-t)/.4,0,1)
    gain=np.minimum(gain,.65-.33*fade)
mix=out+read(p/'score.wav')*gain[:,None]
with wave.open(str(p/'mix-raw.wav'),'wb') as w:
    w.setnchannels(2);w.setsampwidth(2);w.setframerate(sr);w.writeframes((np.clip(mix,-1,1)*32767).astype('<i2').tobytes())
subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(p/'mix-raw.wav'),'-af','loudnorm=I=-18:TP=-2:LRA=7','-ar','48000','-t','48',str(p/'final-mix.wav')],check=True)
subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(p/'final-mix.wav'),'-c:a','libmp3lame','-b:a','160k',str(p/'final-mix.mp3')],check=True)
man.update(title='The Balance: Narration and Original Underscore',spoken_narration=True,voice='Kokoro af_heart, synthesized locally',mix_note='Full original supplied clinical script, scene-timed narration with ducked original procedural score. Target -18 LUFS, -2 dBTP.')
(p/'narration-manifest.json').write_text(json.dumps(man,indent=2)+'\n')
def stamp(s):
    ms=round(s*1000); return f'{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}'
(p/'narration.srt').write_text('\n\n'.join(f"{i+1}\n{stamp(c['narration_start'])} --> {stamp(c['narration_end'])}\n{c['narration_text']}" for i,c in enumerate(man['cues']))+'\n')
print(json.dumps(man,indent=2))
