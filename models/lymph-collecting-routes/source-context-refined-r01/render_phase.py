from pathlib import Path
import re,json,subprocess
P=Path(__file__).parent;h=(P/'index.html').read_text();images=json.loads(re.search(r'const images=(.*?);const reduced=',h,re.S)[1]);svg=re.search(r'<svg viewBox=.*?</svg>',h,re.S)[0]
for lang,b64 in images.items():
 s=svg.replace('<svg viewBox','<svg xmlns="http://www.w3.org/2000/svg" width="1520" height="1960" viewBox',1)
 s=re.sub(r'href="data:image/png;base64,[^"]*"',f'href="data:image/png;base64,{b64}"',s)
 s=s.replace('class="flow"','stroke="#9df6d5" stroke-width="2.4" stroke-dasharray="5 19" fill="none" opacity="0.82"')
 (P/f'phase-{lang}.svg').write_text(s);subprocess.run(['inkscape',str(P/f'phase-{lang}.svg'),'--export-type=png',f'--export-filename={P}/phase-{lang}.png'],check=True,capture_output=True)
