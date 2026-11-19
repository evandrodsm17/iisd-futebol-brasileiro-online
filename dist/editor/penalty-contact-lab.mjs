import {recordedPenaltyContact} from '../penalty-contact-observed.mjs';
const shot=document.querySelector('#penalty-contact-shot');
const keeper=document.querySelector('#penalty-contact-keeper');
const status=document.querySelector('#penalty-contact-status');
let data,tables=null;
function draw(){
 try{
  const result=recordedPenaltyContact(data,tables,shot.value,keeper.value);
  const score=`Placar registrado: ${result.before[0]} × ${result.before[1]} → ${result.after[0]} × ${result.after[1]}.`;
  status.textContent=result.outcome==='contact_deferred'
   ? `Contato selecionado e resolução posterior sem incremento. ${result.contactVerified?'Área de contato conferida com as tabelas locais.':'Tabelas locais indisponíveis para conferir a área.'} ${score} O tipo de defesa não foi identificado.`
   : `O lance registrado seguiu pelo ramo de gol. ${score} Isso não prevê o resultado de outras cobranças.`;
 }catch{status.textContent='Não foi possível validar esta comparação.';}
}
for(const select of [shot,keeper])select.addEventListener('change',draw);
try{
 const response=await fetch('../data/issd-penalty-contact-grid.json');if(!response.ok)throw new Error('comparison unavailable');
 data=await response.json();if(data.schema!=='issd-penalty-contact-grid/v1'||!Array.isArray(data.cases)||data.cases.length!==9)throw new Error('invalid comparison');
 try{const local=await fetch('../assets/issd/penalty-hitbox-tables-local.json');if(local.ok)tables=await local.json();}catch{/* Recorded outcomes remain usable without local tables. */}
 shot.disabled=keeper.disabled=false;draw();
}catch{status.textContent='Comparações capturadas indisponíveis.';}
