import {emptyOverrides,applyRomOverrides,loadRomOverrides,saveRomOverrides,renameRomEntry,validateOverrides,updateRomPlayer,ROM_ATTRIBUTES,ROM_POSITIONS} from './rom-overrides.mjs';
const $=id=>document.getElementById(id);
let base=null,overrides=loadRomOverrides(),selected=0;
function notice(message){$('status').textContent=message;}
function commit(next){overrides=next;saveRomOverrides(next);render();notice('Alterações salvas. Recarregue a partida para atualizar os nomes.');}
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
  const attrs=document.createElement('details');const summary=document.createElement('summary');summary.textContent='Atributos técnicos';attrs.append(summary);
  const inputs={};
  for(const key of ROM_ATTRIBUTES){const wrapper=document.createElement('label');wrapper.textContent=key;const input=document.createElement('input');input.type='number';input.min='1';input.max='99';input.value=p.attributes[key];inputs[key]=input;wrapper.append(input);attrs.append(wrapper);}
  form.append(attrs);
  const buttons=document.createElement('div');buttons.className='player-buttons';
  const save=document.createElement('button');save.type='submit';save.textContent='Salvar jogador';
  const revert=document.createElement('button');revert.type='button';revert.textContent='Restaurar original';
  buttons.append(save,revert);form.append(buttons);
  const values=()=>({name:name.value,position:position.value,shirt_number:number.valueAsNumber,target_team_id:Number(destination.value),attributes:Object.fromEntries(ROM_ATTRIBUTES.map(k=>[k,inputs[k].valueAsNumber]))});
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
try{const response=await fetch('../data/issd-rom-catalog.json');if(!response.ok)throw Error('Falha ao obter catálogo');base=await response.json();render();notice('Catálogo carregado: '+base.teams.length+' equipes.');}catch(error){notice(error.message);}
