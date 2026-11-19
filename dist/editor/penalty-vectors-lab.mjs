import {observedPenaltyAimWord} from '../penalty-observed-input.mjs';
import {nativePenaltyVectorFromTables} from '../penalty-shot-vector.mjs';
const input=document.querySelector('#penalty-vector-input');
const variant=document.querySelector('#penalty-vector-variant');
const height=document.querySelector('#penalty-vector-height');
const status=document.querySelector('#penalty-vector-status');
let tables;
for(const option of input.querySelectorAll('[data-observed]'))option.value=String(observedPenaltyAimWord(option.dataset.observed));
function draw(){
 try{
  const result=nativePenaltyVectorFromTables(tables,Number(variant.value),Number(input.value),Number(height.value));
  status.textContent=`Vetor nativo: X ${result.dx} · Y ${result.dy} · altura ${result.dz} · índice ${result.index}. Valores internos; direção visual não validada.`;
 }catch{status.textContent='Tabelas de vetores inválidas.';}
}
for(const control of [input,variant,height])control.addEventListener('change',draw);
try{
 const response=await fetch('../assets/issd/penalty-shot-vectors-local.json');
 if(!response.ok)throw new Error('local tables unavailable');
 tables=await response.json();nativePenaltyVectorFromTables(tables,0,0,0);
 for(const control of [input,variant,height])control.disabled=false;
 draw();
}catch{status.textContent='Tabelas locais indisponíveis. Extraia os vetores da sua ROM para usar esta prévia.';}
