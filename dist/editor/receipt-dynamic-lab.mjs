import {createNativeReceiptBody} from '../native-throwin-body.mjs';
import {createNativeCapturedAction} from '../native-jump-body.mjs';
const byId=id=>document.getElementById('receipt-dynamic-'+id);
const context=byId('context'),team=byId('team'),kit=byId('kit'),skin=byId('skin'),shirt=byId('shirt'),play=byId('play'),canvas=byId('preview'),status=byId('status');
const read=async path=>{const response=await fetch(path);if(!response.ok)throw Error('Dados locais de recepção indisponíveis.');return response.json();};
try{
 const [data,motion,preview,colors,catalog]=await Promise.all([read('../assets/issd/slide-lab-local/receipt-dynamic.json'),read('../assets/issd/runtime-body-local.json'),read('../assets/issd/editor-preview-local.json'),read('../data/issd-team-detail-colors.json'),read('../data/issd-rom-catalog.json')]);
 const make=(w,h)=>{const c=document.createElement('canvas');c.width=w;c.height=h;return c;};
 const renderer=createNativeReceiptBody(data,motion,make,preview,colors),ctx=canvas.getContext('2d');
 const extra=await fetch('../assets/issd/slide-lab-local/receipt-contested-dynamic.json');
 const contested=extra.ok?createNativeCapturedAction(await extra.json(),preview,colors,make,{schema:'issd-contested-receipt-local/v1',duration:44}):null;
 if(!contested)context.querySelector('option[value=contested]').disabled=true;
 team.replaceChildren(...catalog.teams.map(t=>{const option=document.createElement('option');option.value=String(t.id);option.textContent=t.name;return option;}));team.value='26';team.disabled=false;play.disabled=false;
 let tick=0,last=null,playing=true;
 function draw(){const id=Number(team.value),uniform=kit.value,isContested=context.value==='contested',active=isContested?contested:renderer,base={team:id,kit:uniform,shirtNumber:Number(shirt.value),palette:catalog.teams[id]?.kit?.[uniform]?.sprite_palette},request=isContested?{...base,skin:Number(skin.value),screenDirection:2}:{...base,appearance:{skin_tone:Number(skin.value),hair_style:0},position:'DF',screenDirection:3};ctx.clearRect(0,0,96,96);ctx.imageSmoothingEnabled=false;if(!active?.supports(request)){status.textContent='Combinação não disponível.';return;}const frame=active.frame(Math.floor(tick),request);if(frame)ctx.drawImage(frame,0,0);status.textContent='Corpo e uniforme compostos para o contexto capturado.';}
 for(const element of [context,team,kit,skin,shirt])element.addEventListener('change',()=>{tick=0;last=null;draw();});
 play.addEventListener('click',()=>{playing=!playing;play.textContent=playing?'Pausar':'Reproduzir';last=null;});
 function animate(now){if(playing&&last!==null)tick=(tick+Math.min(100,Math.max(0,now-last))*60/1000)%renderer.duration;last=now;draw();requestAnimationFrame(animate);}draw();requestAnimationFrame(animate);
}catch(error){status.textContent=error.message;}
