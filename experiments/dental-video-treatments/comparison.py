#!/usr/bin/env python3
"""Rebuild a synchronized overview from the three retained final movies."""
import argparse
from pathlib import Path
import subprocess
from replay import ROOT, check_payloads

def command(output):
    output=Path(output).resolve()
    if output.exists():
        raise ValueError('Use a new output filename; retained results are never overwritten')
    check_payloads()
    films=[('HyperFrames','Before the hole','hyperframes.mp4'),('Remotion','The Decay File','remotion.mp4'),('ManimGL','The Mineral Ledger','manimgl.mp4')]
    args=['ffmpeg','-hide_banner','-loglevel','error','-filter_complex_threads','2']
    for _,_,name in films:args+=['-threads','2','-i',str(ROOT/'results'/name)]
    regular=(ROOT/'fonts/DejaVuSans.ttf').as_posix();bold=(ROOT/'fonts/DejaVuSans-Bold.ttf').as_posix()
    filters=[]
    for i,(engine,title,_) in enumerate(films):
        filters.append(f'[{i}:v]scale=640:360,pad=640:440:0:52:color=0x10232a,drawtext=fontfile={bold}:text={engine}:fontsize=22:fontcolor=white:x=20:y=15,drawtext=fontfile={regular}:text={title}:fontsize=14:fontcolor=0xa6c7c2:x=20:y=419[v{i}]')
    filters.append('[v0][v1][v2]hstack=inputs=3[v]')
    return args+['-filter_complex',';'.join(filters),'-map','[v]','-map','0:a:0','-c:v','libx264','-threads','2','-preset','fast','-crf','20','-c:a','copy','-t','48','-movflags','+faststart',str(output)]
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    cmd=command(a.output);a.output.parent.mkdir(parents=True,exist_ok=True);subprocess.run(cmd,check=True)
