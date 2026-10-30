import {applyRomOverrides,loadRomOverrides} from './rom-overrides.mjs';
import {loadContent} from './content-storage.mjs';
import {customCatalogTeams} from './content-model.mjs';
import {FORMATIONS,teamKey,playerKey,applyTransfers,applyLineups,setTransfer,removeTransfer,setLineup,loadTransfers,saveTransfers,loadLineups,saveLineups} from './roster-layout.mjs';
const $=id=>document.getElementById(id);
let catalog,selected=0,transfers=loadTransfers(),lineups=loadLineups();
function msg(s){$('status').textContent=s;}
async function rebuild(){
 const raw=await (await fetch('../data/issd-rom-catalog.json')).json();
 catalog=applyRomOverrides(raw,loadRomOverrides());
 const stored=await loadContent();
 if(stored?.package)catalog.teams.push(...customCatalogTeams(stored.package));
 catalog=applyTransfers(catalog,transfers);
 render();
}
function render(){
 const team=catalog.teams[selected];if(!team)return;
 const id=teamKey(team.id),saved=lineups.teams.find(x=>x.team_id===id);
 $('teams').replaceChildren(...catalog.teams.map((t,i)=>{const b=document.createElement('button');b.textContent=t.name;b.className=i===selected?'selected':'';b.onclick=()=>{selected=i;render();};return b;}));
 $('team-title').textContent=team.name;
 $('formation').replaceChildren(...Object.keys(FORMATIONS).map(f=>new Option(f,f,false,(saved?.formation??team.formation?.label)===f)));
 const starting=saved?.starters??team.players.slice(0,11).map(playerKey);
 $('roster').replaceChildren(...team.players.filter(p=>!p.temporary).map(p=>{
  const row=document.createElement('div');row.className='roster-row';
  const check=document.createElement('input');check.type='checkbox';check.checked=starting.includes(playerKey(p));check.dataset.id=playerKey(p);
  const title=document.createElement('label');title.textContent=p.name+' · '+p.position+' #'+p.shirt_number;title.prepend(check);
  const destination=document.createElement('select');destination.setAttribute('aria-label','Transferir '+p.name);
  destination.replaceChildren(...catalog.teams.map(t=>new Option(t.name,teamKey(t.id),false,teamKey(t.id)===id)));
  destination.onchange=async()=>{try{
   transfers=setTransfer(transfers,playerKey(p),destination.value);saveTransfers(transfers);
   // Clear saved starters containing a moved player; preserve other settings.
   lineups={...lineups,teams:lineups.teams.map(t=>({...t,starters:t.starters.filter(pid=>pid!==playerKey(p))}))};saveLineups(lineups);
   await rebuild();msg('Transferência salva. O atleta foi associado ao novo elenco.');
  }catch(error){msg(error.message);}};
  row.append(title,destination);return row;
 }));
 updatePreview(team,starting);
}
function updatePreview(team,ids){
 const players=ids.map(id=>team.players.find(p=>playerKey(p)===id)).filter(Boolean);
 const preset=$('formation').value;
 const lines=FORMATIONS[preset].lines.map(line=>line[0]);
 let index=0;
 const div=document.createElement('div');div.className='pitch-row';div.append(makePlayer(players[index++]));const nodes=[div];
 for(const amount of lines){const row=document.createElement('div');row.className='pitch-row';for(let i=0;i<amount;i++)row.append(makePlayer(players[index++]));nodes.push(row);}
 $('pitch').replaceChildren(...nodes);
}
function makePlayer(player){const el=document.createElement('span');el.className='pitch-player';el.textContent=player?.name??'Vaga';return el;}
$('save').onclick=()=>{
 try{const team=catalog.teams[selected];
 const starters=[...document.querySelectorAll('#roster input:checked')].map(x=>x.dataset.id);
 if(starters.length!==11)throw Error('Escolha exatamente 11 titulares.');
 lineups=setLineup(lineups,team.id,$('formation').value,starters);saveLineups(lineups);render();msg('Escalação salva neste navegador.');
 }catch(error){msg(error.message);}
};
$('reset').onclick=()=>{const id=teamKey(catalog.teams[selected].id);lineups={...lineups,teams:lineups.teams.filter(t=>t.team_id!==id)};saveLineups(lineups);render();msg('Escalação restaurada.');};
$('formation').onchange=()=>{const team=catalog.teams[selected],ids=[...document.querySelectorAll('#roster input:checked')].map(x=>x.dataset.id);updatePreview(team,ids);};
$('roster').onchange=e=>{if(e.target.type==='checkbox'){const team=catalog.teams[selected],ids=[...document.querySelectorAll('#roster input:checked')].map(x=>x.dataset.id);updatePreview(team,ids);}};
try{await rebuild();}catch(e){msg(e.message);}
