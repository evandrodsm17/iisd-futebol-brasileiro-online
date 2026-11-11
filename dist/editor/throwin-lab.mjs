const select=document.getElementById('throwin-sample');
const preview=document.getElementById('throwin-preview');
const status=document.getElementById('throwin-status');
const base='../assets/issd/slide-lab-local/throwin-gallery/';
const names={Up:'Cima',Down:'Baixo',Left:'Esquerda',Right:'Direita'};
try{
 const response=await fetch(base+'manifest.json');
 if(!response.ok)throw Error('Prévia local indisponível. Gere as amostras a partir da captura e da ROM local.');
 const data=await response.json();
 if(data.schema!=='issd-throwin-body-gallery/v1'||!Array.isArray(data.samples)||!data.samples.length||data.samples.some(s=>!names[s.input]||!['upper','lower'].includes(s.side)||!Number.isInteger(s.descriptor)||!/^(upper|lower)-(up|down|left|right)-[0-9a-f]{4}\.png$/.test(s.file)))throw Error('Dados locais das poses inválidos.');
 select.replaceChildren(...data.samples.map((sample,index)=>{
  const option=document.createElement('option');option.value=String(index);option.textContent=`${sample.side==='lower'?'Lateral inferior':'Lateral superior'} · ${names[sample.input]} · pose $${sample.descriptor.toString(16).toUpperCase()}`;return option;
 }));
 function show(){const sample=data.samples[Number(select.value)];if(!sample)return;preview.hidden=true;preview.src=base+sample.file;status.textContent=`Pose validada · quadro ${sample.displayed_frame} da captura.`;}
 preview.onload=()=>{preview.hidden=false;};preview.onerror=()=>{preview.hidden=true;status.textContent='Não foi possível carregar a pose local.';};
 select.addEventListener('change',show);select.disabled=false;show();
}catch(error){status.textContent=error.message;}
