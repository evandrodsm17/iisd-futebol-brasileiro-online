import {replayPenaltyKeeperWithGate} from '../penalty-keeper-replay.mjs';

const direction=document.querySelector('#penalty-motion-keeper-direction');
const play=document.querySelector('#penalty-motion-keeper-play');
const slider=document.querySelector('#penalty-motion-keeper-frame');
const counter=document.querySelector('#penalty-motion-keeper-counter');
const status=document.querySelector('#penalty-motion-keeper-status');
const canvas=document.querySelector('#penalty-motion-keeper-canvas');
const ctx=canvas.getContext('2d');
const signed24=value=>value&0x800000?value-0x1000000:value;
const point=state=>({x:state.x/256,y:128+signed24(state.z)/256});
let captures=null,frames=null,timer=null;
function stop(){if(timer!==null)clearTimeout(timer);timer=null;play.textContent='Reproduzir';}
function draw(){
 const frame=frames[Number(slider.value)-1],p=point(frame.after);
 ctx.fillStyle='#123c30';ctx.fillRect(0,0,canvas.width,canvas.height);
 ctx.strokeStyle='#8bb9a4';ctx.beginPath();ctx.moveTo(0,128.5);ctx.lineTo(256,128.5);ctx.stroke();
 ctx.strokeStyle='#64a9c8';ctx.beginPath();
 frames.forEach((entry,index)=>{const q=point(entry.after);if(index===0)ctx.moveTo(q.x,q.y);else ctx.lineTo(q.x,q.y);});ctx.stroke();
 ctx.fillStyle='#8fdaff';ctx.beginPath();ctx.arc(p.x,p.y,4,0,Math.PI*2);ctx.fill();
 counter.textContent=`${slider.value} / ${frames.length}`;
 status.textContent=`Quadro ${frame.frame} · posição e velocidade calculadas e conferidas com a captura. As condições usadas no cálculo foram registradas; isto não prevê outras cobranças.`;
}
function next(){
 if(Number(slider.value)>=frames.length){stop();return;}
 timer=setTimeout(()=>{slider.value=String(Number(slider.value)+1);draw();next();},1000/60);
}
function choose(){
 stop();
 try{
  const matches=captures.filter(entry=>entry.direction===direction.value);
  if(matches.length!==1)throw new Error('Missing keeper capture');
  frames=replayPenaltyKeeperWithGate(matches[0]);slider.max=String(frames.length);slider.value='1';slider.disabled=false;play.disabled=frames.length<2;draw();
 }catch{frames=null;slider.disabled=play.disabled=true;counter.textContent='';status.textContent='Não foi possível validar esta trajetória.';}
}
direction.addEventListener('change',choose);
slider.addEventListener('input',()=>{stop();draw();});
play.addEventListener('click',()=>{
 if(timer!==null){stop();return;}
 if(!frames||frames.length<2)return;
 if(Number(slider.value)>=frames.length){slider.value='1';draw();}
 play.textContent='Pausar';next();
});
try{
 const response=await fetch('../data/issd-penalty-keeper-motion.json');if(!response.ok)throw new Error('Missing keeper data');
 const data=await response.json();if(data.schema!=='issd-penalty-keeper-motion/v1'||!Array.isArray(data.captures))throw new Error('Invalid keeper data');
 captures=data.captures;direction.disabled=false;choose();
}catch{status.textContent='Trajetórias capturadas indisponíveis.';}
