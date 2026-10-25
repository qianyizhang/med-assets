from pathlib import Path
from html import escape
D=Path(__file__).resolve().parent
copy={
'en':{'title':'Testis → epididymis → ductus deferens','sub':'Sectional teaching schematic · relationships and flow, not specimen geometry','top':'SUPERIOR','bottom':'INFERIOR','ant':'ANTERIOR','post':'POSTERIOR','testis':'Inside the testis','cap':'Tunica albuginea','lob':'Symbolic lobules','tub':'Coiled seminiferous tubules','straight':'Straight tubules (tubuli recti)','rete':'Rete testis','mediast':'Within posterior mediastinum','eff':'Efferent ductules','epi':'Outside the testis','head':'Head of epididymis','body':'Body of epididymis','tail':'Tail of epididymis','vas':'Ductus deferens','vas2':'Ascends from the tail','hint':'Blue arrows: sperm transport direction','limit':'Not to scale. Coils, lobules and duct counts are symbolic. No lumen diameter or clinical geometry implied.','flow':'TRANSPORT PATH','route':['Seminiferous tubules','Straight tubules → rete','Efferent ductules','Head → body → tail','Ductus deferens'],'source':'References: NCI SEER · OpenStax Anatomy & Physiology 2e §27.1. Original diagram; no source figure copied.'},
'zh':{'title':'睾丸 → 附睾 → 输精管','sub':'剖面教学示意 · 表达结构关系与流向，不代表标本几何形态','top':'上方 SUPERIOR','bottom':'下方 INFERIOR','ant':'前方 ANTERIOR','post':'后方 POSTERIOR','testis':'睾丸内部','cap':'白膜 Tunica albuginea','lob':'示意小叶','tub':'卷曲的生精小管','straight':'生精直小管 (tubuli recti)','rete':'睾丸网 Rete testis','mediast':'位于后部睾丸纵隔内','eff':'睾丸输出小管','epi':'睾丸外部','head':'附睾头 Head','body':'附睾体 Body','tail':'附睾尾 Tail','vas':'输精管 Ductus deferens','vas2':'由附睾尾延续并向上走行','hint':'蓝色箭头：精子输送方向','limit':'非等比例。卷曲、小叶和管道数量均为示意；不表达管腔直径或临床几何精度。','flow':'输送路径','route':['生精小管','生精直小管 → 睾丸网','睾丸输出小管','附睾头 → 体 → 尾','输精管'],'source':'参考：NCI SEER · OpenStax Anatomy & Physiology 2e §27.1。原创示意图，未复制来源插图。'}}
for lang,c in copy.items():
 a=[];add=a.append
 add('''<svg xmlns="http://www.w3.org/2000/svg" width="1400" height="1060" viewBox="0 0 1400 1060" role="img" aria-labelledby="title desc"><defs><marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10Z" fill="#76b9f4"/></marker><style>text{font-family:'Noto Sans CJK SC','Noto Sans',sans-serif;fill:#e9edf1} .small{font-size:17px;fill:#a7b0bb} .label{font-size:21px} .section{font-size:16px;letter-spacing:1.7px;fill:#a7b0bb} .lead{fill:none;stroke:#697582;stroke-width:1.5} .flow{fill:none;stroke:#76b9f4;stroke-width:3;marker-end:url(#arrow)} .tube{fill:none;stroke:#76b9f4;stroke-width:4;stroke-linecap:round;stroke-linejoin:round}</style></defs><rect width="1400" height="1060" fill="#101318"/><rect x="32" y="32" width="1336" height="996" rx="18" fill="#151a20" stroke="#323b46"/>''')
 def text(x,y,t,cl='label',extra=''):add(f'<text x="{x}" y="{y}" class="{cl}" {extra}>{escape(t)}</text>')
 add(f'<title id="title">{escape(c["title"])}</title><desc id="desc">{escape(c["sub"]+". "+c["limit"])}</desc>')
 text(70,95,c['title'],'title',extra='font-size="28" font-weight="600"');text(70,132,c['sub'],'small');add('<path d="M70 162H1330" stroke="#323b46"/>')
 text(620,203,c['top'],'small','text-anchor="middle"');text(620,831,c['bottom'],'small','text-anchor="middle"');text(385,230,c['ant'],'section');text(850,230,c['post'],'section')
 # Testis cutaway: internal posterior mediastinum remains inside capsule.
 add('<path d="M590 260 C475 260 404 350 403 493 C396 657 458 778 575 784 C681 790 748 709 754 566 C763 401 712 268 590 260Z" fill="#252e37" stroke="#a6b2bd" stroke-width="5"/>')
 add('<path d="M700 380 C729 418 739 505 725 624 L698 646 C712 534 708 456 687 410Z" fill="#45515d" stroke="#758493" stroke-width="1.5"/>')
 # Few symbolic septa, not an anatomical lobule count.
 for path in ['M701 425 Q574 373 458 359','M708 479 Q545 450 413 462','M714 536 Q552 549 412 584','M712 588 Q556 660 466 733']:
  add(f'<path d="{path}" fill="none" stroke="#506171" stroke-width="2"/>')
 # Three illustrative convoluted tubules connect by straighter portions into rete.
 for path in ['M513 339 C470 329 478 384 518 372 S555 319 532 337 S514 394 560 388 S591 349 570 354 S565 410 606 402 S636 372 623 383 L696 434','M468 490 C439 465 439 530 474 517 S510 468 484 481 S474 539 516 532 S557 480 530 492 S525 548 568 535 S602 490 582 505 L710 507','M496 631 C465 609 468 671 500 659 S539 611 514 623 S510 687 550 670 S585 623 567 641 L708 581']:
  add(f'<path class="tube" d="{path}"/>')
 add('<path class="flow" d="M645 507L687 507"/><path class="flow" d="M630 614L676 594"/>')
 # rete network posterior; deliberately schematic branching.
 add('<path class="tube" d="M696 434 L717 455 L699 481 L720 507 L703 533 L720 557 L708 581 M696 434 L699 481 L703 533 L708 581 M717 455 L720 507 L720 557"/>')
 # epididymis head, body, tail: a continuous external envelope, not a coiled-lumen model.
 add('<path d="M701 278 C745 248 790 280 805 325 C816 354 799 382 794 410 C797 481 808 558 801 626 C797 677 788 703 786 724 C803 724 821 742 814 762 C804 790 768 792 751 772 C736 753 748 729 759 712 C772 683 776 654 777 621 C784 548 770 475 770 412 C764 383 738 373 728 348 C716 321 704 304 701 278Z" fill="#4c555e" stroke="#a5afb8" stroke-width="3"/>')
 # efferent ductules pass from rete through posterior capsule to superior head.
 for path in ['M696 434 Q716 374 749 329','M706 434 Q733 383 760 337','M717 435 Q748 395 770 344']:
  add(f'<path class="tube" d="{path}"/>')
 add('<path class="flow" d="M731 386L753 348"/>')
 # transport indication through epididymis, then tail-to-vas ascent outside testis
 add('<path class="flow" d="M759 336 Q793 371 784 427 L790 492"/><path class="flow" d="M790 536 Q792 645 778 706"/><path class="flow" d="M778 732 Q766 767 794 763 Q827 756 844 706"/>')
 add('<path d="M802 763 C845 746 858 682 860 604 L875 298" fill="none" stroke="#a5afb8" stroke-width="19" stroke-linecap="round"/>')
 add('<path class="flow" d="M802 763 C845 746 858 682 860 604 L864 544"/><path class="flow" d="M868 468 L874 315"/>')
 # Labels and leader lines avoid traversing structures.
 text(78,286,c['testis'],'section');text(78,334,c['cap'] if lang=='en' else '白膜');text(78,361,'' if lang=='en' else 'Tunica albuginea','small');add('<path class="lead" d="M295 328H357L422.33 379"/>')
 text(78,419,c['lob']);add('<path class="lead" d="M270 413H360L465 409"/>')
 text(78,495,'Seminiferous tubules' if lang=='en' else c['tub']);text(78,522,'Coiled · symbolic' if lang=='en' else '卷曲仅作示意','small');add('<path class="lead" d="M313 500H367L464 503"/>')
 text(78,688,'Straight tubules' if lang=='en' else '生精直小管');text(78,718,'(tubuli recti)','small');add('<path class="lead" d="M332 682H365L637 612"/>')
 text(78,580,c['rete']);text(78,608,c['mediast'],'small');add('<path class="lead" d="M302 574H360L703 560"/>')
 text(987,266,c['epi'],'section');text(987,292,'Envelope; duct coils omitted' if lang=='en' else '外形轮廓；省略内部管道卷曲','small');text(987,336,c['head']);add('<path class="lead" d="M970 330H920L804 324"/>')
 text(987,420,c['eff']);add('<path class="lead" d="M970 414H928L755 385"/>')
 text(987,504,c['body']);add('<path class="lead" d="M970 498H930L803 511"/>')
 text(987,606,c['vas']);text(987,637,c['vas2'],'small');add('<path class="lead" d="M970 600H930L862 600"/>')
 text(987,745,c['tail']);add('<path class="lead" d="M970 739H922L815 757"/>')
 text(987,805,c['hint'],'small')
 # Path summary; labels are also spelled out above.
 add('<rect x="70" y="863" width="1260" height="100" rx="10" fill="#1c232b" stroke="#323b46"/>');text(88,889,c['flow'],'section')
 for i,t in enumerate(c['route']):
  x=92+i*248;text(x,929,t,'small')
  if i<4:text(x+223,929,'→',extra='font-size="20" fill="#76b9f4"')
 text(70,991,c['limit'],'small');text(70,1018,c['source'],'small',extra='font-size="14"')
 add('</svg>');(D/f'testis-pathway-{lang}.svg').write_text(''.join(a))
