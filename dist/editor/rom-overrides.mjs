// Stable identities: source ROM team + player slot, independent of names/transfers.
// Compatible with saved v1 name-only overrides (same storage key and schema).
const KEY='issd-rom-catalog-overrides-v1';
export const ROM_ATTRIBUTES=Object.freeze(['acceleration','speed','shooting','technique','balance','intelligence','dribbling','jumping','stamina']);
export const ROM_POSITIONS=Object.freeze(['GK','DF','MF','FW']);
const NAME_MAX=90;
const isTeam=value=>Number.isInteger(value)&&value>=0&&value<36;
const isSlot=value=>Number.isInteger(value)&&value>=0&&value<20;
const isRating=value=>Number.isInteger(value)&&value>=1&&value<=99;
const validName=value=>typeof value==='string'&&value.trim().length>0&&value.trim().length<=NAME_MAX;
export function emptyOverrides(){return {schema_version:1,teams:[],players:[]};}
export function validateOverrides(value){
 if(!value||typeof value!=='object'||value.schema_version!==1||!Array.isArray(value.teams)||!Array.isArray(value.players))throw Error('Formato de alterações inválido');
 const teamSeen=new Set(),playerSeen=new Set();
 for(const team of value.teams){
  if(!isTeam(team.team_id)||!validName(team.name)||teamSeen.has(team.team_id))throw Error('Equipe inválida ou repetida');
  teamSeen.add(team.team_id);
 }
 for(const player of value.players){
  if(!isTeam(player.team_id)||!isSlot(player.slot)||!validName(player.name))throw Error('Nome ou ID de jogador inválido');
  const id=player.team_id+':'+player.slot;
  if(playerSeen.has(id))throw Error('Jogador duplicado: '+id);playerSeen.add(id);
  if(player.position!==undefined&&!ROM_POSITIONS.includes(player.position))throw Error('Posição inválida em '+id);
  if(player.shirt_number!==undefined&&!isRating(player.shirt_number))throw Error('Número de camisa inválido em '+id);
  if(player.target_team_id!==undefined&&!isTeam(player.target_team_id))throw Error('Destino de transferência inválido em '+id);
  if(player.attributes!==undefined){
   if(!player.attributes||typeof player.attributes!=='object'||Array.isArray(player.attributes))throw Error('Atributos inválidos em '+id);
   for(const [key,val] of Object.entries(player.attributes)){
    if(!ROM_ATTRIBUTES.includes(key)||!isRating(val))throw Error('Atributo inválido '+key+' em '+id);
   }
  }
 }
 return value;
}
export function applyRomOverrides(catalog,overrides){
 validateOverrides(overrides);
 const next=structuredClone(catalog);
 const teams=new Map(next.teams.map(team=>[team.id,team]));
 for(const item of overrides.teams){const team=teams.get(item.team_id);if(!team)throw Error('Equipe ausente no catálogo: '+item.team_id);team.name=item.name.trim();}
 const changes=new Map(overrides.players.map(entry=>[entry.team_id+':'+entry.slot,entry]));
 const rosters=new Map([...teams.keys()].map(id=>[id,[]]));
 for(const team of next.teams){
  for(let slot=0;slot<team.players.length;slot++){
   const change=changes.get(team.id+':'+slot);
   const player=team.players[slot];
   player.rom_origin_team_id=team.id;player.rom_origin_slot=slot;
   if(change){
    player.name=change.name.trim();
    if(change.position!==undefined)player.position=change.position;
    if(change.shirt_number!==undefined)player.shirt_number=change.shirt_number;
    if(change.attributes)player.attributes={...player.attributes,...change.attributes};
   }
   const destination=change?.target_team_id??team.id;
   if(!rosters.has(destination))throw Error('Equipe de destino ausente no catálogo: '+destination);
   rosters.get(destination).push(player);
  }
 }
 for(const team of next.teams){
  // Native members retain their original order. Arrivals stay after them;
  // starting-XI selection is a separate editor feature, not silently changed.
  const roster=rosters.get(team.id);
  team.players=[...roster.filter(p=>p.rom_origin_team_id===team.id),...roster.filter(p=>p.rom_origin_team_id!==team.id)];
 }
 return next;
}
export function updateRomPlayer(overrides,sourceTeamId,slot,values,original){
 validateOverrides(overrides);
 if(!isTeam(sourceTeamId)||!isSlot(slot)||!original)throw Error('Identidade do jogador inválida');
 const name=String(values.name??'').trim();
 if(!validName(name))throw Error('Nome deve ter entre 1 e 90 caracteres');
 const shirt=values.shirt_number,position=values.position,destination=values.target_team_id??sourceTeamId;
 if(!isRating(shirt)||!ROM_POSITIONS.includes(position)||!isTeam(destination))throw Error('Posição, camisa ou equipe de destino inválida');
 if(!values.attributes||typeof values.attributes!=='object'||Array.isArray(values.attributes))throw Error('Atributos ausentes');
 const attrs={};
 for(const key of ROM_ATTRIBUTES){
  if(!isRating(values.attributes[key]))throw Error('Atributo '+key+' deve estar entre 1 e 99');
  if(values.attributes[key]!==original.attributes[key])attrs[key]=values.attributes[key];
 }
 const result=structuredClone(overrides);
 result.players=result.players.filter(p=>p.team_id!==sourceTeamId||p.slot!==slot);
 const record={team_id:sourceTeamId,slot,name};
 if(position!==original.position)record.position=position;
 if(shirt!==original.shirt_number)record.shirt_number=shirt;
 if(destination!==sourceTeamId)record.target_team_id=destination;
 if(Object.keys(attrs).length)record.attributes=attrs;
 if(name!==original.name||Object.keys(record).length>3)result.players.push(record);
 return validateOverrides(result);
}
export function renameRomEntry(overrides,kind,teamId,slot,name,originalName){
 const result=structuredClone(validateOverrides(overrides));
 const cleaned=String(name).trim();if(!validName(cleaned))throw Error('Nome deve ter entre 1 e 90 caracteres');
 if(!isTeam(teamId))throw Error('Equipe inválida');
 if(kind==='team'){
  result.teams=result.teams.filter(e=>e.team_id!==teamId);
  if(cleaned!==originalName)result.teams.push({team_id:teamId,name:cleaned});
 }else if(kind==='player'){
  if(!isSlot(slot))throw Error('Jogador inválido');
  const existing=result.players.find(e=>e.team_id===teamId&&e.slot===slot);
  result.players=result.players.filter(e=>e.team_id!==teamId||e.slot!==slot);
  if(existing){
   const updated={...existing,name:cleaned};
   if(cleaned!==originalName||Object.keys(updated).some(k=>!['team_id','slot','name'].includes(k)))result.players.push(updated);
  }else if(cleaned!==originalName)result.players.push({team_id:teamId,slot,name:cleaned});
 }else throw Error('Tipo inválido');
 return validateOverrides(result);
}
export function loadRomOverrides(storage=globalThis.localStorage){
 try{return validateOverrides(JSON.parse(storage.getItem(KEY)));}catch{return emptyOverrides();}
}
export function saveRomOverrides(overrides,storage=globalThis.localStorage){
 validateOverrides(overrides);storage.setItem(KEY,JSON.stringify(overrides));
}
