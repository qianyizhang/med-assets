import { add, calibratedShape, landmarks, mean, mul, sub, unit, volumeFor } from './playable-model.js';

const AXIAL = { beam: [0,-1,0], width: [1,0,0], name: 'Transverse' };
const SAGITTAL = { beam: [0,-1,0], width: [0,0,1], name: 'Sagittal' };
const CORONAL = { beam: [0,-.06,-1], width: [1,0,0], name: 'Coronal' };
const EARLY_CR = ['embryo', 'yolk_sac'];
const HEART_LABELS = ['right_atrium', 'left_atrium', 'right_ventricle', 'left_ventricle'];

export function chapters(record) {
  const stage = record.family.replace('pregnancy-', '');
  const kind = record.kind;
  const l = landmarks(stage, kind);
  const shape = calibratedShape(stage, kind);
  const output = [];
  let source;
  const views = title => {
    source = record.views.find(entry => entry.title === title);
    if (!source) throw new Error(`Missing worked view ${record.id}: ${title}`);
  };
  const chapter = (id, title, target, plane, span, observation, options = {}) => {
    const frames = options.signal ? (options.signal.mode === 'M-mode' ? 39 : 43) : 17;
    const evidenceFrame = options.signal ? frames-1 : (options.evidenceFrame ?? 8);
    output.push({
      ...plane, ...options, id, title, target, span, frames, evidenceFrame, observation,
      stage, kind, viewImage: source.image,
    });
  };
  const memory = sourceTitle => record.views.find(entry=>entry.title===sourceTitle)?.measurement;
  const shadow = (target, shift = 0, width = 7) => ({ target, shift, width });
  const length = (a,b,label) => ({ type: 'line', a,b,label });
  const crl = () => length(l.crown,l.rump,`CRL ${shape.crl} mm`);
  const signal = (mode, cycles, seconds, peak, edv, interrupted) => ({ mode, cycles, seconds, peak, edv, interrupted });
  const mmode = (id, title, target, plane, span, cycles, seconds, measurement, extra={}) =>
    chapter(id,title,target,plane,span,'The M-line intersects the moving cardiac interface. Measure between like phases across the complete trace.', {
      ...extra, signal: signal('M-mode',cycles,seconds), measurement,
    });
  const addLimbs = (limbs, mid) => {
    for (const [index, nodes] of limbs.entries()) {
      const [proximal, joint, terminal, digit] = nodes;
      const name = ['Right arm','Left arm','Right leg','Left leg'][index];
      const side = index % 2 ? 'left' : 'right';
      const surface = index < 2 ? 'hand' : 'foot';
      const labels = mid ? ['forearm / lower-leg bones'] : ['fetus'];
      chapter(`limb-${index}`,name,mean(proximal, terminal),{
        ...AXIAL, width: unit(sub(terminal,proximal)), name:'Oblique long axis',
      },mid?80:38,`Trace the ${name.toLowerCase()} from its proximal segment past the joint to the paired distal shafts.`,{
        span:mid?80:42, sweep:mid?9:5, labels, pathLine: [proximal,joint,terminal],
      });
      if (mid) chapter(`${side}-${surface}`,`${side==='right'?'Right':'Left'} ${surface}`,digit,
        { ...CORONAL, width:unit(sub(digit,terminal)), name:'Distal long axis' },44,
        `Resolve the ${surface} beyond the distal limb and trace its digital echoes.`, {
          sweep:8, labels: [surface==='hand'?'hands':'feet'],
        });
    }
  };

  if (stage === 'early') {
    const transvaginal = { vaginal: true };
    if (kind === 'normal') {
      views('Locate the sac');
      chapter('ta-orientation','Transabdominal uterine orientation',[0,-12,-8],SAGITTAL,112,
        'A full bladder provides an anterior window to the uterine cavity and then the gestational sac.', {
          overview:true, labels:['maternal_bladder','uterus','gestational_rim'],
        });
      chapter('tv-location','Transvaginal gestational sac',[3.6,-9,-.4],SAGITTAL,43,
        'A yolk sac and embryo in the intrauterine gestational sac establish location.', {
          ...transvaginal, labels:['gestational_rim','yolk_sac','embryo'],
        });
      chapter('tv-crl','Embryonic crown–rump length',mean(l.crown,l.rump),SAGITTAL,29,
        'The longest usable longitudinal embryonic section supports the crown-to-rump measurement.', {
          ...transvaginal, labels:EARLY_CR, measure:crl(), measurement:source.measurement,
        });
      views('Document cardiac activity');
      mmode('embryonic-mmode','Embryonic cardiac M-mode',l.heart,SAGITTAL,30,3,1.25,source.measurement,transvaginal);
      views('Check adnexa and cul-de-sac');
    } else {
      views(kind==='abnormal'?'Sweep uterine cavity':'Check cavity and adnexa');
      chapter('ta-orientation','Transabdominal uterine orientation',[0,-14,-12],SAGITTAL,120,
        'Survey the filled bladder, uterus and expected sac location. Continue transvaginally because the initial uterine view has no established sac.', {
          overview:true, labels:['maternal_bladder','uterus'],
        });
      chapter('tv-location','Transvaginal uterine cavity',l.uterus,SAGITTAL,81,
        'The uterine cavity has no probable or definite pregnancy in the visible field.', {
          ...transvaginal, labels:['uterus'],
        });
    }
    chapter('left-adnexa','Left adnexal sweep',l.left,AXIAL,54,
      'Follow the left ovary and visible adjacent region. The modeled follicles lie within the ovary.', {
        ...transvaginal, labels:['ovary','adnexal follicles'],
      });
    if (kind === 'abnormal') views('Localize the right adnexal sac');
    if (kind === 'limited') views('Repeat right adnexal view');
    const rightAim = kind==='abnormal'?mean(l.right,l.ectopic):l.right;
    chapter('right-adnexa','Right adnexal sweep',rightAim,AXIAL,55,
      kind==='abnormal'?'Identify the ovary separately from the extraovarian sac and its yolk sac.'
        :kind==='limited'?'Bowel shadow interrupts the far right adnexal field before the sweep clears it.'
          :'Follow the right ovary and visible adjacent tissues without an extraovarian sac.', {
        ...transvaginal, labels:kind==='abnormal'?['ovary','tubal wall','ectopic yolk sac']:['ovary','adnexal follicles'],
        shadow:kind==='limited'?shadow(l.right,5,10):undefined,
      });
    if (kind === 'abnormal') {
      chapter('tubal-measure','Right extraovarian sac and yolk sac',l.ectopic,AXIAL,36,
        'The bright-walled structure contains its own yolk sac and remains distinct from the ovary on the adjacent sweep.', {
          ...transvaginal, labels:['tubal wall','tubal sac','ectopic yolk sac'],
          measure:length(add(l.ectopic,[-9,0,0]),add(l.ectopic,[9,0,0]),'18 mm'),
          measurement:source.measurement,
        });
    }
    if (kind === 'limited') {
      chapter('right-adnexal-repeat','Right adnexa · repeat oblique window',add(l.right,[4,-2,1]),{
        ...AXIAL, width:[1,0,.38], name:'Repeat oblique',
      },54,'A separate beam approaches the ovary after position change. Residual posterior shadow still limits exclusion of a right adnexal finding.', {
        ...transvaginal, sweep:9, shadow:shadow(l.right,6,8), labels:['ovary','adnexal follicles'],
        measurement:source.measurement,
      });
    }
    chapter('posterior-pelvis','Cul-de-sac and cervix',l.pouch,CORONAL,69,
      kind==='abnormal'?'Trace free fluid behind the cervix in the posterior cul-de-sac.':'Survey the visible posterior cul-de-sac and cervix.', {
        ...transvaginal, labels:kind==='abnormal'?['uterus','cul-de-sac fluid']:['uterus'],
      });
    return output;
  }

  if (stage === 'first') {
    views('Count fetuses and date by CRL');
    chapter('plurality','Fetal number and uterine contents',[0,1,10],SAGITTAL,113,
      'Sweep through the whole sac before magnification. This modeled pregnancy has one fetus in the visualized cavity.', {
        overview:true, sweep:37, labels:['amniotic_fluid','fetus','placenta'],
      });
    chapter('crl','Neutral midsagittal crown–rump length',mean(l.crown,l.rump),SAGITTAL,88,
      'The neutral midsagittal profile excludes limb tips. Measure the longitudinal crown-to-rump span in the saved plane.', {
        sweep:10, labels:['fetus','nasal_bone'], measure:crl(), measurement:source.measurement,
      });
    views(kind === 'limited' ? 'Attempt and repeat nuchal plane' : 'Magnify the nuchal region');
    if (kind === 'limited') {
      chapter('nt-initial','Nuchal profile · initial attempt',add(l.nuchal,[3,-1,0]),{
        ...SAGITTAL, width:[.4,0,1], name:'Oblique attempt',
      },35,'The fluid layer and adjacent amnion intersect the oblique section. The amnion and skin cannot be reliably distinguished.', {
        labels:['NT space','posterior skin','amnion fold'], shadow:shadow(l.nuchal,-2,3), sweep:4,
      });
      chapter('nt-repeat','Nuchal profile · position-change repeat',add(l.nuchal,[-3,-1,1]),{
        ...SAGITTAL, width:[-.47,0,1], name:'Alternate oblique',
      },35,'After position change, the oblique crop again cuts the amnion close to the posterior skin. Withhold NT.', {
        labels:['NT space','amnion fold'], shadow:shadow(l.nuchal,1,2.7), sweep:5,
        measurement:source.measurement,
      });
    } else {
      chapter('nt','Magnified midsagittal nuchal translucency',l.nuchal,SAGITTAL,40,
        `The skin borders the hypoechoic subcutaneous layer. Here its maximum span is ${shape.nt.toFixed(1)} mm.`, {
          sweep:8, labels:['NT space','posterior skin'],
          measure:length(l.nuchal,add(l.nuchal,[0,-shape.nt,0]),`NT ${shape.nt.toFixed(1)} mm`), measurement:source.measurement,
        });
    }
    views('Record cardiac activity and basic anatomy');
    mmode('first-mmode','Fetal cardiac activity',l.heart,AXIAL,37,3,1.20,source.measurement);
    chapter('axial-head','Calvarium, midline and choroid plexuses',[0,0,34*l.scale],AXIAL,39,
      'Rotate the beam through the calvarium and bright paired choroid plexuses.', {
        labels:['calvarium','falx','choroid_plexus'],
      });
    chapter('first-abdomen','Stomach and intact abdominal wall',[0,3,-3*l.scale],AXIAL,40,
      'Trace the stomach region and outer abdominal contour across an axial sweep.', { labels:['fetus','first stomach'] });
    chapter('first-bladder','Fetal pelvis and bladder',[0,4,-5.1*l.scale],AXIAL,35,
      'The fetal bladder lies within the lower abdominal wall.', { labels:['fetus','fetal_bladder'] });
    chapter('first-cord','Fetal abdominal cord insertion',[0,10,2*l.scale],SAGITTAL,47,
      'Follow the cord into the anterior wall in an oblique-to-longitudinal sweep.', {
        labels:['fetus','umbilical_cord'],
      });
    views('Survey fetal outline and maternal landmarks');
    chapter('first-profile','Face and sagittal profile',[0,8,31*l.scale],SAGITTAL,60,
      'Follow the nose, jaw and vault through the longitudinal plane.', { labels:['nasal_bone','calvarium','fetus'] });
    chapter('first-spine','Longitudinal spine',[0,-10,7*l.scale],SAGITTAL,57,
      'The paramedian plane separates the spinal echoes from the fetal outline.', { labels:['spinal_echoes','fetus'] });
    addLimbs(l.limbs,false);
    chapter('first-placenta','Posterior placenta and internal os',[0,-14,-24],SAGITTAL,106,
      'Track the posterior placental band and its relation to the lower uterine segment and internal os.', {
        overview:true, sweep:17, labels:['placenta','uterus'],
      });
    return output;
  }

  const mid = stage==='mid';
  const [hax, hay] = l.hcAxes;
  const [aax, aay] = l.acAxes;
  const ellipse = (centre, radii, annotation) => ({ type:'ellipse', centre, radii, label:annotation });
  const hc = ellipse(l.head,[hax,hay],`HC ${shape.hc} mm`);
  const ac = ellipse(l.abdomen,[aax,aay],`AC ${shape.ac} mm`);
  const bpd = length(add(l.head,[-hax,0,0]),add(l.head,[hax,0,0]),`BPD ${shape.bpd} mm`);
  const shaftEdge = mul(l.femur.direction,l.femur.length/2);
  const fl = length(sub(l.femur.centre,shaftEdge),add(l.femur.centre,shaftEdge),`FL ${shape.fl} mm`);
  const scanHead = () =>
    chapter('biometry-head','Transthalamic head biometry',l.head,AXIAL,mid?76:117,
      'Calvarium, falx, cavum and thalami identify the plane. Trace the outer head ellipse.', {
        labels:['calvarial contour','cavum','thalami','falx'], measure:mid?[hc,bpd]:hc,
        measurement:mid?`BPD ${shape.bpd} mm; HC ${shape.hc} mm.`:`HC ${shape.hc} mm.`,
      });
  const scanAbdomen = (failed = false, repeat = false) => {
    const target = failed ? add(l.abdomen,[repeat?4:-3,repeat?-4:1,0]) : l.abdomen;
    chapter(failed?(repeat?'ac-repeat':'ac-initial'):'biometry-abdomen',
      failed?(repeat?'Abdominal circumference · lateral repeat':'Abdominal circumference · shadowed window'):'Abdominal circumference',target,
      failed?{...AXIAL,beam:[repeat?-.31:.2,-1,0],name:repeat?'Lateral repeat':'Initial axial'}:AXIAL,mid?74:122,
      failed?'The near abdominal wall is seen but the shadow removes part of the skin contour. An ellipse cannot be recovered from this window.'
        :'The rounded section contains the left stomach and portal sinus. Trace the external skin line.', {
        labels:['abdominal skin','stomach','umbilical_vein'], measure:failed?undefined:ac,
        shadow:failed?shadow(target,repeat?-14:15,repeat?16:14):undefined,
        measurement:failed?(repeat?'AC and EFW unavailable.':undefined):`AC ${shape.ac} mm.`,
      });
  };
  const scanFemur = () =>
    chapter('biometry-femur','Ossified femoral diaphysis',l.femur.centre,{
      ...AXIAL,width:l.femur.direction,name:'Femur long axis',
    },mid?60:99,'Sweep along the bright shaft, align both ossified ends and exclude the cartilaginous epiphyses.', {
      labels:['ossified shaft','femur'], measure:fl, measurement:`FL ${shape.fl} mm.`,
    });
  const scanFluid = (failed=false, repeat=false) => {
    const ends = mul(l.vertical,shape.dvp/2);
    const target = failed ? add(l.fluid,[repeat?3:-3,0,0]) : l.fluid;
    chapter(repeat?'fluid-repeat':'fluid',repeat?'Vertical pocket · lateral repeat':'Deepest vertical fluid pocket',
      target,{ ...AXIAL,beam:mul(l.vertical,-1), width:[1,0,0], name: 'Maternal vertical' },mid?78:115,
      failed?'The dark near-field lies adjacent to fetal parts and a persistent far-wall shadow. A reliable vertical span cannot be saved.'
        :'The line through the selected fluid pocket is vertical in the maternal frame. Follow the two fluid–tissue interfaces.', {
        sweep:10, labels:['nearest fluid','maternal interface'],
        shadow:failed?shadow(target,repeat?-3:1,11):undefined,
        measure:failed?undefined:length(sub(l.fluid,ends),add(l.fluid,ends),`DVP ${(shape.dvp/10).toFixed(1)} cm`),
        measurement:failed?(repeat?'DVP unavailable on the repeat view.':undefined):`DVP ${(shape.dvp/10).toFixed(1)} cm.`,
      });
  };

  if (mid) {
    views('Record heart rate and biometry');
    chapter('mid-overview','Singleton overview',[0,1,58],SAGITTAL,214,
      'Survey fetal lie, location and number through adjacent sections before individual measurements.', {
        overview:true, sweep:49, labels:['fetus','placenta','amniotic_cavity'],
      });
    mmode('mid-mmode','Fetal cardiac activity',[-4,1,43],AXIAL,68,3,1.25,'3 cycles / 1.25 s × 60 = 144 bpm.');
    scanHead();
    scanAbdomen();
    scanFemur();
    views('Survey head and face');
    chapter('transventricular','Transventricular brain',[0,-1,112],AXIAL,75,
      'A superior axial sweep shows the ventricles and choroid plexuses above the transthalamic plane.', {
        labels:['ventricles','choroid','falx'],
      });
    chapter('posterior-fossa','Posterior fossa',[0,-13,99],{
      ...AXIAL,beam:[0,-1,-.19],name:'Oblique axial',
    },70,'Rotate into the posterior fossa to reveal the cerebellum and cisterna magna.', { labels:['cerebellum','cisterna_magna'] });
    chapter('orbits','Both eye globes',[0,22,102],CORONAL,70,
      'The coronal plane samples the paired eye globes side by side.', { labels:['orbits'] });
    chapter('upper-lip','Coronal nose and upper lip',[0,31,95],{
      ...CORONAL,beam:[0,-.62,-1],
    },47,'Sweep past the nares to find the continuous upper lip in the adjacent slice.', { labels:['nares','upper_lip'] });
    chapter('profile','Midsagittal face and nasal bone',[0,19,104],SAGITTAL,79,
      'Track the anterior profile from forehead through nasal bone to chin.', { labels:['upper_lip','fetus'] });
    views('Sweep thorax and heart');
    chapter('chest-diaphragm','Lungs and diaphragm',[0,-6,37],{
      ...CORONAL, beam:[0,-.25,-1],
    },94,'Coronal-to-oblique motion shows both lungs and the diaphragm over the abdominal contents.', {
      labels:['lungs','diaphragm'],
    });
    chapter('four-chamber','Four-chamber view and situs',[-4,0,42.5],AXIAL,73,
      'Trace four separate chambers. Relative position of the spine and left-facing cardiac apex establishes orientation.', {
        labels:HEART_LABELS,
      });
    const cardiacTargets = [
      ['lvot','Left ventricular outflow',[-6,5,50.8],{ ...AXIAL, beam:[0,-1,-.13], width:[1,-.1,1.1] },['left_ventricle','aortic_outflow']],
      ['rvot','Right ventricular outflow',[-1,8,50.9],{ ...AXIAL, beam:[0,-1,-1] },['right_ventricle','pulmonary_outflow']],
      ['3vv','Three-vessel view',[0,7,58.6],AXIAL,['aortic_outflow','pulmonary_outflow','superior_vena_cava']],
      ['3vt','Three-vessel and trachea',[0,0,64.25],AXIAL,['aortic_outflow','pulmonary_outflow','trachea']],
    ];
    for (const [id,title,target,plane,labels] of cardiacTargets) {
      chapter(id,title,target,plane,73,kind==='limited'?'Spine and rib shadow interrupt the great-vessel profile. Save the limited image and reattempt from an alternate angle.'
        :'Rock the probe superiorly to bring the named great-vessel landmarks into the slice.', {
        labels, shadow:kind==='limited'?shadow(target,3,12):undefined, sweep:6,
      });
    }
    if (kind==='limited') {
      views('Repeat cardiac sweep');
      for (const [id,title,target,plane,labels] of cardiacTargets) {
        chapter(`${id}-repeat`,`${title} · lateral repeat`,add(target,[2,-3,1]),{
          ...plane, beam:add(plane.beam,[-.55,.14,-.09]),name:'Lateral repeat',
        },73,'The repeat beam follows a different approach. A residual shadow crosses the required landmark, which remains incomplete.', {
          labels, shadow:shadow(target,-4,11), sweep:6,
          measurement:id==='3vt'?'Outflow and three-vessel views remain limited.':undefined,
        });
      }
    }
    views('Assess abdomen and umbilical insertion');
    chapter('kidneys','Kidneys and renal pelves',[0,-8,5.6],AXIAL,75,
      'Sweep across both renal outlines and their collecting systems.', { labels:['kidneys','renal_pelves'] });
    chapter('bladder','Bladder and adjacent umbilical arteries',[0,5.4,-12.5],AXIAL,72,
      'Trace the fetal bladder and vessels beside it in the pelvis.', { labels:['fetal_bladder','umbilical_arteries'] });
    const defect = l.omphalocele;
    const defectLabels = ['cord','sac contents','sac membrane','abdominal wall defect'];
    chapter('insertion','Fetal abdominal cord insertion',defect?.target??[0,23.8,11.6],AXIAL,65,
      defect?'Sweep through the neck of a membrane-covered sac at the midline wall. Follow the bowel echoes into the sac.'
        :'Trace the cord through the intact anterior abdominal wall.', {
        labels:defect?defectLabels:['cord','fetus'],
        focus:defect?'omphalocele':undefined,
        sweep:defect?14:undefined,
        measure:defect?length(...defect.neck,`${Math.hypot(...sub(...defect.neck)).toFixed(0)} mm wall neck`):undefined,
        measurement:defect?source.measurement:undefined,
      });
    if (defect) {
      views('Confirm the wall finding in another plane');
      chapter('omphalocele-sagittal','Sagittal confirmation of cord insertion',defect.target,SAGITTAL,71,
        'The membrane-covered sac remains contiguous with the ventral defect. The cord leads into the sac apex in the orthogonal sweep.', {
          labels:defectLabels, focus:'omphalocele', sweep:10,
        });
    }
    views('Survey spine and extremities');
    chapter('long-spine','Longitudinal spine',[0,-15,43],SAGITTAL,134,
      'Trace the ossification centers and overlying skin from cervical to caudal levels.', { labels:['spine','fetus'], sweep:12 });
    chapter('axial-spine','Transverse spine',[0,-17,33],AXIAL,72,
      'Sweep across serial transverse levels to find the body and paired posterior ossification centers.', { labels:['spine'], sweep:34 });
    addLimbs(l.limbs,true);
    views('Document placenta, cervix and fluid');
    const maternalSagittal={
      beam:mul(l.vertical,-1), width:volumeFor(stage).axes[2], name:'Maternal sagittal',
    };
    chapter('mid-placenta','Posterior placental edge',l.placenta,maternalSagittal,132,
      'Follow the deep placental band along the chorionic surface toward the lower uterine segment.', {
        labels:['placenta','uterus'], overview:true,
      });
    chapter('mid-cervix','Internal os and lower uterine segment',l.cervix,maternalSagittal,118,
      'Advance to the internal os and identify the cervical canal inside the lower uterine tissues.', {
        labels:['cervical_canal','uterus'], overview:true,
      });
    chapter('placental-insertion','Placental cord insertion',l.placentalCord,SAGITTAL,73,
      'Sweep the cord into the placental surface to document the attachment.', { labels:['cord','placenta'] });
    scanFluid();
    return output;
  }

  const lateVolume = volumeFor('late');
  const local = world => lateVolume.axes[0].map((_,j)=>
    lateVolume.axes.reduce((sum,row,i)=>sum+row[j]*(world[i]-lateVolume.maternalCentre[i]),0));
  views('Confirm lie and assess fluid');
  chapter('presentation','Cephalic lie and lower uterine segment',local([0,26,-65]),{
    beam:mul(l.vertical,-1),width:lateVolume.axes[2],name:'Maternal sagittal',
  },164,'The presenting head lies at the lower uterine segment upstream of the internal os.', {
    labels:['calvarium','cervical_canal','maternal_bladder'], overview:true, sweep:22,
  });
  chapter('late-placenta','Placental position',local([12,94,183]),{
    beam:mul(l.vertical,-1),width:lateVolume.axes[2],name:'Maternal sagittal',
  },153,'Sweep the anterior placental surface and its adjacent tissue–fluid boundary.', {
    labels:['placenta','uterus'], overview:true, sweep:17,
  });
  scanFluid(kind==='limited');
  if (kind==='limited') scanFluid(true,true);
  views(kind==='limited'?'Record usable biometry':'Acquire fetal biometry');
  scanHead();
  scanAbdomen(kind==='limited');
  if (kind==='limited') scanAbdomen(true,true);
  scanFemur();
  views(kind==='limited'?'Compare with previous scan':'Calculate estimated weight and compare');
  const [head,abdomen,femur]=[shape.hc,shape.ac,shape.fl].map(length=>length/10);
  const estimated = Math.round(10**(1.326+.0107*head+.0438*abdomen+.158*femur-.00326*abdomen*femur));
  const previous = {normal:1190,abnormal:1130,limited:1205}[kind];
  chapter('interval-growth','Interval growth assessment',l.head,AXIAL,122,
    kind==='limited'?'The prior comparison is available. Today’s head and femur are visible but the AC is incomplete, so the current estimated weight is withheld.'
      :'Revisit the saved head plane alongside the comparison chart. The modeled EFW uses the three saved HC, AC and FL acquisitions.', {
      labels:['calvarial contour','thalami'], chart: true, measurement: source.measurement,
      growth:[previous, kind==='limited'?null:estimated],
    });
  views(kind==='limited'?'Attempt clinically indicated Doppler':'Sample umbilical artery flow');
  const cordChapter = (repeat) => {
    const target = l.cord[repeat?12:6];
    const interrupted = kind==='limited';
    const abnormal = kind==='abnormal';
    const peak = abnormal ? (repeat?43:44) : 42;
    const edv = abnormal ? 0 : 16;
    chapter(repeat?'ua-repeat':'ua',repeat?'Free-loop UA · repeat sample':'Free-loop umbilical artery',
      target, { ...SAGITTAL, beam:[repeat?.23:-.13,-1,0], name:repeat?'Alternate free loop':'Free-loop gate' },83,
      interrupted?'Repeat gated sampling at a distinct segment. Gaps obscure the end-diastolic envelope, so waveform classification is unavailable.'
        :abnormal?'The correctly seated sample continues to reach zero at end diastole on repeated cycles.'
          :'A stable free-loop gate gives forward flow through end diastole.', {
        labels:['cord'], signal:signal('PW Doppler',4,1.68,peak,edv,interrupted),
        measurement:repeat?(interrupted?source.measurement:'Repeat EDV 0 cm/s.'):interrupted?undefined:source.measurement,
      });
  };
  cordChapter(false);
  if (kind!=='normal') cordChapter(true);
  return output;
}
