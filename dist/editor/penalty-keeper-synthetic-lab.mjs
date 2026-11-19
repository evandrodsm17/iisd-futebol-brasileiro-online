const canvas=document.querySelector('#penalty-synthetic-keeper');
const direction=document.querySelector('#penalty-synthetic-keeper-direction');
const play=document.querySelector('#penalty-synthetic-keeper-play');
const slider=document.querySelector('#penalty-synthetic-keeper-frame');
const counter=document.querySelector('#penalty-synthetic-keeper-counter');
const status=document.querySelector('#penalty-synthetic-keeper-status');
const context=canvas.getContext('2d');
let captures=new Map(),animation=0;
function draw(){
 const selected=captures.get(direction.value),index=Number(slider.value)-1;
 context.clearRect(0,0,canvas.width,canvas.height);
 if(selected?.data.frames[index]){
  const {width,height}=selected.data;
  context.imageSmoothingEnabled=false;
  context.drawImage(selected.image,index*width,0,width,height,Math.floor((canvas.width-width)/2),Math.floor((canvas.height-height)/2),width,height);
  status.textContent='Quadro validado contra a captura. Ensaio sintético; a configuração natural de dois jogadores e a animação completa ainda precisam de validação.';
 }else status.textContent='Quadro sem associação validada; escolha outro quadro.';
 counter.textContent=`${index+1} / 40`;
}
function stop(){cancelAnimationFrame(animation);animation=0;}
slider.addEventListener('input',()=>{stop();draw();});
direction.addEventListener('change',()=>{stop();slider.value='2';draw();});
play.addEventListener('click',()=>{
 stop();let start;
 const update=now=>{if(start===undefined)start=now;const index=Math.min(39,Math.floor((now-start)*60/1000));slider.value=String(index+1);draw();if(index<39)animation=requestAnimationFrame(update);};
 animation=requestAnimationFrame(update);
});
try{
 const response=await fetch('../assets/issd/penalty-keeper-synthetic-local.json');if(!response.ok)throw new Error('manifest unavailable');
 const manifest=await response.json();
 if(manifest.schema!=='issd-penalty-keeper-synthetic-preview/v1'||manifest.frame_count!==40||!Array.isArray(manifest.captures))throw new Error('invalid manifest');
 for(const item of manifest.captures){
  if(!['Left','Right'].includes(item.direction)||!Number.isInteger(item.width)||!Number.isInteger(item.height)||item.width<1||item.width>canvas.width||item.height<1||item.height>canvas.height||!Array.isArray(item.frames)||item.frames.length!==40)throw new Error('invalid capture');
  const image=new Image();image.src=`../assets/issd/penalty-keeper-synthetic-${item.direction.toLowerCase()}-local.png`;await image.decode();
  if(image.naturalWidth!==item.width*40||image.naturalHeight!==item.height)throw new Error('invalid atlas');
  captures.set(item.direction,{data:item,image});
 }
 if(captures.size!==2)throw new Error('missing direction');
 direction.disabled=play.disabled=slider.disabled=false;draw();
}catch{status.textContent='Capturas locais indisponíveis. Gere a prévia a partir dos dados locais para visualizá-la.';}
