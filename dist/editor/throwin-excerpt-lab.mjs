const byId=id=>document.getElementById('throwin-excerpt'+id);
const side=byId('-side'),play=byId('-play'),slider=byId('-tick'),label=byId('-frame'),status=byId('-status'),canvas=byId('');
const ctx=canvas.getContext('2d'),base='../assets/issd/slide-lab-local/throwin-excerpt/';
let frames=[],tick=0,last=null,playing=true,loadId=0;
function loadImage(url){return new Promise((resolve,reject)=>{const img=new Image();img.onload=()=>resolve(img);img.onerror=()=>reject(Error('Quadro local indisponível.'));img.src=url;});}
function draw(){if(!frames.length)return;const index=Math.min(frames.length-1,Math.floor(tick));ctx.clearRect(0,0,160,128);ctx.imageSmoothingEnabled=false;ctx.drawImage(frames[index].image,0,0);slider.value=String(index);label.textContent=`${index+1} / ${frames.length}`;}
async function load(){
 const id=++loadId;status.textContent='Carregando trecho local…';play.disabled=true;slider.disabled=true;
 try{
  const root=base+side.value+'/',response=await fetch(root+'manifest.json');if(!response.ok)throw Error('Trecho local indisponível. Gere-o a partir da captura.');
  const data=await response.json();
  if(data.schema!=='issd-throwin-excerpt/v1'||data.width!==160||data.height!==128||data.ticks_per_second!==60||!Array.isArray(data.frames)||!data.frames.length||data.frames.some((f,i)=>!Number.isInteger(f.prepared_frame)||(i&&f.prepared_frame!==data.frames[i-1].prepared_frame+1)||f.file!==`frame-${f.prepared_frame}.png`))throw Error('Trecho local inválido.');
  const images=await Promise.all(data.frames.map(f=>loadImage(root+f.file)));if(id!==loadId)return;
  if(images.some(img=>img.naturalWidth!==160||img.naturalHeight!==128))throw Error('Dimensões dos quadros inválidas.');
  frames=data.frames.map((f,i)=>({...f,image:images[i]}));tick=0;last=null;slider.max=String(frames.length-1);slider.disabled=false;play.disabled=false;status.textContent='Trecho parcial validado com a trajetória capturada da bola.';draw();
 }catch(error){if(id===loadId){frames=[];ctx.clearRect(0,0,160,128);status.textContent=error.message;}}
}
side.addEventListener('change',load);play.addEventListener('click',()=>{playing=!playing;play.textContent=playing?'Pausar':'Reproduzir';last=null;});
slider.addEventListener('input',()=>{tick=Number(slider.value);playing=false;play.textContent='Reproduzir';last=null;draw();});
function animate(now){if(last!==null&&playing&&frames.length){tick=(tick+Math.min(100,Math.max(0,now-last))*60/1000)%frames.length;draw();}last=now;requestAnimationFrame(animate);}
load();requestAnimationFrame(animate);
