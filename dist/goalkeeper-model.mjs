// Provisional browser goalkeeper positioning and shot contact. Values are in
// world units, not yet calibrated to ROM collision boxes or native AI.
export function goalkeeperHome(keeper,ball,field){
 const left=keeper.team===0,center=field.y+field.h/2,half=field.goalH/2;
 return {x:left?field.x+32:field.x+field.w-32,y:Math.max(center-half+10,Math.min(center+half-10,ball.y))};
}

export function goalkeeperShotContact(previous,ball,players,field,lastTouchTeam){
 if(ball.actionKind!=='shot'||ball.owner||![ball.x,ball.y,ball.z,ball.vx,ball.vy,previous.x,previous.y,previous.z].every(Number.isFinite))return null;
 const dx=ball.x-previous.x,dy=ball.y-previous.y,length2=dx*dx+dy*dy;
 if(!length2)return null;
 let best=null;
 for(const keeper of players){
  if(keeper.team===lastTouchTeam||!(keeper.roster?.position==='GK'||keeper.formationRole==='GK')||![keeper.x,keeper.y].every(Number.isFinite))continue;
  const line=keeper.team===0?field.x:field.x+field.w;
  if(Math.abs(keeper.x-line)>90)continue;
  const t=Math.max(0,Math.min(1,((keeper.x-previous.x)*dx+(keeper.y-previous.y)*dy)/length2));
  const x=previous.x+t*dx,y=previous.y+t*dy,z=previous.z+t*(ball.z-previous.z);
  if(Math.abs(x-keeper.x)>13||Math.abs(y-keeper.y)>18||z < -21||z>0)continue;
  if(!best||t<best.t)best={keeper,t,x,y,z,kind:z>=-9&&Math.hypot(ball.vx,ball.vy)<=6.6?'catch':'parry'};
 }
 return best;
}

// Visual anticipation only; the actual contact still uses the current frame.
// Ten future frames are a provisional browser timing, not a ROM AI constant.
export function predictGoalkeeperShot(ball,players,field,lastTouchTeam){
 if(ball?.actionKind!=='shot'||ball.owner||![ball.x,ball.y,ball.z,ball.vx,ball.vy,ball.vz,ball.gravity].every(Number.isFinite))return null;
 const n=10,future={...ball,x:ball.x+ball.vx*n,y:ball.y+ball.vy*n,z:Math.min(0,ball.z+ball.vz*n+ball.gravity*n*(n+1)/2)};
 return goalkeeperShotContact(ball,future,players,field,lastTouchTeam);
}

export function applyGoalkeeperShotContact(ball,contact){
 const {keeper,kind,x,y,z}=contact;
 if(kind==='catch'){
  Object.assign(ball,{owner:keeper,x:keeper.x,y:keeper.y,z:0,vx:0,vy:0,vz:0,actionKind:null});
 }else{
  const side=y>=keeper.y?1:-1;
  // A contact near the edge can continue toward the end line; central
  // deflections rebound into play. Both outcomes are prototype heuristics.
  const glancing=Math.abs(y-keeper.y)>=10;
  Object.assign(ball,{owner:null,x,y,z,vx:ball.vx*(glancing?0.35:-0.55),vy:ball.vy*0.45+side*2.2,vz:-0.8,actionKind:null});
 }
 return keeper.team;
}
