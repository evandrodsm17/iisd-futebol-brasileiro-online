import {projectPitchToSource} from '../stadium-pitch-projection.mjs';

const select=document.querySelector('#pitch-layout'),canvas=document.querySelector('#pitch-preview'),status=document.querySelector('#pitch-status');
const ctx=canvas.getContext('2d'),field={x:0,y:0,w:1,h:1};let generation=0;
function load(){
 const id=Number(select.value),serial=++generation,image=new Image();
 status.textContent='Carregando estádio…';
 image.onload=()=>{
  if(serial!==generation)return;
  const scale=Math.min(canvas.width/image.naturalWidth,canvas.height/image.naturalHeight),ox=(canvas.width-image.naturalWidth*scale)/2,oy=(canvas.height-image.naturalHeight*scale)/2;
  const point=(x,y)=>{const p=projectPitchToSource(x,y,field,id);return {x:ox+p.x*scale,y:oy+p.y*scale};};
  ctx.clearRect(0,0,canvas.width,canvas.height);ctx.imageSmoothingEnabled=false;ctx.drawImage(image,ox,oy,image.naturalWidth*scale,image.naturalHeight*scale);
  const corners=[[0,0],[1,0],[1,1],[0,1]].map(([x,y])=>point(x,y));ctx.beginPath();ctx.moveTo(corners[0].x,corners[0].y);for(const p of corners.slice(1))ctx.lineTo(p.x,p.y);ctx.closePath();ctx.strokeStyle='#ffe66a';ctx.lineWidth=2;ctx.stroke();
  for(const [x,y] of [[0,0],[1,0],[1,1],[0,1],[.5,.5],[0,.5],[1,.5]]){const p=point(x,y);ctx.beginPath();ctx.arc(p.x,p.y,4,0,Math.PI*2);ctx.fillStyle='#42d6ff';ctx.fill();}
  status.textContent='Linhas medidas na imagem; controles, câmera e traves ainda precisam de validação na partida.';
 };
 image.onerror=()=>{if(serial===generation)status.textContent='Não foi possível carregar a imagem do estádio.';};
 image.src=`../assets/issd/stadium/layout-${id}.png`;
}
select.addEventListener('change',load);load();
