import {emptyOverrides,applyRomOverrides,loadRomOverrides,saveRomOverrides,renameRomEntry,validateOverrides} from './rom-overrides.mjs';
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
 $('players').replaceChildren(...team.players.map((p,slot)=>{
  const row=document.createElement('div');row.className='player-row';
  const number=document.createElement('span');number.textContent='#'+p.shirt_number+' · '+p.position;
  const input=document.createElement('input');input.value=p.name;input.maxLength=90;input.setAttribute('aria-label','Nome do jogador '+String(slot+1));
  const save=document.createElement('button');save.textContent='Salvar';save.type='button';save.onclick=()=>{try{commit(renameRomEntry(overrides,'player',selected,slot,input.value,original.players[slot].name));}catch(e){notice(e.message);}};
  const revert=document.createElement('button');revert.textContent='Original';revert.type='button';revert.onclick=()=>commit(renameRomEntry(overrides,'player',selected,slot,original.players[slot].name,original.players[slot].name));
  row.append(number,input,save,revert);return row;
 }));
}
$('search').oninput=render;
$('edit-team').onsubmit=e=>{e.preventDefault();try{commit(renameRomEntry(overrides,'team',selected,null,$('team-name').value,base.teams[selected].name));}catch(error){notice(error.message);}};
$('revert-team').onclick=()=>commit(renameRomEntry(overrides,'team',selected,null,base.teams[selected].name,base.teams[selected].name));
$('reset').onclick=()=>{if(confirm('Restaurar todos os nomes originais?'))commit(emptyOverrides());};
$('export').onclick=()=>{const url=URL.createObjectURL(new Blob([JSON.stringify(overrides,null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download='issd-nomes-editados.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);};
$('import').onchange=async e=>{const file=e.target.files?.[0];if(!file)return;try{if(file.size>1024*1024)throw Error('Arquivo excede 1 MB');const imported=validateOverrides(JSON.parse(await file.text()));commit(imported);}catch(error){notice(error.message);}e.target.value='';};
try{const response=await fetch('../data/issd-rom-catalog.json');if(!response.ok)throw Error('Falha ao obter catálogo');base=await response.json();render();notice('Catálogo carregado: '+base.teams.length+' equipes.');}catch(error){notice(error.message);}
