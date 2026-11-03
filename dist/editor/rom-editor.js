import {emptyOverrides,applyRomOverrides,loadRomOverrides,saveRomOverrides,renameRomEntry,validateOverrides,updateRomPlayer,ROM_ATTRIBUTES,ROM_POSITIONS} from './rom-overrides.mjs';
import {previewPixels,drawPreview} from './rom-player-preview.mjs';
const $=id=>document.getElementById(id);
let base=null,overrides=loadRomOverrides(),selected=0,previewData=null;
function notice(message){$('status').textContent=message;}
function commit(next){overrides=next;saveRomOverrides(next);render();notice('Alterações salvas. A aparência visual ainda está em desenvolvimento.');}
function render(){
 if(!base)return;
 const view=applyRomOverrides(base,overrides),team=view.teams[selected],original=base.teams[selected];
 $('teams').replaceChildren(...view.teams.filter(t=>t.name.toLowerCase().includes($('search').value.toLowerCase())).map(t=>{
  const button=document.createElement('button');button.type='button';button.textContent=String(t.id+1).padStart(2,'0')+' · '+t.name;button.className=t.id===selected?'selected':'';button.onclick=()=>{selected=t.id;render();};return button;
 }));
 $('title').textContent=team.name;$('team-name').value=team.name;
 const originalRoster=base.teams.flatMap(t=>t.players.map((p,slot)=>({...p,rom_origin_team_id:t.id,rom_origin_slot:slot})));
 $('players').replaceChildren(...team.players.map(p=>{
  const teamId=p.rom_origin_team_id,slot=p.rom_origin_slot;
  const original=base.teams[teamId].players[slot];
  const form=document.createElement('form');form.className='player-edit';
  const heading=document.createElement('strong');heading.textContent=p.name+' · origem '+base.teams[teamId].name;
  const makeInput=(label,value,type='text')=>{const wrapper=document.createElement('label');wrapper.textContent=label;const input=document.createElement('input');input.type=type;input.value=value;input.name=label;if(type==='number'){input.min='1';input.max='99';}wrapper.append(input);form.append(wrapper);return input;};
  form.append(heading);
  const name=makeInput('Nome',p.name);
  const number=makeInput('Camisa',p.shirt_number,'number');
  const positionLabel=document.createElement('label');positionLabel.textContent='Posição';const position=document.createElement('select');
  position.replaceChildren(...ROM_POSITIONS.map(pos=>new Option(pos,pos,false,p.position===pos)));positionLabel.append(position);form.append(positionLabel);
  const destinationLabel=document.createElement('label');destinationLabel.textContent='Equipe';const destination=document.createElement('select');
  destination.replaceChildren(...view.teams.map(t=>new Option(t.name,t.id,false,t.id===team.id)));destinationLabel.append(destination);form.append(destinationLabel);
  const appearanceLabel=document.createElement('label');appearanceLabel.textContent='Cabelo (código original)';const hair=document.createElement('select');
  hair.replaceChildren(...Array.from({length:14},(_,i)=>new Option(i===0?'Padrão':`Estilo ${i}`,i,false,i===(p.appearance?.hair_style??0))));appearanceLabel.append(hair);form.append(appearanceLabel);
  const skinLabel=document.createElement('label');skinLabel.textContent='Paleta de pele';const skin=document.createElement('select');
  skin.replaceChildren(...['Normal','Alternativa'].map((label,i)=>new Option(label,i,false,i===(p.appearance?.skin_tone??0))));skinLabel.append(skin);form.append(skinLabel);
  const appearanceNote=document.createElement('small');appearanceNote.textContent='Dados salvos; a personalização visual ainda não é aplicada na partida.';form.append(appearanceNote);
  if(previewData){
   let direction=0;
   const box=document.createElement('div');box.className='player-preview';
   const canvas=document.createElement('canvas');canvas.className='preview-sprite';canvas.setAttribute('aria-label','Prévia do jogador');
   const controls=document.createElement('div');controls.className='preview-controls';
   const prev=document.createElement('button'),next=document.createElement('button'),choose=document.createElement('button');
   prev.type=next.type=choose.type='button';prev.textContent='← Girar';next.textContent='Girar →';choose.textContent='Escolher cabelo';
   const current=()=>previewPixels(previewData,team.id,direction,position.value,Number(skin.value),Number(hair.value));
   const paint=()=>{try{drawPreview(canvas,current());}catch(error){notice('Falha na prévia: '+error.message);}};
   prev.onclick=()=>{direction=(direction+7)%8;paint();};next.onclick=()=>{direction=(direction+1)%8;paint();};
   hair.onchange=skin.onchange=position.onchange=paint;
   choose.onclick=()=>{
    const dialog=document.createElement('dialog');dialog.className='hair-picker';
    const title=document.createElement('h3');title.textContent='Escolher cabelo · '+name.value;dialog.append(title);
    const grid=document.createElement('div');grid.className='hair-grid';
    for(let style=0;style<14;style++){
     const option=document.createElement('button');option.type='button';option.title=style===0?'Padrão':'Estilo '+style;
     const mini=document.createElement('canvas');mini.className='hair-option-preview';
     drawPreview(mini,previewPixels(previewData,team.id,direction,position.value,Number(skin.value),style));
     option.append(mini,document.createTextNode(style===0?'Padrão':String(style)));
     option.onclick=()=>{hair.value=String(style);paint();dialog.close();};grid.append(option);
    }
    const close=document.createElement('button');close.type='button';close.textContent='Fechar';close.onclick=()=>dialog.close();
    dialog.append(grid,close);dialog.addEventListener('close',()=>dialog.remove(),{once:true});document.body.append(dialog);dialog.showModal();
   };
   controls.append(prev,next,choose);box.append(canvas,controls);form.append(box);paint();
  }
  const attrs=document.createElement('details');const summary=document.createElement('summary');summary.textContent='Atributos técnicos';attrs.append(summary);
  const inputs={};
  for(const key of ROM_ATTRIBUTES){const wrapper=document.createElement('label');wrapper.textContent=key;const input=document.createElement('input');input.type='number';input.min='1';input.max='99';input.value=p.attributes[key];inputs[key]=input;wrapper.append(input);attrs.append(wrapper);}
  form.append(attrs);
  const buttons=document.createElement('div');buttons.className='player-buttons';
  const save=document.createElement('button');save.type='submit';save.textContent='Salvar jogador';
  const revert=document.createElement('button');revert.type='button';revert.textContent='Restaurar original';
  buttons.append(save,revert);form.append(buttons);
  const values=()=>({name:name.value,position:position.value,shirt_number:number.valueAsNumber,target_team_id:Number(destination.value),appearance:{hair_style:Number(hair.value),skin_tone:Number(skin.value)},attributes:Object.fromEntries(ROM_ATTRIBUTES.map(k=>[k,inputs[k].valueAsNumber]))});
  form.onsubmit=event=>{event.preventDefault();try{commit(updateRomPlayer(overrides,teamId,slot,values(),original));}catch(error){notice(error.message);}};
  revert.onclick=()=>{try{commit(updateRomPlayer(overrides,teamId,slot,{...original,target_team_id:teamId},original));}catch(error){notice(error.message);}};
  return form;
 }));
}
$('search').oninput=render;
$('edit-team').onsubmit=e=>{e.preventDefault();try{commit(renameRomEntry(overrides,'team',selected,null,$('team-name').value,base.teams[selected].name));}catch(error){notice(error.message);}};
$('revert-team').onclick=()=>commit(renameRomEntry(overrides,'team',selected,null,base.teams[selected].name,base.teams[selected].name));
$('reset').onclick=()=>{if(confirm('Restaurar todos os nomes originais?'))commit(emptyOverrides());};
$('export').onclick=()=>{const url=URL.createObjectURL(new Blob([JSON.stringify(overrides,null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download='issd-nomes-editados.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);};
$('import').onchange=async e=>{const file=e.target.files?.[0];if(!file)return;try{if(file.size>1024*1024)throw Error('Arquivo excede 1 MB');const imported=validateOverrides(JSON.parse(await file.text()));commit(imported);}catch(error){notice(error.message);}e.target.value='';};
try{const [response,preview]=await Promise.all([fetch('../data/issd-rom-catalog.json'),fetch('../assets/issd/editor-preview-local.json').catch(()=>null)]);if(!response.ok)throw Error('Falha ao obter catálogo');base=await response.json();if(preview?.ok)previewData=await preview.json();render();notice(previewData?'Catálogo e prévia local carregados.':'Catálogo carregado. Gere a prévia local seguindo o manual do editor.');}catch(error){notice(error.message);}
