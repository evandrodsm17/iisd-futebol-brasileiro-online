import {nativePenaltyDirection} from '../penalty-direction.mjs';
import {nativePenaltyKeeperDirection} from '../penalty-keeper-direction.mjs';
const select=document.querySelector('#penalty-keeper-direction-input');
const status=document.querySelector('#penalty-keeper-direction-status');
function draw(){
 const word=Number(select.value),base=nativePenaltyDirection(word).base;
 // In the three recorded examples the CPU helper preserved the decoded index.
 const result=nativePenaltyKeeperDirection(word,base);
 status.textContent=`Índice inicial ${result.base} · índice final ${result.index}. Neste ensaio a rotina intermediária preservou a direção.`;
}
select.addEventListener('change',draw);draw();
