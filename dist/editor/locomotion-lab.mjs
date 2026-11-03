const $=id=>document.getElementById(id),status=$('status');
const canvases=['body','hair','combined'].map(id=>$(id));
let manifest=null,style=null,frame=0,playing=true,last=0,images={};
function draw(){
 if(!style||!images.body||!images.hair)return;
 const size=manifest.cell_size;
 for(let i=0;i<canvases.length;i++){
  const ctx=canvases[i].getContext('2d');ctx.clearRect(0,0,size,size);ctx.imageSmoothingEnabled=false;
  if(i!==1)ctx.drawImage(images.body,frame*size,0,size,size,0,0,size,size);
  if(i!==0)ctx.drawImage(images.hair,frame*size,0,size,size,0,0,size,size);
 }
 $('frame').value=String(frame);$('frame-label').textContent=`${frame+1} / ${style.frames}`;
}
function loadImage(url){return new Promise((resolve,reject)=>{const image=new Image();image.onload=()=>resolve(image);image.onerror=()=>reject(Error('Não foi possível carregar as camadas locais.'));image.src=url;});}
let loadId=0;
async function selectStyle(value){
 const current=++loadId;const chosen=manifest.styles.find(item=>item.style===Number(value));
 if(!chosen)throw Error('Estilo indisponível');
 const root='../assets/issd/hair-lab-local/';const [body,hair]=await Promise.all([loadImage(root+chosen.body),loadImage(root+chosen.hair)]);
 if(current!==loadId)return;
 const width=manifest.cell_size*chosen.frames;
 if(body.naturalWidth!==width||hair.naturalWidth!==width||body.naturalHeight!==manifest.cell_size||hair.naturalHeight!==manifest.cell_size)throw Error('Dimensões das camadas não conferem.');
 style=chosen;images={body,hair};frame=0;$('frame').max=String(chosen.frames-1);draw();
}
$('style').onchange=()=>selectStyle($('style').value).catch(error=>{status.textContent=error.message;});
$('frame').oninput=()=>{frame=Number($('frame').value);draw();};
$('play').onclick=()=>{playing=!playing;$('play').textContent=playing?'Pausar':'Reproduzir';};
function tick(now){if(playing&&style&&now-last>=130){frame=(frame+1)%style.frames;last=now;draw();}requestAnimationFrame(tick);}
try{
 const response=await fetch('../assets/issd/hair-lab-local/manifest.json');
 if(!response.ok)throw Error('Dados locais não encontrados. Gere a demonstração seguindo o manual do editor.');
 manifest=await response.json();
 if(manifest.schema!=='issd-hair-lab-local/v1'||manifest.cell_size!==64||!Array.isArray(manifest.styles)||!manifest.styles.length)throw Error('Dados da demonstração inválidos.');
 $('style').replaceChildren(...manifest.styles.map(item=>new Option(`Estilo ${item.style}`,item.style)));
 await selectStyle(manifest.styles[0].style);status.textContent='Camadas locais carregadas.';requestAnimationFrame(tick);
}catch(error){status.textContent=error.message;$('play').disabled=true;$('style').disabled=true;$('frame').disabled=true;}
