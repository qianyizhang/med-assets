"""Original procedural score; no samples, external music, or generated speech."""
import numpy as np, wave, json
from pathlib import Path
P=Path(__file__).parent; SR=48000; DUR=48; N=SR*DUR
rng=np.random.default_rng(271828)
y=np.zeros((N,2),dtype=np.float64)
def hz(m): return 440*2**((m-69)/12)
def add(start, s, pan=0):
    i=int(start*SR); j=min(N,i+len(s)); s=s[:j-i]
    if len(s): y[i:j,0]+=s*np.sqrt((1-pan)/2); y[i:j,1]+=s*np.sqrt((1+pan)/2)
def pad(start,dur,notes,gain=.035):
    t=np.arange(int(dur*SR))/SR
    env=np.minimum(1,t/1.6)*np.minimum(1,(dur-t)/1.8)
    for k,m in enumerate(notes):
        f=hz(m); s=np.zeros(len(t))
        for detune in [-.0018,0,.0018]:
            s+=np.sin(2*np.pi*f*(1+detune)*t + .12*np.sin(2*np.pi*.13*t+k))
        s/=3
        s+=.12*np.sin(2*np.pi*f*2*t)
        s*=env*gain*(.88+.12*np.sin(2*np.pi*.16*t+k))
        add(start,s,(k-(len(notes)-1)/2)*.28)
def bell(start,m,gain=.055,pan=0,dur=2.8):
    t=np.arange(int(dur*SR))/SR; f=hz(m)
    s=(np.sin(2*np.pi*f*t)*np.exp(-t/1.25)+.28*np.sin(2*np.pi*f*2.01*t)*np.exp(-t/.48)+.1*np.sin(2*np.pi*f*3.99*t)*np.exp(-t/.17))
    s*=gain*np.minimum(1,t/.008)*np.minimum(1,(dur-t)/.3)
    add(start,s,pan)
    add(start+.19,s*.20,-pan)
def pulse(start,m,gain=.045):
    t=np.arange(int(.7*SR))/SR
    s=np.sin(2*np.pi*hz(m)*t)*np.exp(-t/.22)*np.minimum(1,t/.025)*gain
    add(start,s)
def air(at,dur=1.3,gain=.04):
    t=np.arange(int(dur*SR))/SR
    noise=rng.standard_normal(len(t)); noise=np.convolve(noise,np.ones(21)/21,mode='same')
    env=np.sin(np.pi*t/dur)**2
    add(at,noise*env*gain,-.3); add(at+.035,noise*env*gain,.3)
# Continuous harmonic arc: mystery, pressure, repair, tipping point, repair, prevention.
scenes=[(0,6,[50,57,64,69]),(6,8,[46,53,60,65]),(14,9,[48,55,62,67]),(23,8,[45,52,59,64]),(31,9,[48,55,60,64]),(40,8,[48,55,62,64,67])]
for start,dur,notes in scenes: pad(max(0,start-.65),dur+1.25,notes,.031 if start!=23 else .026)
for at,m,pan in [(0.3,81,-.25),(2.5,76,.25),(4.15,74,-.1),(6.2,77,-.4),(8.1,72,.3),(10.2,70,-.25),(12.25,65,.3),(14.3,79,-.35),(16.2,74,.35),(18.4,76,-.15),(20.7,79,.25),(23.3,71,-.3),(25.4,64,.25),(28.1,69,-.2),(31.3,76,.3),(33.1,79,-.3),(35.35,84,.2),(37.55,79,-.15),(40.3,79,-.3),(42.2,81,.3),(44.2,84,-.1),(46,79,.2)]: bell(at,m,.045,pan)
for at in np.arange(6.25,13.5,1): pulse(at,34,.034)
for at in np.arange(23.25,30,1.2): pulse(at,33,.028)
for at in [5.45,13.45,22.45,30.45,39.45]: air(at)
# Final soft resolution and ending tail.
bell(45.1,72,.025,-.25); bell(45.2,76,.025,.25)
y*=np.minimum(1,np.arange(N)/SR/1.2)[:,None]
y*=np.minimum(1,(DUR-np.arange(N)/SR)/2.2)[:,None]
y=np.tanh(y*1.5)/1.5
with wave.open(str(P/'score-raw.wav'),'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(y,-1,1)*32767).astype('<i2').tobytes())
manifest={'title':'The Balance: Voice Cues and Original Underscore','duration_seconds':48,'sample_rate':48000,'channels':2,'spoken_narration':True,'license':'Original procedural composition created for this project; no third-party samples.','mix_note':'Generate the original underscore, then synthesize these scene-timed narration cues and mix the stems.','cues':[]}
texts=[('Mystery','Tooth decay starts before a hole. What tips the balance?'),('Acid pressure','Some bacteria in plaque use sugars to make acids. Repeated exposure can keep enamel losing minerals.'),('Repair response','Saliva and fluoride help replace lost minerals. Early decay can sometimes be stopped or reversed before a cavity forms.'),('Threshold','If loss keeps winning, the surface can break down. A formed cavity needs dental assessment and appropriate treatment.'),('Restoration','A dentist assesses the tooth and selects treatment. A filling is one common way to restore damaged structure.'),('Prevention','The long game is prevention: fluoride toothpaste twice daily, cleaning between teeth, and regular dental review.')]
for (start,dur,_),(title,txt) in zip(scenes,texts): manifest['cues'].append({'start':start,'end':start+dur,'title':title,'narration_text':txt})
(P/'cue-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
