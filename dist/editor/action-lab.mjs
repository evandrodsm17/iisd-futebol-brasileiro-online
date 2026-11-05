import {createNativeShotBody} from '../native-shot-body.mjs';
import {createNativePassBody} from '../native-pass-body.mjs';
import {actionAssetPath,actionFrame,directionForAction,durationInTicks} from '../action-visual.mjs';

// The panel uses the same renderers and timing selection as the match. It never
// changes match state and never invents a missing action or direction.
export async function startActionLab(doc, env={}){
 const byId=id=>doc.getElementById(id), fetcher=env.fetch??fetch, schedule=env.requestFrame??requestAnimationFrame;
 const makeCanvas=env.makeCanvas??((w,h)=>{const c=doc.createElement('canvas');c.width=w;c.height=h;return c;});
 const makeImage=env.makeImage??(()=>new Image());
 const el=Object.fromEntries(['kind','team','kit','direction','skin','hair','shirt','preview','play','tick','frame','status'].map(k=>[k,byId('action-'+k)]));
 if(Object.values(el).some(v=>!v))throw Error('Painel de ações incompleto');
 const read=async path=>{const r=await fetcher(path);if(!r.ok)throw Error('Dados locais ausentes: '+path);return r.json();};
 let pass=null,shot=null,catalog=null,passError=null,hairData=null;
 try{
  const [body,motion,preview,detail,teams,hair]=await Promise.all([
   read('../assets/issd/native-pass-body-local.json'),read('../assets/issd/runtime-body-local.json'),read('../assets/issd/editor-preview-local.json'),
   read('../data/issd-team-detail-colors.json'),read('../data/issd-rom-catalog.json'),read('../assets/issd/native-pass-hair-local.json').catch(()=>null)]);
  catalog=teams;hairData=hair;pass=createNativePassBody(body,makeCanvas,motion,preview,detail,hair);
  try{shot=createNativeShotBody(await read('../assets/issd/native-shot-body-local.json'),makeCanvas,motion,preview);}catch{}
 }catch(error){passError=error.message;}
 if(catalog?.teams?.length){
  el.team.replaceChildren(...catalog.teams.map(t=>{const o=doc.createElement('option');o.value=String(t.id);o.textContent=t.name;return o;}));
  el.team.value='30';
 }else{const o=doc.createElement('option');o.value='30';o.textContent='Brasil';el.team.replaceChildren(o);el.team.value='30';}
 el.hair.replaceChildren(...Array.from({length:14},(_,i)=>{const o=doc.createElement('option');o.value=String(i);o.textContent=String(i);return o;}));el.hair.value='0';
 let playing=true,tick=0,last=null;const images=new Map(),ctx=el.preview.getContext('2d');
 const duration=()=>el.kind.value==='shot'?durationInTicks('shot'):18;
 function showStatus(message){if(el.status.textContent!==message)el.status.textContent=message;}
 function draw(){
  const total=duration(),frame=Math.min(total-1,Math.floor(tick));el.tick.max=String(total-1);el.tick.value=String(frame);el.frame.textContent=`${frame+1} / ${total}`;
  ctx.clearRect(0,0,96,96);ctx.imageSmoothingEnabled=false;
  if(el.kind.value==='shot'){
   const screen=Number(el.direction.value),team=Number(el.team.value),kit=el.kit.value,skin=Number(el.skin.value),style=Number(el.hair.value);
   const request={team,kit,appearance:{skin_tone:skin,hair_style:style},position:'MF',screenDirection:screen,palette:catalog?.teams?.[team]?.kit?.[kit]?.sprite_palette};
   if(shot?.supports(request)){try{const image=shot.frame(frame,request),scale=96/shot.referenceHeight(screen);if(image){ctx.drawImage(image,48-48*scale,68-68*scale,96*scale,96*scale);showStatus('Chute composto para esta direção; cabelo e temporização ainda são provisórios.');return;}}catch(error){showStatus('Falha ao compor chute: '+error.message);return;}}
   const dir=directionForAction('shot',screen),path=actionAssetPath('shot',dir);
   if(!path){showStatus('Chute não disponível nesta direção.');return;}
   if(!images.has(path)){
    const img=makeImage();images.set(path,img);img.onload=()=>draw();img.onerror=()=>{img.failed=true;draw();};img.src='../'+path.replace(/^\.\//,'');
   }
   const img=images.get(path);
   if(img.failed){showStatus('Folha local de chute indisponível.');return;}
   if(!img.complete||!img.naturalWidth){showStatus('Carregando chute…');return;}
   ctx.drawImage(img,actionFrame('shot',frame)*96,0,96,96,0,0,96,96);
   showStatus('Chute provisório: folha capturada, aparência fixa e direção aproximada.');return;
  }
  if(!pass||!catalog){showStatus('Passe local indisponível. '+(passError??''));return;}
  const team=Number(el.team.value),kit=el.kit.value,screenDirection=Number(el.direction.value),skin=Number(el.skin.value),style=Number(el.hair.value);
  const request={team,kit,appearance:{skin_tone:skin,hair_style:style},position:'MF',screenDirection,shirtNumber:Number(el.shirt.value),palette:catalog.teams[team]?.kit?.[kit]?.sprite_palette};
  if(!pass.supports(request)){showStatus('Essa combinação ainda usa a pose de reserva na partida.');return;}
  try{
   const image=pass.frame(frame,request);if(!image){showStatus('Quadro de passe indisponível.');return;}
   const scale=96/pass.referenceHeight(screenDirection);
   ctx.drawImage(image,48-48*scale,68-68*scale,96*scale,96*scale);
   const hairReady=style===0||hairData?.schema==='issd-pass-hair-local/v1'&&hairData.screen_direction===screenDirection&&Array.isArray(hairData.styles?.[style]);
   showStatus(hairReady?'Passe composto com os dados locais; a física da partida permanece provisória.':'Passe composto; camada de cabelo desta direção ainda não foi validada.');
  }catch(error){showStatus('Não foi possível montar o passe: '+error.message);}
 }
 function reset(){tick=0;last=null;draw();}
 for(const k of ['kind','team','kit','direction','skin','hair','shirt'])el[k].addEventListener('change',reset);
 el.play.disabled=false;el.play.addEventListener('click',()=>{playing=!playing;el.play.textContent=playing?'Pausar':'Reproduzir';last=null;});
 el.tick.addEventListener('input',()=>{tick=Math.min(duration()-1,Math.max(0,Number(el.tick.value)||0));playing=false;el.play.textContent='Reproduzir';last=null;draw();});
 function animate(now){if(last!==null&&playing)tick=(tick+Math.min(100,Math.max(0,now-last))*60/1000)%duration();last=now;draw();schedule(animate);}
 draw();schedule(animate);
}
