from pathlib import Path
from html import escape
D=Path(__file__).resolve().parent
C={'en':{'title':'Bile and pancreatic juice: routes to the duodenum','sub':'Duct-network teaching schematic · organ contours and positions simplified','liver':'Liver','liver2':'Produces bile','hepatic':'Right + left hepatic ducts','chd':'Common hepatic duct','gall':'Gallbladder','gall2':'Stores and concentrates bile','cystic':'Cystic duct','cbd':'Common bile duct','pancreas':'Pancreas','pancreas2':'Produces pancreatic juice','pduct':'Pancreatic duct','duo':'Duodenum','duo2':'First part of small intestine','fill':'Filling ↔ emptying','fill2':'Different phases, not simultaneous flow','outlet':'Typical shared terminal junction shown','outlet2':'Duct variants and sphincters omitted','legend1':'Solid blue: bile pathway','legend2':'Dashed blue: pancreatic-juice pathway','limit':'Not to scale; not a procedural map. No duct diameters or individual anatomical pattern implied.','source':'References: NIDDK digestive system · NCI bile-duct anatomy. Original diagram; no source figure copied.'},'zh':{'title':'胆汁与胰液：通向十二指肠的路径','sub':'管道网络教学示意 · 器官轮廓与位置均已简化','liver':'肝 Liver','liver2':'产生胆汁','hepatic':'左、右肝管','chd':'肝总管 Common hepatic duct','gall':'胆囊 Gallbladder','gall2':'储存并浓缩胆汁','cystic':'胆囊管 Cystic duct','cbd':'胆总管 Common bile duct','pancreas':'胰 Pancreas','pancreas2':'产生胰液','pduct':'胰管 Pancreatic duct','duo':'十二指肠 Duodenum','duo2':'小肠的第一段','fill':'充盈 ↔ 排空','fill2':'表示不同阶段，并非同时流动','outlet':'图示典型的共同终末汇合','outlet2':'省略管道变异与括约肌','legend1':'蓝色实线：胆汁路径','legend2':'蓝色虚线：胰液路径','limit':'非等比例，不用于操作定位；不表达管径或个体解剖模式。','source':'参考：NIDDK 消化系统 · NCI 胆管解剖。原创示意图，未复制来源插图。'}}
for lang,c in C.items():
 a=[];add=a.append
 add('''<svg xmlns="http://www.w3.org/2000/svg" width="1400" height="1060" viewBox="0 0 1400 1060" role="img" aria-labelledby="title desc"><defs><marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse"><path d="M0 0L10 5L0 10Z" fill="#76b9f4"/></marker><style>text{font-family:'Noto Sans CJK SC','Noto Sans',sans-serif;fill:#e9edf1}.label{font-size:21px}.small{font-size:17px;fill:#adb7c3}.lead{fill:none;stroke:#71808e;stroke-width:1.5}.duct{fill:none;stroke:#76b9f4;stroke-width:5;stroke-linecap:round;stroke-linejoin:round}.flow{fill:none;stroke:#76b9f4;stroke-width:3;marker-end:url(#arrow)}.organ{fill:#28323c;stroke:#8f9eac;stroke-width:2}</style></defs><rect width="1400" height="1060" fill="#101318"/><rect x="32" y="32" width="1336" height="996" rx="18" fill="#151a20" stroke="#323b46"/>''')
 def t(x,y,s,cl='label',extra=''):add(f'<text x="{x}" y="{y}" class="{cl}" {extra}>{escape(s)}</text>')
 add(f'<title id="title">{escape(c["title"])}</title><desc id="desc">{escape(c["sub"]+". "+c["limit"])}</desc>');t(70,92,c['title'],'title','font-size="28" font-weight="600"');t(70,130,c['sub'],'small');add('<path d="M70 161H1330" stroke="#323b46"/>')
 # Original simplified organ silhouettes; relationships rather than specimen contours.
 add('<path class="organ" d="M315 243 C421 200 589 222 683 245 C756 263 824 267 877 280 C838 327 760 356 695 371 C641 383 595 367 547 376 C466 392 377 397 320 359 C274 327 270 271 315 243Z"/>')
 # Duodenum C-shaped context around pancreatic head; opened top/bottom continuation.
 add('<path d="M620 555 C598 566 577 584 558 661 C539 735 580 799 651 816 C700 828 749 818 785 797" fill="none" stroke="#8998a5" stroke-width="55" stroke-linecap="butt"/><path d="M620 555 C598 566 577 584 558 661 C539 735 580 799 651 816 C700 828 749 818 785 797" fill="none" stroke="#252e37" stroke-width="49"/>')
 # Pancreas lies in the concavity; shape remains illustrative.
 add('<path class="organ" d="M623 627 C653 591 700 599 747 601 C815 585 877 595 935 609 C977 615 1010 620 1041 636 C1024 662 977 678 936 677 C864 688 807 679 750 697 C716 704 692 735 657 727 C625 718 606 670 623 627Z"/>')
 # Gallbladder reservoir and neck joining cystic duct.
 add('<path class="organ" d="M537 432 C524 455 517 478 500 494 C463 512 445 552 461 584 C475 614 509 617 533 595 C558 573 556 540 548 515 C542 488 555 462 561 443Z"/>')
 # Bile duct network: hepatic confluence -> common hepatic -> cystic join -> CBD.
 add('<path class="duct" d="M470 287 C509 314 569 323 650 378 M793 294 C754 323 701 337 650 378 L650 469 L650 627 Q652 666 619 692 L567 713"/>')
 add('<path class="duct" d="M549 443 Q579 466 612 469 L650 469"/>')
 # Pancreatic juice reaches same typical terminal junction, dashed to distinguish origin.
 add('<path d="M999 641 C911 651 824 642 749 665 Q673 675 619 692" fill="none" stroke="#76b9f4" stroke-width="5" stroke-dasharray="10 7" stroke-linecap="round"/>')
 add('<path class="flow" d="M538 323L596 352"/><path class="flow" d="M735 334L686 359"/><path class="flow" d="M650 390V440"/><path class="flow" d="M650 507V565"/><path class="flow" d="M648 634Q646 668 625 686"/><path class="flow" d="M610 696L558 718"/>')
 add('<path class="flow" d="M914 647L857 651"/><path class="flow" d="M746 666L683 682"/>')
 add('<path d="M574 461L620 469" fill="none" stroke="#76b9f4" stroke-width="2.5" marker-start="url(#arrow)" marker-end="url(#arrow)"/>')
 # Clear label leaders.
 t(90,278,c['liver']);t(90,309,c['liver2'],'small');add('<path class="lead" d="M221 274H269L315 284"/>')
 t(956,278,c['hepatic']);add('<path class="lead" d="M938 272H876L788 298"/>')
 t(956,400,c['chd']);add('<path class="lead" d="M938 394H842L652 415"/>')
 t(956,474,c['cystic']);add('<path class="lead" d="M938 468H841L611 469"/>')
 t(956,547,c['cbd']);add('<path class="lead" d="M938 541H839L652 553"/>')
 t(90,528,c['gall']);t(90,559,c['gall2'],'small');add('<path class="lead" d="M315 522H380L461 550"/>')
 t(90,639,c['fill'],'small');t(90,669,c['fill2'],'small');add('<path class="lead" d="M368 632L417 610L579 466"/>')
 t(956,735,c['pduct']);add('<path class="lead" d="M939 729H887L818 650"/>')
 t(956,804,c['pancreas']);t(956,835,c['pancreas2'],'small');add('<path class="lead" d="M938 798H901L910 673"/>')
 t(90,802,c['duo']);t(90,834,c['duo2'],'small');add('<path class="lead" d="M343 796H431L555 750"/>')
 # Common outlet explicitly typical; no universal junction assertion.
 t(470,883,c['outlet'],'small');t(470,910,c['outlet2'],'small');add('<path class="lead" d="M605 860L606 779L619 692"/>')
 add('<path d="M75 951H135" class="duct"/>');t(151,957,c['legend1'],'small');add('<path d="M640 951H700" class="duct" stroke-dasharray="10 7"/>');t(716,957,c['legend2'],'small');t(70,990,c['limit'],'small');t(70,1018,c['source'],'small')
 add('</svg>');(D/f'biliary-pathways-{lang}.svg').write_text(''.join(a))
