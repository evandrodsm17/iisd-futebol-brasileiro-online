import {recordedPenaltyChecks} from '../penalty-contact-timeline.mjs';
import {recordedPenaltyContact} from '../penalty-contact-observed.mjs';
const shot=document.querySelector('#penalty-contact-shot');
const keeper=document.querySelector('#penalty-contact-keeper');
const status=document.querySelector('#penalty-contact-status');
const slider=document.querySelector('#penalty-contact-check');
const play=document.querySelector('#penalty-contact-play');
const counter=document.querySelector('#penalty-contact-check-counter');
const checkStatus=document.querySelector('#penalty-contact-check-status');
const diagram=document.querySelector('#penalty-contact-diagram');
const context=diagram.getContext('2d');
let data,tables=null,timeline=null,motion=null,checks=null,timer=null;
function stop(){if(timer!==null)clearTimeout(timer);timer=null;play.textContent='Reproduzir sequência';}
function playNext(){
 const index=Number(slider.value)-1;
 if(!checks||index>=checks.length-1){stop();return;}
 const delay=Math.max(1,Math.round((checks[index+1].frame-checks[index].frame)*1000/60));
 timer=setTimeout(()=>{slider.value=String(index+2);drawCheck();playNext();},delay);
}
function draw(){
 try{
  const result=recordedPenaltyContact(data,tables,shot.value,keeper.value);
  const score=`Placar registrado: ${result.before[0]} × ${result.before[1]} → ${result.after[0]} × ${result.after[1]}.`;
  status.textContent=result.outcome==='contact_deferred'
   ? `Contato selecionado e resolução posterior sem incremento. ${result.contactVerified?'Área de contato conferida com as tabelas locais.':'Tabelas locais indisponíveis para conferir a área.'} ${score} O tipo de defesa não foi identificado.`
   : `O lance registrado seguiu pelo ramo de gol. ${score} Isso não prevê o resultado de outras cobranças.`;
 }catch{status.textContent='Não foi possível validar esta comparação.';}
}
function drawCheck(){
 context.clearRect(0,0,diagram.width,diagram.height);
 context.fillStyle='#123c30';context.fillRect(0,0,diagram.width,diagram.height);
 if(!checks){counter.textContent='';checkStatus.textContent='Sequência de verificações não capturada para esta combinação.';return;}
 const index=Number(slider.value)-1,check=checks[index];counter.textContent=`${index+1} / ${checks.length}`;
 context.fillStyle='#78c9ff';context.beginPath();context.arc(check.keeper.x,check.keeper.y,5,0,Math.PI*2);context.fill();
 context.fillStyle='#ffe57a';context.beginPath();context.arc(check.ball.x,check.ball.y,3,0,Math.PI*2);context.fill();
 const keeperDescription=check.keeperSource==='calculated'?'calculado a partir do movimento registrado':check.keeperSource==='initial-confirmed'?'na posição inicial confirmada pela captura':'com posição registrada';
 checkStatus.textContent=`Quadro ${check.frame} · ${check.hit?'contato na área':'sem contato na área'} · ${check.verified?'comparação conferida com a ROM local':'comparação registrada; tabelas locais indisponíveis'}. Bola calculada; goleiro ${keeperDescription}. Quadros sem chamada registrada não são incluídos.`;
}
function choose(){
 stop();draw();checks=null;slider.disabled=true;play.disabled=true;
 if(timeline){
  try{checks=recordedPenaltyChecks(timeline,tables,shot.value,keeper.value,motion);if(checks){slider.max=String(checks.length);slider.value='1';slider.disabled=false;play.disabled=checks.length<2;}}
  catch{checkStatus.textContent='Não foi possível validar a sequência.';counter.textContent='';return;}
 }
 drawCheck();
}
for(const select of [shot,keeper])select.addEventListener('change',choose);
slider.addEventListener('input',()=>{stop();drawCheck();});
play.addEventListener('click',()=>{
 if(timer!==null){stop();return;}
 if(!checks||checks.length<2)return;
 if(Number(slider.value)>=checks.length){slider.value='1';drawCheck();}
 play.textContent='Pausar';playNext();
});
try{
 const response=await fetch('../data/issd-penalty-contact-grid.json');if(!response.ok)throw new Error('comparison unavailable');
 data=await response.json();if(data.schema!=='issd-penalty-contact-grid/v1'||!Array.isArray(data.cases)||data.cases.length!==9)throw new Error('invalid comparison');
 try{const local=await fetch('../assets/issd/penalty-hitbox-tables-local.json');if(local.ok)tables=await local.json();}catch{/* Recorded outcomes remain usable without local tables. */}
 try{const response=await fetch('../data/issd-penalty-contact-timeline.json');if(response.ok){const result=await response.json();if(result.schema==='issd-penalty-contact-timeline/v1')timeline=result;}}catch{/* The nine recorded outcomes remain available. */}
 try{const response=await fetch('../data/issd-penalty-keeper-motion.json');if(response.ok){const result=await response.json();if(result.schema==='issd-penalty-keeper-motion/v1')motion=result;}}catch{/* Recorded goalkeeper coordinates remain available. */}
 shot.disabled=keeper.disabled=false;choose();
}catch{status.textContent='Comparações capturadas indisponíveis.';}
