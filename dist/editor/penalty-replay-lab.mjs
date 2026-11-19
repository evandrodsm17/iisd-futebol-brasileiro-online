import {replayPenaltyCapture} from '../penalty-capture-replay.mjs';
const status=document.querySelector('#penalty-replay-status');
const result=document.querySelector('#penalty-replay-result');
const previous=document.querySelector('#penalty-replay-previous');
const next=document.querySelector('#penalty-replay-next');
let steps=[],index=0;
function draw(){
 const step=steps[index];
 result.textContent=`Cobrança ${index+1} / ${steps.length} · Equipe ${step.team+1} · ${step.scored?'GOL':'SEM GOL'} · ${step.score[0]} × ${step.score[1]}`;
 status.textContent=step.checks?`Resultado após contato e ${step.checks} verificações da captura. A causa exata do contato não é determinada nesta prévia.`:'Resultado pela verificação de gol observada na captura.';
 if(step.winner!==null) status.textContent+=` Equipe ${step.winner+1} venceu a disputa registrada.`;
 previous.disabled=index===0;next.disabled=index===steps.length-1;
}
previous.addEventListener('click',()=>{if(index>0){index--;draw();}});
next.addEventListener('click',()=>{if(index<steps.length-1){index++;draw();}});
try{
 const response=await fetch('../data/issd-penalty-replay.json');
 if(!response.ok)throw new Error('capture unavailable');
 steps=replayPenaltyCapture(await response.json());
 if(!steps.length)throw new Error('empty capture');
 draw();
}catch(error){status.textContent='Não foi possível reproduzir a captura de pênaltis.';console.error(error);}
