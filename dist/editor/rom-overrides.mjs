// Non-destructive edits to the ROM catalog: only display metadata changes.
// Stable identity uses ROM team id and player slot, never a mutable name.
const KEY='issd-rom-catalog-overrides-v1';
const NAME_MAX=90;
export function validateOverrides(value){
 if(!value||value.schema_version!==1||!Array.isArray(value.teams)||!Array.isArray(value.players))throw Error('Formato de alterações inválido');
 const teamSeen=new Set(), playerSeen=new Set();
 for(const team of value.teams){
  if(!Number.isInteger(team.team_id)||team.team_id<0||team.team_id>=36||typeof team.name!=='string'||!team.name.trim()||team.name.length>NAME_MAX||teamSeen.has(team.team_id))throw Error('Clube inválido ou repetido');
  teamSeen.add(team.team_id);
 }
 for(const player of value.players){
  if(!Number.isInteger(player.team_id)||player.team_id<0||player.team_id>=36||!Number.isInteger(player.slot)||player.slot<0||player.slot>=20||typeof player.name!=='string'||!player.name.trim()||player.name.length>NAME_MAX)throw Error('Jogador inválido');
  const id=player.team_id+':'+player.slot;if(playerSeen.has(id))throw Error('Jogador duplicado');playerSeen.add(id);
 }
 return value;
}
export function emptyOverrides(){return {schema_version:1,teams:[],players:[]};}
export function applyRomOverrides(catalog,overrides){
 validateOverrides(overrides);
 const next=structuredClone(catalog);
 for(const item of overrides.teams){const team=next.teams.find(t=>t.id===item.team_id);if(team)team.name=item.name.trim();}
 for(const item of overrides.players){const team=next.teams.find(t=>t.id===item.team_id);const player=team?.players?.[item.slot];if(player)player.name=item.name.trim();}
 return next;
}
export function renameRomEntry(overrides,kind,teamId,slot,name,originalName){
 const result=structuredClone(validateOverrides(overrides));
 const cleaned=String(name).trim();if(!cleaned||cleaned.length>NAME_MAX)throw Error('Nome deve ter de 1 a 90 caracteres');
 const key=kind==='team'?'teams':kind==='player'?'players':null;if(!key)throw Error('Tipo inválido');
 const index=result[key].findIndex(e=>e.team_id===teamId&&(kind==='team'||e.slot===slot));
 if(index>=0)result[key].splice(index,1);
 if(cleaned!==originalName)result[key].push(kind==='team'?{team_id:teamId,name:cleaned}:{team_id:teamId,slot,name:cleaned});
 return validateOverrides(result);
}
export function loadRomOverrides(storage=globalThis.localStorage){
 try{return validateOverrides(JSON.parse(storage.getItem(KEY)));}catch{return emptyOverrides();}
}
export function saveRomOverrides(overrides,storage=globalThis.localStorage){
 validateOverrides(overrides);storage.setItem(KEY,JSON.stringify(overrides));
}
