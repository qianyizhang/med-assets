export const STAGES = ['mechanics', 'airway', 'exchange'];
export const initialState = (language='en') => ({stage:0,language,phase:0,playing:false,gas:'oxygen',elapsed:0,breathClock:0,assets:'loading',error:''});
export function reduce(state, action) {
  switch(action.type) {
    case 'stage': return Number.isInteger(action.value) && action.value>=0 && action.value<3 ? {...state,stage:action.value} : state;
    case 'language': return ['en','zh'].includes(action.value) ? {...state,language:action.value} : state;
    case 'play': return state.assets==='ready' ? {...state,phase:state.phase>=1?0:state.phase,breathClock:state.phase>=1?0:state.breathClock,playing:!state.playing} : state;
    case 'gas': return ['oxygen','carbon-dioxide'].includes(action.value) ? {...state,gas:action.value} : state;
    case 'tick': {const dt=Math.max(0,Math.min(.1,Number.isFinite(action.dt)?action.dt:0));const phase=state.playing?Math.min(1,state.phase+dt/6):state.phase;return {...state,elapsed:state.elapsed+dt,breathClock:state.breathClock+(state.playing?dt:0),phase,playing:state.playing&&phase<1};}
    case 'reset': return {...initialState(state.language),assets:state.assets,error:state.error};
    case 'loaded': return {...state,assets:'ready',error:''};
    case 'failed': return {...state,assets:'error',playing:false,error:String(action.message||'Asset unavailable')};
    case 'retry': return {...state,assets:'loading',error:'',playing:false};
    default: return state;
  }
}
export function breath(state) {
  const p=state.phase, amplitude=(1-Math.cos(p*2*Math.PI))/2;
  const phaseFlow=Math.abs(Math.sin(p*2*Math.PI))<1e-6?0:Math.sin(p*2*Math.PI);
  const flow=state.playing?phaseFlow:0;
  const phaseName=p<=1e-6||p>=1-1e-6?'rest':Math.abs(p-.5)<.015?'peak':!state.playing?'paused':phaseFlow>0?'in':'out';
  return {amplitude,flow,phaseFlow,phaseName,diaphragmDrop:amplitude*.018,
    oxygenDirection:'air-to-blood',carbonDioxideDirection:'blood-to-air',exchangeProgress:(state.elapsed*.18)%1};
}
export const COPY={
 en:{title:'One breath',sub:'Mechanics → airway route → gas exchange',reset:'Reset',language:'中文',stages:['Make space','Follow the air','Across the barrier'],kicker:['01 · MECHANICS','02 · AIRWAY ROUTE','03 · GAS EXCHANGE'],heading:['What draws air in?','One passage, two branches.','Air and blood stay separate.'],body:['The diaphragm contracts downward and the ribs move out. The lungs expand; air flows inward.','Follow the central airway into the two main bronchi. Smaller airways continue toward the alveoli.','Oxygen moves into blood. Carbon dioxide moves into alveolar air across a thin barrier.'],action:['Take one breath','Trace one breath','Trace a gas'],pause:'Pause',resume:'Continue',again:'Another breath',phase:{loading:'Loading models',error:'Models unavailable',unavailable:'3D unavailable',exchange:'Gas exchange',in:'Inhale',out:'Exhale',rest:'At rest',peak:'End of inhale',paused:'Paused'},cue:{unavailable:'Breath motion unavailable',in:'More space → air in',out:'Recoil → air out',rest:'Ready for one breath',peak:'Fuller lungs · flow turns',paused:'Paused within this breath'},source:'Existing source-derived lungs + authored tracheal shell',limit:'Illustrative motion · no measured physiology',diagram:'Authored schematic · not to scale',exchangeNote:'Exchange continues between breaths; both gases move in opposite directions.',alveolus:'Alveolar air',blood:'Capillary blood',barrier:'Thin barrier',oxygen:'Oxygen · O₂',co2:'Carbon dioxide · CO₂',oxygenPath:'Air → blood',co2Path:'Blood → air',trachea:'Trachea',left:'Left main bronchus',right:'Right main bronchus',diaphragm:'Diaphragm guide',ribs:'Rib guides',routeNote:'Central airway only · smaller branches omitted',loading:'Loading the teaching models…',error:'The models could not be loaded.',retry:'Retry assets',fallback:'3D view unavailable. Static offline composition; the exchange schematic remains available.',preview:'Static preview',fallbackMissing:'3D view and offline preview are unavailable. The exchange schematic remains available.',snapshot:'Offline composition · motion unavailable',receipt:'Sources & limits'},
 zh:{title:'一次呼吸',sub:'呼吸力学 → 气道路径 → 气体交换',reset:'重置',language:'EN',stages:['腾出空间','跟随气流','跨越屏障'],kicker:['01 · 呼吸力学','02 · 气道路径','03 · 气体交换'],heading:['空气为什么进入？','一条通道，分为两支。','空气与血液保持分隔。'],body:['膈肌收缩下降，肋骨向外运动。肺随之扩张，空气流入。','沿中央气道进入左右主支气管。更细的气道继续通向肺泡。','氧气进入血液，二氧化碳进入肺泡气体。两者跨越薄的交换屏障。'],action:['体验一次呼吸','追踪一次呼吸','追踪一种气体'],pause:'暂停',resume:'继续',again:'再呼吸一次',phase:{loading:'正在加载模型',error:'模型不可用',unavailable:'三维视图不可用',exchange:'气体交换',in:'吸气',out:'呼气',rest:'静息',peak:'吸气末',paused:'已暂停'},cue:{unavailable:'呼吸运动不可用',in:'空间增大 → 空气流入',out:'弹性回缩 → 空气流出',rest:'准备体验一次呼吸',peak:'肺已扩张 · 气流即将转向',paused:'已暂停当前呼吸'},source:'既有来源肺模型 + 人工构建的气管教学壳体',limit:'示意运动 · 非定量生理模拟',diagram:'人工绘制示意图 · 非等比例',exchangeNote:'两种气体向相反方向移动；呼吸间隙仍在交换。',alveolus:'肺泡气体',blood:'毛细血管血液',barrier:'薄的交换屏障',oxygen:'氧气 · O₂',co2:'二氧化碳 · CO₂',oxygenPath:'空气 → 血液',co2Path:'血液 → 空气',trachea:'气管',left:'左主支气管',right:'右主支气管',diaphragm:'膈肌示意',ribs:'肋骨示意',routeNote:'仅展示中央气道 · 省略更细分支',loading:'正在加载教学模型…',error:'模型加载失败。',retry:'重试加载',fallback:'三维视图不可用。下方为离线静态构图；气体交换示意图仍可使用。',preview:'静态预览',fallbackMissing:'三维视图与离线预览不可用。气体交换示意图仍可使用。',snapshot:'离线静态构图 · 未运行运动',receipt:'来源与限制'}
};

export function fallbackFrame(state){return state.stage===1?'airway':state.phase<=1e-6||state.phase>=1-1e-6?'mechanics-rest':'mechanics-in';}

// Availability takes precedence over breath progress outside the exchange diagram.
export function lessonStatus(state, hasRenderer, previewLoaded=false) {
  const c=COPY[state.language];
  if(state.stage===2)return {phase:c.phase.exchange,cue:state.gas==='oxygen'?c.oxygenPath:c.co2Path};
  if(state.assets==='loading')return {phase:c.phase.loading,cue:c.loading};
  if(state.assets==='error')return {phase:c.phase.error,cue:c.retry};
  if(!hasRenderer)return {phase:previewLoaded?c.preview:c.phase.unavailable,cue:previewLoaded?c.snapshot:c.cue.unavailable};
  const {phaseName}=breath(state);
  return {phase:c.phase[phaseName],cue:c.cue[phaseName]};
}
