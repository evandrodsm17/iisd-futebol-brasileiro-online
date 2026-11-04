import {createNativeSlideBody} from '../native-slide-body.mjs';

// Same renderer as the match; unsupported directions are displayed explicitly.
export async function startSlideDemo(doc,env={}){
 const byId=id=>doc.getElementById(id),fetcher=env.fetch??fetch,schedule=env.requestFrame??requestAnimationFrame;
 const makeCanvas=env.makeCanvas??((w,h)=>{const c=doc.createElement('canvas');c.width=w;c.height=h;return c;});
 const el=Object.fromEntries(['team','kit','direction','skin','hair','demo','play','tick','frame','status'].map(k=>[k,byId('slide-'+k)]));
 if(Object.values(el).some(v=>!v))throw Error('Painel de carrinho incompleto');
 const read=async path=>{const r=await fetcher(path);if(!r.ok)throw Error('Dados locais indisponíveis: '+path);return r.json();};
 const [data,motion,preview,catalog]=await Promise.all([read('../assets/issd/slide-lab-local/preview.json'),read('../assets/issd/runtime-body-local.json'),read('../assets/issd/editor-preview-local.json'),read('../data/issd-rom-catalog.json')]);
 const leftResponse=await fetcher('../assets/issd/slide-lab-local/left.json');
 const left=leftResponse.ok?await leftResponse.json():null;
 const renderer=createNativeSlideBody(data,motion,makeCanvas,preview,left),ctx=el.demo.getContext('2d');
 el.team.replaceChildren(...catalog.teams.map(t=>{const o=doc.createElement('option');o.value=String(t.id);o.textContent=t.name;return o;}));el.team.value='30';
 el.hair.replaceChildren(...Array.from({length:14},(_,i)=>{const o=doc.createElement('option');o.value=String(i);o.textContent=String(i);return o;}));el.hair.value='0';
 let playing=true,tick=0,last=null;
 function draw(){
  const current=Math.min(renderer.duration-1,Math.floor(tick)),team=Number(el.team.value),kit=el.kit.value;
  el.tick.max=String(renderer.duration-1);el.tick.value=String(current);el.frame.textContent=`${current+1} / ${renderer.duration}`;
  const request={team,kit,appearance:{skin_tone:Number(el.skin.value),hair_style:Number(el.hair.value)},position:'DF',screenDirection:Number(el.direction.value),palette:catalog.teams[team]?.kit?.[kit]?.sprite_palette};
  ctx.clearRect(0,0,96,96);ctx.imageSmoothingEnabled=false;
  if(!renderer.supports(request)){el.status.textContent='Direção ou aparência ainda não disponível na partida.';return;}
  try{const image=renderer.frame(current,request);if(!image)throw Error('Quadro indisponível');ctx.drawImage(image,0,0);el.status.textContent='Corpo capturado, com cores da equipe; camada de cabelo ainda não validada.';}
  catch(error){el.status.textContent='Não foi possível montar o carrinho: '+error.message;}
 }
 const reset=()=>{tick=0;last=null;draw();};
 for(const k of ['team','kit','direction','skin','hair'])el[k].addEventListener('change',reset);
 el.play.disabled=false;el.play.addEventListener('click',()=>{playing=!playing;el.play.textContent=playing?'Pausar':'Reproduzir';last=null;});
 el.tick.addEventListener('input',()=>{tick=Math.min(renderer.duration-1,Math.max(0,Number(el.tick.value)||0));playing=false;el.play.textContent='Reproduzir';last=null;draw();});
 function animate(now){if(last!==null&&playing)tick=(tick+Math.min(100,Math.max(0,now-last))*60/1000)%renderer.duration;last=now;draw();schedule(animate);}
 draw();schedule(animate);
}
