import {previewPenaltyFreeFlight} from '../penalty-free-flight-preview.mjs';
const canvas=document.querySelector('#penalty-free-flight-canvas');
const direction=document.querySelector('#penalty-free-flight-direction');
const shoot=document.querySelector('#penalty-free-flight-shoot');
const status=document.querySelector('#penalty-free-flight-status');
const ctx=canvas.getContext('2d'),held=new Set();
let tables,animation=0;
function stop(){cancelAnimationFrame(animation);animation=0;}
function background(){
 ctx.clearRect(0,0,canvas.width,canvas.height);ctx.fillStyle='#123c30';ctx.fillRect(0,0,canvas.width,canvas.height);
 ctx.strokeStyle='#285c49';ctx.lineWidth=1;
 for(let x=0;x<=256;x+=32){ctx.beginPath();ctx.moveTo(x,0);ctx.lineTo(x,224);ctx.stroke();}
 for(let y=0;y<=224;y+=32){ctx.beginPath();ctx.moveTo(0,y);ctx.lineTo(256,y);ctx.stroke();}
}
function draw(frames,index){
 background();if(index<0)return;
 ctx.strokeStyle='#9ddcb1';ctx.lineWidth=1;ctx.beginPath();
 for(let i=0;i<=index;i++){const f=frames[i],x=f.screenX+4,y=f.screenY+4;if(i===0)ctx.moveTo(x,y);else ctx.lineTo(x,y);}
 ctx.stroke();const point=frames[index];ctx.fillStyle='#ffe57a';ctx.beginPath();ctx.arc(point.screenX+4,point.screenY+4,3,0,Math.PI*2);ctx.fill();
}
function launch(){
 if(!tables)return;stop();
 const result=previewPenaltyFreeFlight(tables,direction.value);let started;
 status.textContent='Calculando voo livre…';
 const animate=now=>{
  if(started===undefined)started=now;
  const index=Math.min(result.frames.length-1,Math.floor((now-started)*60/1000));draw(result.frames,index);
  if(index<result.frames.length-1){status.textContent=`Voo calculado · quadro ${index+1} de ${result.frames.length}.`;animation=requestAnimationFrame(animate);}
  else status.textContent=result.stop==='geometry_reached'?'Ponto de verificação geométrica alcançado. Gol, defesa e colisões não são calculados nesta prévia.':result.stop==='ground_pending'?'Contato com o chão pendente de cálculo nesta prévia.':'Limite da prévia alcançado; resultado não determinado.';
 };
 animation=requestAnimationFrame(animate);
}
function updateDirection(){
 const x=Number(held.has('ArrowRight'))-Number(held.has('ArrowLeft'));
 const y=Number(held.has('ArrowDown'))-Number(held.has('ArrowUp'));
 direction.value=y<0?(x<0?'upLeft':x>0?'upRight':'up'):y>0?(x<0?'downLeft':x>0?'downRight':'down'):x<0?'left':x>0?'right':'neutral';
}
canvas.addEventListener('keydown',event=>{
 if(event.key.startsWith('Arrow')){event.preventDefault();held.add(event.key);updateDirection();}
 else if(event.code==='KeyA'&&!event.repeat){event.preventDefault();launch();}
});
canvas.addEventListener('keyup',event=>{if(event.key.startsWith('Arrow')){event.preventDefault();held.delete(event.key);updateDirection();}});
canvas.addEventListener('blur',()=>held.clear());
shoot.addEventListener('click',launch);
background();
try{
 const response=await fetch('../assets/issd/penalty-shot-vectors-local.json');if(!response.ok)throw new Error('tables unavailable');
 const loaded=await response.json();previewPenaltyFreeFlight(loaded,'neutral');tables=loaded;
 direction.disabled=shoot.disabled=false;status.textContent='Escolha uma direção para calcular o voo livre. A prévia não determina o resultado.';
}catch{status.textContent='Tabelas locais indisponíveis. Extraia os vetores da sua ROM para usar esta prévia.';}
