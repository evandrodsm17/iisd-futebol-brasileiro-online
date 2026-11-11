import {matchStarters} from './match-flow.mjs';

// Prepares immutable-by-copy input data only. It does not mutate or start a match.
// Catalog and layouts must be the base data, not local editor overrides.
export function prepareOnlineMatch(setup,catalog,layouts,expectedBuild){
 if(!setup||typeof setup!=='object'||!Array.isArray(setup.sides)||setup.sides.length!==2||typeof setup.epoch!=='string'||!/^[a-f0-9]{32}$/.test(setup.epoch)||typeof expectedBuild!=='string'||!expectedBuild||setup.build!==expectedBuild||!Array.isArray(catalog?.teams)||!Array.isArray(layouts))return null;
 const settings=setup.settings;
 if(!settings||!Number.isInteger(settings.stadium)||!Number.isInteger(settings.gameTime)||![0,1,2].includes(settings.gameTime))return null;
 const stadium=layouts.find(item=>item.id===settings.stadium);
 if(!stadium)return null;
 const teams=[];
 for(const side of setup.sides){
  if(!side||!Number.isInteger(side.team)||!['home','away'].includes(side.kit))return null;
  const team=catalog.teams.find(item=>item.id===side.team);
  if(!team||!team.kit?.[side.kit]||!Array.isArray(team.players)||team.players.length<11||!team.formation||!Array.isArray(team.formation.outfield_slots)||team.formation.outfield_slots.length<10)return null;
  const starters=matchStarters(team);
  if(starters.length!==11||starters.some(player=>!team.players.includes(player)))return null;
  teams.push({team:structuredClone(team),kit:side.kit,starters:structuredClone(starters)});
 }
 return {epoch:setup.epoch,build:setup.build,gameTime:settings.gameTime,stadium:structuredClone(stadium),teams};
}
