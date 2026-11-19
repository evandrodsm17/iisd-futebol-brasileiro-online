import {nativePenaltyVectorFromTables} from './penalty-shot-vector.mjs';
import {observedPenaltyAimWord} from './penalty-observed-input.mjs';
import {advanceNativePenaltyFreeFlight} from './penalty-free-flight.mjs';
import {nativePenaltyGoalGeometryReason} from './penalty-goal-geometry.mjs';
import {nativeOamProjectionPart} from './native-oam-projection.mjs';

// Restricted laboratory experiment: the initial state, gravity, variant and
// flags come from two synthetic captures. No collision or save is simulated.
export function previewPenaltyFreeFlight(tables,direction){
 const word=observedPenaltyAimWord(direction),flags=0x1284,gravity=0x20;
 const vector=nativePenaltyVectorFromTables(tables,0,word,flags);
 let state={x:0x8000,y:0x9400,z:0,vx:vector.dx&0xffffff,vy:vector.dy&0xffffff,vz:vector.dz&0xffffff};
 const frames=[];
 for(let tick=1;tick<=90;tick++){
  state=advanceNativePenaltyFreeFlight(state,gravity);
  const x=(state.x>>>8)&0xffff,y=(state.y>>>8)&0xffff,height=(state.z>>>8)&0xffff;
  const projection=nativeOamProjectionPart({x,y,height,partX:0,partY:0xfffd,size:8});
  frames.push({tick,x,y,height,screenX:projection.x&255,screenY:projection.y&255});
  // Ground response and object contacts require separate native gates.
  if(height!==0 && height<0x8000)return {vector,frames,stop:'ground_pending'};
  const decision=nativePenaltyGoalGeometryReason({x,y,height,flags});
  if(decision!=='outside_path')return {vector,frames,stop:'geometry_reached'};
 }
 return {vector,frames,stop:'frame_limit'};
}
