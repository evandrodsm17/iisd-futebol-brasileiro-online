// Readiness only yields the choices verified by the server. Other match
// settings are not yet shared and must not be inferred from this object.
export function buildRoomMatchSetup(players,epoch,build){
 if(!Array.isArray(players)||players.length!==2||typeof epoch!=='string'||!epoch||typeof build!=='string'||!build)return null;
 const ordered=[...players].sort((a,b)=>a.seat-b.seat);
 if(!ordered.every((player,index)=>player.seat===index+1&&player.ready===true&&Number.isInteger(player.team)&&(player.kit===0||player.kit===1)))return null;
 return {epoch,build,sides:ordered.map(player=>({team:player.team,kit:player.kit===0?'home':'away'}))};
}
