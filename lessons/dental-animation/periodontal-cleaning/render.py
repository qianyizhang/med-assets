"""Patient-education storyboard. Authored vector schematic, not clinical anatomy."""
from pathlib import Path
import math, io, json
OUT=Path(__file__).resolve().parent/'output'
W,H,FPS,N=960,540,12,144
TOOTH='M292 142 C280 118 304 99 330 114 C353 125 369 123 390 112 C417 99 440 116 428 146 L412 224 C405 261 399 311 389 364 C379 418 365 448 358 427 C350 400 342 363 335 327 C325 275 313 239 307 210 Z'
DEPOSITS=[(310,195,5),(314,215,6),(319,236,5),(325,257,7),(331,282,5),(337,304,6),(405,241,6),(400,265,7),(395,286,5),(390,307,6)]
HEAD=['Plaque can harden into tartar','Look below the gumline','Professional cleaning','Reassess and maintain']
BODY=[['Deposits can collect around teeth.','The amber marks are illustrative.'],['A cutaway makes the story clear.','Pocket geometry is schematic.'],['Deposits fade in this timing test.','No instrument technique is shown.'],['Keep the supporting tissues fixed.','Recheck healing after treatment.']]
def ease(t):t=max(0,min(1,t));return t*t*(3-2*t)
def render(f):
 t=f/FPS; stage=min(int(t/3),3); clean=ease((t-6)/2.7)
 deposits=''.join(f'<ellipse cx="{x}" cy="{y}" rx="{r}" ry="{r*1.5}" fill="#e6ae4a" stroke="#966122" stroke-width="1.5" opacity="{max(0,min(1,1-clean*1.8+i*.08)):.3f}"/>' for i,(x,y,r) in enumerate(DEPOSITS))
 marker=''
 if stage==2:
  cy=315-125*clean
  marker=f'<ellipse cx="358" cy="{cy}" rx="70" ry="18" fill="none" stroke="#71d6cf" stroke-width="3" stroke-dasharray="6 5"/><text x="90" y="425" fill="#71d6cf" font-size="14">Animated cleaning zone, not a tool trajectory</text>'
 labels=''
 if stage>=1:
  labels='<path d="M208 199 L280 199 L307 214" fill="none" stroke="#f1c06f"/><text x="83" y="194" fill="#f1c06f" font-size="16">Illustrative tartar</text><path d="M444 270 L493 256" stroke="#f09a9e" fill="none"/><text x="443" y="248" fill="#f09a9e" font-size="15">Gum cutaway</text>'
 if stage==3: labels='<text x="146" y="433" fill="#b4c7cd" font-size="15">No instant gum or bone regrowth is implied</text>'
 svg=f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
 <defs><linearGradient id="tooth" x1="0" x2="1"><stop stop-color="#ecdfc5"/><stop offset=".5" stop-color="#fff7df"/><stop offset="1" stop-color="#cfbd98"/></linearGradient><linearGradient id="gum" x1="0" x2="1"><stop stop-color="#bf6677"/><stop offset="1" stop-color="#e8a0a5"/></linearGradient><radialGradient id="bg"><stop stop-color="#213e4b"/><stop offset="1" stop-color="#132a35"/></radialGradient></defs>
 <rect width="960" height="540" fill="#10242e"/><rect x="24" y="84" width="548" height="390" rx="22" fill="url(#bg)"/>
 <text x="30" y="35" fill="#73d5cf" font-size="13" font-family="DejaVu Sans" letter-spacing="2">DENTAL / ANIMATION STUDY 03</text><text x="30" y="66" fill="#f1f0e8" font-size="26" font-weight="bold" font-family="DejaVu Sans">Why professional cleaning reaches deeper</text>
 <ellipse cx="360" cy="449" rx="135" ry="12" fill="#0c1e27" opacity=".55"/>
 <path d="M222 287 C255 267 279 282 299 302 L324 433 L273 445 L222 431 Z" fill="#827c65"/><path d="M425 302 C452 283 475 280 508 294 L505 433 L406 440 Z" fill="#827c65"/>
 <path d="{TOOTH}" fill="url(#tooth)" stroke="#c9bca0" stroke-width="1.8"/>
 <path d="M224 241 C263 213 281 202 301 235 C312 254 319 280 329 330 L310 437 L223 435 Z" fill="url(#gum)" opacity=".94"/>
 <path d="M420 239 C437 203 461 214 507 239 L505 436 L405 439 L399 335 C409 286 416 264 420 239 Z" fill="url(#gum)" opacity=".94"/>
 <path d="M301 234 C309 254 320 286 329 331 M420 239 C414 265 405 298 399 335" fill="none" stroke="#f3b2b1" stroke-width="4"/>
 {deposits}{marker}{labels}
 <text x="602" y="117" fill="#72d5ce" font-size="13" font-family="DejaVu Sans">SHOT {stage+1:02d} / 04</text>
 <text x="602" y="157" fill="#f1f0e8" font-size="19" font-weight="bold" font-family="DejaVu Sans">{HEAD[stage]}</text>
 <text x="602" y="198" fill="#bbccd1" font-size="15" font-family="DejaVu Sans"><tspan x="602">{BODY[stage][0]}</tspan><tspan x="602" dy="26">{BODY[stage][1]}</tspan></text>
 <line x1="602" x2="925" y1="255" y2="255" stroke="#39535f"/>
 <text x="602" y="291" fill="#e9b461" font-size="13" font-family="DejaVu Sans">SCHEMATIC ANATOMY</text><text x="602" y="317" fill="#b4c7cd" font-size="14" font-family="DejaVu Sans"><tspan x="602">Patient-education pacing test.</tspan><tspan x="602" dy="24">Not an operative training guide.</tspan><tspan x="602" dy="24">Clinical review still required.</tspan></text>
 <text x="602" y="422" fill="#7d9da9" font-size="12" font-family="DejaVu Sans">Evidence: NIDCR / ADA patient guidance</text>
 <rect x="30" y="489" width="900" height="3" rx="1.5" fill="#29434f"/><rect x="30" y="489" width="{900*t/12}" height="3" rx="1.5" fill="#73d5cf"/>
 <text x="30" y="519" fill="#89a4af" font-size="12" font-family="DejaVu Sans">Concept-only deposits and tissue relationships • Assessment → professional care → follow-up</text><text x="870" y="519" fill="#89a4af" font-size="12" font-family="DejaVu Sans">{t:04.1f} / 12s</text></svg>'''
 return svg
def main():
    import cairosvg
    from PIL import Image
    OUT.mkdir(exist_ok=True)
    frames=[]
    for f in range(N):
     svg=render(f)
     im=Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode()))).convert('RGB');frames.append(im)
     if f in (0,42,86,130):im.save(OUT/f'periodontal-shot-{f//36+1}.png')
    frames[0].save(OUT/'periodontal-cleaning-schematic.gif',save_all=True,append_images=frames[1:],duration=[80 if i%3 else 90 for i in range(N)],loop=0,optimize=True)
    (OUT/'periodontal-poster.svg').write_text(render(42))
    (OUT/'periodontal-manifest.json').write_text(json.dumps({'kind':'authored vector schematic','frames':N,'fps':FPS,'duration_seconds':12,'anatomy':'not validated','unchanged_support':'bone and gum shapes constant in every frame','motion':'concept zone only; no instrument technique','source_guidance':['https://www.nidcr.nih.gov/health-info/gum-disease','https://www.mouthhealthy.org/all-topics-a-z/scaling-and-root-planing']},indent=2))
    print(OUT/'periodontal-cleaning-schematic.gif')

if __name__ == '__main__':
    main()
