// Playable browser approximation; timing, aim and scaling still need ROM calibration.
import {inputAxes} from './input-frame.mjs';

export function beginThrowIn(receiver, field, ball) {
 if(!receiver||![receiver.x,receiver.y,field.y,field.h].every(Number.isFinite))throw new RangeError('Invalid throw-in');
 const inward=receiver.y<field.y+field.h/2?1:-1;
 Object.assign(ball,{x:receiver.x,y:receiver.y,z:-22,vx:0,vy:0,vz:0,owner:receiver,passRolling:false,actionKind:null});
 return {receiver,team:receiver.team,inward,phase:'aim',ticks:0,aim:{x:0,y:inward},visualDirection:inward===1?4:0,power:'pass'};
}

// Actions are fixed-tick input from either a human or the CPU. Movement is
// held while the restart is prepared. Return true exactly on release.
export function advanceThrowIn(state, input, isHuman, ball, toWorld) {
 if(!state||ball.owner!==state.receiver)throw new RangeError('Invalid throw-in state');
 state.receiver.vx=state.receiver.vy=0;
 if(state.phase==='aim'){
  const {x,y}=inputAxes(input??{});
  if(x||y){
   const world=toWorld(state.receiver,x,y),horizontal=Number(world.x)||0,vertical=Number(world.y)||0;
   // A throw must enter the field; keep the chosen horizontal component.
   const inwardY=Math.max(.25,vertical*state.inward),length=Math.hypot(horizontal,inwardY);
   state.aim={x:horizontal/length,y:state.inward*inwardY/length};
   // Only the individual left/right inputs were captured on each side;
   // diagonal input uses the neutral pose until its own mapping is validated.
   state.visualDirection=y===0&&x!==0?(state.inward===1?(x<0?5:3):(x<0?7:1)):(state.inward===1?4:0);
  }
  state.ticks++;
  const action=input?.actions?.find(a=>a==='pass'||a==='shot');
  if(action||(!isHuman&&state.ticks>=30)){
   state.power=action==='shot'?'shot':'pass';state.phase='release';state.ticks=0;
  }
  return false;
 }
 if(state.phase!=='release')throw new RangeError('Invalid throw-in phase');
 if(++state.ticks<4)return false;
 const speed=state.power==='shot'?3.25:2.5;
 Object.assign(ball,{owner:null,vx:state.aim.x*speed,vy:state.aim.y*speed,vz:state.power==='shot'?-2.625:-1.875,
  gravity:.125,passRolling:false,actionKind:'throw_in',throwInSide:state.inward===1?'upper':'lower',throwInPower:state.power,throwInTeam:state.team});
 return true;
}
