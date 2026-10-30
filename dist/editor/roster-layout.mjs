// Offline roster editor: independent of ROM bytes, stable player IDs and club IDs.
// The match and editor both consume the same pure transforms.
export const FORMATIONS = Object.freeze({
  '4-4-2': { lines: [[4, 35, 5], [4, 6, 2], [2, -37, 3]] },
  '4-3-3': { lines: [[4, 35, 5], [3, 5, 2], [3, -36, 3]] },
  '4-2-3-1': { lines: [[4, 35, 5], [2, 15, 2], [3, -12, 2], [1, -40, 3]] },
  '3-5-2': { lines: [[3, 33, 5], [5, 5, 2], [2, -36, 3]] },
});
const PRESET_KEYS=Object.keys(FORMATIONS);
const TEAM_PATTERN=/^(?:rom:(?:[0-9]|[12][0-9]|3[0-5])|custom:[a-z0-9][a-z0-9-]{1,63})$/;
const PLAYER_PATTERN=/^(?:rom:(?:[0-9]|[12][0-9]|3[0-5]):(?:[0-9]|1[0-9])|custom:[a-z0-9][a-z0-9-]{1,63}|temp:.+)$/;
const LINEUP_KEY='issd-team-lineups-v1';
const TRANSFER_KEY='issd-team-transfers-v1';
const roleBase={5:20,2:0,3:-28};
export const teamKey=id=>Number.isInteger(id)?'rom:'+id:String(id);
export function playerKey(player){
 if(Number.isInteger(player?.rom_origin_team_id)&&Number.isInteger(player?.rom_origin_slot))
   return 'rom:'+player.rom_origin_team_id+':'+player.rom_origin_slot;
 if(typeof player?.id==='string' && player.id.startsWith('temp:')) return player.id;
 if(typeof player?.id==='string' && player.id.startsWith('custom:')) return player.id;
 if(typeof player?.id==='string') return 'custom:'+player.id;
 throw Error('Identidade estável de jogador ausente');
}
export function formationSlots(preset){
 const info=FORMATIONS[preset];
 if(!info) throw Error('Formação desconhecida');
 return info.lines.flatMap(([amount,depth,role])=>Array.from({length:amount},(_,index)=>{
  // Explicit full-field depths; convert to existing match projection offsets.
  const width=(index-(amount-1)/2)*(amount===5?11:amount===4?17:amount===3?23:amount===2?29:0);
  return {role_code:role,depth:depth-roleBase[role],width};
 }));
}
export function emptyLineups(){return {schema_version:1,teams:[]};}
export function emptyTransfers(){return {schema_version:1,assignments:[]};}
function verify(condition,message){if(!condition)throw Error(message);}
export function validateLineups(value){
 verify(value?.schema_version===1&&Array.isArray(value.teams),'Escalações inválidas');
 const keys=new Set();
 for(const entry of value.teams){
  verify(entry&&TEAM_PATTERN.test(entry.team_id)&&PRESET_KEYS.includes(entry.formation)&&Array.isArray(entry.starters),'Escalação inválida');
  verify(entry.starters.length<=11&&entry.starters.every(id=>PLAYER_PATTERN.test(id)),'Titulares inválidos');
  verify(new Set(entry.starters).size===entry.starters.length,'Jogador repetido na escalação');
  verify(!keys.has(entry.team_id),'Equipe repetida na escalação');keys.add(entry.team_id);
 }
 return value;
}
export function validateTransfers(value){
 verify(value?.schema_version===1&&Array.isArray(value.assignments),'Transferências inválidas');
 const keys=new Set();
 for(const entry of value.assignments){
  verify(entry&&PLAYER_PATTERN.test(entry.player_id)&&!entry.player_id.startsWith('temp:')&&TEAM_PATTERN.test(entry.team_id),'Transferência inválida');
  verify(!keys.has(entry.player_id),'Transferência duplicada');keys.add(entry.player_id);
 }
 return value;
}
export function setLineup(current,clubId,formation,starters){
 const draft=structuredClone(validateLineups(current)),id=teamKey(clubId);
 draft.teams=draft.teams.filter(e=>e.team_id!==id);
 draft.teams.push({team_id:id,formation,starters:[...starters]});
 return validateLineups(draft);
}
export function setTransfer(current,playerId,destination){
 const draft=structuredClone(validateTransfers(current)),id=teamKey(destination);
 draft.assignments=draft.assignments.filter(e=>e.player_id!==playerId);
 draft.assignments.push({player_id:playerId,team_id:id});
 return validateTransfers(draft);
}
export function removeTransfer(current,playerId){
 const draft=structuredClone(validateTransfers(current));
 draft.assignments=draft.assignments.filter(e=>e.player_id!==playerId);
 return draft;
}
export function applyTransfers(catalog,changes){
 validateTransfers(changes);
 const copy=structuredClone(catalog),teams=new Map(copy.teams.map(team=>[teamKey(team.id),team]));
 const destinations=new Map(changes.assignments.map(a=>[a.player_id,a.team_id]));
 const groups=new Map([...teams.keys()].map(id=>[id,[]])),ids=new Set();
 for(const team of copy.teams){
  for(const player of team.players){
   const key=playerKey(player);
   verify(!ids.has(key),'Jogador duplicado no catálogo: '+key);ids.add(key);
   const destination=destinations.get(key);
   const group=destination&&teams.has(destination)?destination:teamKey(team.id);
   groups.get(group).push(player);
  }
 }
 for(const team of copy.teams) team.players=groups.get(teamKey(team.id));
 return copy;
}
function temporaryPlayer(teamId,index){
 return {id:'temp:'+teamKey(teamId)+':'+index,name:'Atleta temporário '+(index+1),
   position:index===0?'GK':index<5?'DF':index<9?'MF':'FW',
   shirt_number:index+1,temporary:true};
}
export function applyLineups(catalog,settings){
 validateLineups(settings);
 const copy=structuredClone(catalog),saved=new Map(settings.teams.map(entry=>[entry.team_id,entry]));
 for(const team of copy.teams){
  const selected=saved.get(teamKey(team.id));
  if(selected){
   const lookup=new Map(team.players.map(p=>[playerKey(p),p]));
   const starters=selected.starters.map(id=>lookup.get(id)).filter(Boolean);
   const used=new Set(starters.map(playerKey));
   team.players=[...starters,...team.players.filter(p=>!used.has(playerKey(p)))];
   team.formation={...team.formation,label:selected.formation,outfield_slots:formationSlots(selected.formation)};
  }
  // Temporary match actors don't overwrite the edited roster or database.
  if(team.players.length<11){
   const original=team.players.length;
   for(let index=original;index<11;index++)team.players.push(temporaryPlayer(team.id,index));
  }
 }
 return copy;
}
function load(storage,key,validator,fallback){
 try{return validator(JSON.parse(storage.getItem(key)))}catch{return fallback();}
}
export function loadLineups(storage=globalThis.localStorage){return load(storage,LINEUP_KEY,validateLineups,emptyLineups);}
export function loadTransfers(storage=globalThis.localStorage){return load(storage,TRANSFER_KEY,validateTransfers,emptyTransfers);}
export function saveLineups(value,storage=globalThis.localStorage){validateLineups(value);storage.setItem(LINEUP_KEY,JSON.stringify(value));}
export function saveTransfers(value,storage=globalThis.localStorage){validateTransfers(value);storage.setItem(TRANSFER_KEY,JSON.stringify(value));}
