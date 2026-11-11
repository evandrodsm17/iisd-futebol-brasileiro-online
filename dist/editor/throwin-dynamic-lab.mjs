import {createNativeThrowBody} from '../native-throwin-body.mjs';
const byId=id=>document.getElementById('throw-dynamic-'+id);
const team=byId('team'),kit=byId('kit'),side=byId('side'),skin=byId('skin'),shirt=byId('shirt'),play=byId('play'),canvas=byId('preview'),status=byId('status');
const read=async path=>{const response=await fetch(path);if(!response.ok)throw Error('Dados locais de lateral indisponíveis.');return response.json();};
try{
 const [data,motion,preview,colors,catalog]=await Promise.all([read('../assets/issd/slide-lab-local/throwin-dynamic.json'),read('../assets/issd/runtime-body-local.json'),read('../assets/issd/editor-preview-local.json'),read('../data/issd-team-detail-colors.json'),read('../data/issd-rom-catalog.json')]);
 const make=(w,h)=>{const c=document.createElement('canvas');c.width=w;c.height=h;return c;};
 const renderer=createNativeThrowBody(data,motion,make,preview,colors),ctx=canvas.getContext('2d');
 team.replaceChildren(...catalog.teams.map(t=>{const option=document.createElement('option');option.value=String(t.id);option.textContent=t.name;return option;}));team.value='26';team.disabled=false;play.disabled=false;
 let tick=0,last=null,playing=true;
 function draw(){const id=Number(team.value),uniform=kit.value,request={team:id,kit:uniform,appearance:{skin_tone:Number(skin.value),hair_style:0},position:'DF',screenDirection:Number(side.value),shirtNumber:Number(shirt.value),palette:catalog.teams[id]?.kit?.[uniform]?.sprite_palette};ctx.clearRect(0,0,96,96);ctx.imageSmoothingEnabled=false;if(!renderer.supports(request)){status.textContent='Combinação não disponível.';return;}const frame=renderer.frame(Math.floor(tick),request);if(frame)ctx.drawImage(frame,0,0);status.textContent='Corpo e uniforme compostos; cabelo ainda não validado.';}
 for(const element of [team,kit,side,skin,shirt])element.addEventListener('change',()=>{tick=0;last=null;draw();});
 play.addEventListener('click',()=>{playing=!playing;play.textContent=playing?'Pausar':'Reproduzir';last=null;});
 function animate(now){if(playing&&last!==null)tick=(tick+Math.min(100,Math.max(0,now-last))*60/1000)%renderer.duration;last=now;draw();requestAnimationFrame(animate);}draw();requestAnimationFrame(animate);
}catch(error){status.textContent=error.message;}
