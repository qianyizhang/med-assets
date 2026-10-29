import {COPY,breath} from './state.mjs';
export function exchangeSVG(state){
 const c=COPY[state.language],b=breath(state),oxy=state.gas==='oxygen',amp=b.amplitude;
 const active=oxy?'#e5b76b':'#78d5d3',oOpacity=oxy?1:.35,cOpacity=oxy?.35:1;
 const oy=239+88*b.exchangeProgress,cy=327-88*b.exchangeProgress;
 return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 510" role="img" aria-label="${c.diagram}"><defs><marker id="arrowO" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto"><path d="M0 0L8 4L0 8" fill="#e5b76b"/></marker><marker id="arrowC" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto"><path d="M0 0L8 4L0 8" fill="#78d5d3"/></marker></defs>
 <rect x="24" y="20" width="712" height="467" rx="26" fill="#193840" stroke="#769095" stroke-dasharray="7 7"/>
 <text x="380" y="57" text-anchor="middle" fill="#b7cccf" font-size="16">${c.diagram}</text>
 <path d="M316 90V117 C245 102 170 ${125-amp*5} 168 203 Q165 272 280 278H480Q590 274 592 206Q590 104 444 117V90" fill="#6f4f4b" stroke="#e3ad98" stroke-width="4"/>
 <text x="380" y="182" text-anchor="middle" fill="#fff2e4" font-size="24">${c.alveolus}</text>
 <rect x="134" y="292" width="492" height="91" rx="45" fill="#395e79" stroke="#8db3c6" stroke-width="3"/>
 <path d="M380 294H579Q625 294 625 338Q625 383 579 383H380" fill="#825552" opacity=".8"/>
 <path d="M195 285H566" stroke="#f8e1bb" stroke-width="3"/>
 <text x="380" y="423" text-anchor="middle" fill="#c7dce0" font-size="22">${c.blood}</text>
 <text x="631" y="278" text-anchor="end" fill="#e1d4bb" font-size="15">${c.barrier}</text>
 <g opacity="${oOpacity}"><path d="M315 218V345" fill="none" stroke="#e5b76b" stroke-width="5" marker-end="url(#arrowO)"/><circle cx="315" cy="${oy}" r="9" fill="#e5b76b"/><text x="284" y="231" text-anchor="end" fill="#f3d49b" font-size="22">O₂</text></g>
 <g opacity="${cOpacity}"><path d="M455 350V226" fill="none" stroke="#78d5d3" stroke-width="5" marker-end="url(#arrowC)"/><circle cx="455" cy="${cy}" r="9" fill="#78d5d3"/><text x="480" y="247" fill="#b5efeb" font-size="22">CO₂</text></g>
 <g fill="#c88e88" stroke="#e1aaa0" stroke-width="2"><ellipse cx="204" cy="339" rx="21" ry="12"/><ellipse cx="548" cy="339" rx="21" ry="12"/></g>
 <text x="380" y="459" text-anchor="middle" fill="${active}" font-size="18">${oxy?c.oxygenPath:c.co2Path}</text></svg>`;
}
