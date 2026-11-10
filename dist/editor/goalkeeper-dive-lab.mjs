import {createKeeperDive} from '../native-keeper-dive.mjs';
const canvas=document.querySelector('#keeper-dive-preview'),status=document.querySelector('#keeper-dive-status'),slider=document.querySelector('#keeper-dive-tick'),button=document.querySelector('#keeper-dive-play'),counter=document.querySelector('#keeper-dive-frame');
try{
 const responses=await Promise.all(['../assets/issd/native-keeper-dive-local.json','../assets/issd/editor-preview-local.json'].map(path=>fetch(path)));
 if(responses.some(r=>!r.ok))throw Error('dados locais indisponíveis');
 const [data,preview]=await Promise.all(responses.map(r=>r.json()));
 const renderer=createKeeperDive(data,preview,(w,h)=>{const c=document.createElement('canvas');c.width=w;c.height=h;return c;});
 const ctx=canvas.getContext('2d'),request={team:30,skin:0,screenDirection:6};let tick=0,playing=true,last=null;
 slider.max=String(renderer.duration-1);slider.disabled=false;button.disabled=false;
 const draw=()=>{const frame=Math.floor(tick),image=renderer.frame(frame,request);ctx.clearRect(0,0,96,96);ctx.imageSmoothingEnabled=false;if(image)ctx.drawImage(image,0,0);slider.value=String(frame);counter.textContent=`${frame+1} / ${renderer.duration}`;};
 button.addEventListener('click',()=>{playing=!playing;button.textContent=playing?'Pausar':'Reproduzir';last=null;});
 slider.addEventListener('input',()=>{tick=Number(slider.value);playing=false;button.textContent='Reproduzir';draw();});
 status.textContent='Três poses da ROM, verificadas em replay sintético; uma orientação disponível.';
 const animate=now=>{if(last!==null&&playing)tick=(tick+Math.min(100,Math.max(0,now-last))*60/1000)%renderer.duration;last=now;draw();requestAnimationFrame(animate);};
 draw();requestAnimationFrame(animate);
}catch(error){status.textContent='Mergulho local indisponível: '+error.message;}
