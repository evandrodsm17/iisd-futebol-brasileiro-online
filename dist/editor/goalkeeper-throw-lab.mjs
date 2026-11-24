import {renderRuntimeBody} from '../native-runtime-body.mjs';

const sources = {
  '0': {path:'../assets/issd/slide-lab-local/goalkeeper-throw-sheet.png', durations:[1, 2, 2, 3, 20]},
  '7': {path:'../assets/issd/slide-lab-local/goalkeeper-throw-7.png', durations:[2, 2, 2, 2, 20]},
  '1': {path:'../assets/issd/slide-lab-local/goalkeeper-throw-1.png', durations:[2, 2, 2, 3, 22]}
};
const canvas = document.getElementById('keeper-throw-sequence');
const status = document.getElementById('keeper-throw-sequence-status');
const direction = document.getElementById('keeper-throw-direction');
const paletteSelect = document.getElementById('keeper-throw-palette');
const skin = document.getElementById('keeper-throw-skin');
const play = document.getElementById('keeper-throw-play');
const slider = document.getElementById('keeper-throw-tick');
const label = document.getElementById('keeper-throw-frame');
const evidenceLabel = document.getElementById('keeper-throw-input-evidence');
const directionNames = {Up:'cima',Down:'baixo',Left:'esquerda',Right:'direita',UpLeft:'cima/esquerda',UpRight:'cima/direita',DownLeft:'baixo/esquerda',DownRight:'baixo/direita'};
let inputEvidence = null;
function updateEvidence(){
 const item=inputEvidence?.orientations?.[direction.value];
 if(!item){evidenceLabel.textContent='Condições dos ensaios indisponíveis.';return;}
 const names=item.long.map(name=>directionNames[name]||name).join(', ');
 evidenceLabel.textContent=`No mesmo estado salvo, segurar ${names} antes de B produziu estes descritores; também observado após mudar de cima para essas direções. Isso não estabelece uma regra geral de direção na tela.`;
}
const ctx = canvas.getContext('2d');
let sheet = null, durations = [], total = 0, tick = 0, playing = true, last = null, generation = 0, runtime = null, preview = null;
const rendered = new Map();
const colors = words => words.map(word=>'#'+[0,5,10].map(shift=>{const value=(word>>shift)&31;return ((value<<3)|(value>>2)).toString(16).padStart(2,'0');}).join(''));
function currentCycle(){
 if(!runtime)return null;
 if(runtime.schema==='issd-keeper-throw-runtime-local/v1')return direction.value==='0'?runtime:null;
 const cycle=runtime.cycles?.[direction.value];return cycle?{...cycle,width:runtime.width,height:runtime.height}:null;
}
function updatePalette(){
 const available=!!currentCycle();paletteSelect.disabled=!available;skin.disabled=!available||paletteSelect.value==='captured';
 if(sheet)status.textContent=available&&paletteSelect.value!=='captured'?'Paleta experimental aplicada aos descritores validados; aparência da equipe ainda não foi confirmada.':'Cinco poses validadas; cadência observada em um replay, sem a continuação completa.';
}
function dynamicFrame(index){
 const cycle=currentCycle();if(!cycle)return null;
 const key=`${direction.value}/${index}/${paletteSelect.value}/${skin.value}`;if(rendered.has(key))return rendered.get(key);
 const words=paletteSelect.value==='captured'?runtime.palette:preview.teams?.[Number(paletteSelect.value)]?.palettes?.[2+Number(skin.value)];
 if(!Array.isArray(words)||words.length!==16||words.some(word=>!Number.isInteger(word)||word<0||word>0x7fff))return null;
 const palette=colors(words);let result;
 try{result=renderRuntimeBody(cycle,index,palette,{4:palette});}
 catch{runtime=null;updatePalette();status.textContent='Composição dinâmica indisponível; exibindo a captura original.';return null;}
 const frame=document.createElement('canvas');frame.width=96;frame.height=96;frame.getContext('2d').putImageData(new ImageData(result.rgba,96,96),0,0);
 if(rendered.size>=256)rendered.delete(rendered.keys().next().value);rendered.set(key,frame);return frame;
}
function draw() {
  if (!sheet) return;
  let frame = Math.floor(tick), index = 0;
  while (index < durations.length - 1 && frame >= durations[index]) frame -= durations[index++];
  ctx.clearRect(0, 0, 96, 96);
  ctx.imageSmoothingEnabled = false;
  const dynamic=dynamicFrame(index);
  if(dynamic)ctx.drawImage(dynamic,0,0);else ctx.drawImage(sheet, index * 96, 0, 96, 96, 0, 0, 96, 96);
  slider.value = String(Math.floor(tick));
  const releaseTick = {'0': 5, '7': 6, '1': 6}[direction.value];
  const release = Math.floor(tick) === releaseTick ? ' · vínculo com o goleiro liberado neste replay' : '';
  label.textContent = `${Math.floor(tick) + 1} / ${total}${release}`;
}
function loadDirection() {
  updateEvidence();
  const selected = sources[direction.value]; const current = ++generation;
  sheet = null; tick = 0; last = null; play.disabled = true; slider.disabled = true;updatePalette();
  ctx.clearRect(0, 0, 96, 96); label.textContent = '';
  if (!selected) { status.textContent = 'Orientação indisponível.'; return; }
  status.textContent = 'Carregando sequência local…';
  const image = new Image();
  image.onload = () => {
    if (current !== generation) return;
    if (image.naturalWidth !== 480 || image.naturalHeight !== 96) { status.textContent = 'Arquivo local da sequência tem dimensões inválidas.'; return; }
    sheet = image; durations = selected.durations; total = durations.reduce((a, b) => a + b, 0);
    slider.max = String(total - 1); play.disabled = false; slider.disabled = false;
    status.textContent = 'Cinco poses validadas; cadência observada em um replay, sem a continuação completa.'; updatePalette();draw();
  };
  image.onerror = () => { if (current === generation) status.textContent = 'Sequência local indisponível: gere os dados da ROM e das capturas validadas.'; };
  image.src = selected.path;
}
function animate(now) {
  if (last !== null && playing && sheet) tick = (tick + Math.min(100, Math.max(0, now - last)) * 60 / 1000) % total;
  last = now; draw(); requestAnimationFrame(animate);
}
direction.addEventListener('change', loadDirection);
play.addEventListener('click', () => { playing = !playing; play.textContent = playing ? 'Pausar' : 'Reproduzir'; last = null; });
slider.addEventListener('input', () => {
  if (!sheet) return;
  tick = Math.max(0, Math.min(total - 1, Number(slider.value) || 0));
  playing = false; play.textContent = 'Reproduzir'; last = null; draw();
});
paletteSelect.addEventListener('change',()=>{updatePalette();draw();});
skin.addEventListener('change',draw);
try{
 const responses=await Promise.all(['../assets/issd/native-keeper-throw-local.json','../assets/issd/editor-preview-local.json','../data/issd-rom-catalog.json'].map(path=>fetch(path)));
 if(responses.some(response=>!response.ok))throw new Error('Local composition unavailable');
 const [data,editor,catalog]=await Promise.all(responses.map(response=>response.json()));
 const legacy=data.schema==='issd-keeper-throw-runtime-local/v1'&&data.frames?.length===5&&data.durations?.join(',')==='1,2,2,3,20';
 const complete=data.schema==='issd-keeper-throw-runtime-local/v2'&&Object.entries(sources).every(([key,source])=>data.cycles?.[key]?.frames?.length===5&&data.cycles[key].durations?.join(',')===source.durations.join(','));
 if((!legacy&&!complete)||data.width!==96||data.height!==96||editor.schema!=='issd-editor-preview-local/v1'||!Array.isArray(catalog.teams))throw new Error('Invalid composition data');
 runtime=data;preview=editor;
 for(const team of catalog.teams){const option=document.createElement('option');option.value=String(team.id);option.textContent=team.name;paletteSelect.append(option);}
 updatePalette();
}catch{/* The existing captured sheets remain available. */}
loadDirection(); requestAnimationFrame(animate);
try{
 const response=await fetch('../data/issd-keeper-throw-input-evidence.json');
 const data=await response.json();
 if(!response.ok||data.schema!=='issd-keeper-throw-input-evidence/v1'||!Object.values(data.orientations||{}).every(item=>Array.isArray(item.long)&&Array.isArray(item.turn)))throw new Error('Invalid evidence');
 inputEvidence=data;updateEvidence();
}catch{updateEvidence();}
