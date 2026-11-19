import {nativePenaltyShotDirection} from './penalty-direction.mjs';
import {advanceNativePenaltyFreeFlight} from './penalty-free-flight.mjs';
import {advanceNativePenaltyGroundStep} from './penalty-ground-motion.mjs';
import {nativePenaltyPostCrossing} from './penalty-post-crossing.mjs';
import {nativeOamProjectionPart} from './native-oam-projection.mjs';

// Deterministic reconstruction of these recorded excerpts, not a general shot
// simulator. Branches and post-goal flags are supplied by the capture.
export function replayCapturedPenaltyMotion(capture,exceptions,gravity,launch=null){
 if(!capture||!exceptions||capture.input!==exceptions.input||capture.graphics_sha256!==exceptions.graphics_sha256||!Array.isArray(capture.samples)||capture.samples.length!==40||!Array.isArray(exceptions.cases))throw new RangeError('Mismatched penalty capture');
 const exceptional=new Map();
 for(const item of exceptions.cases){
  if(!Number.isInteger(item.index)||item.index<0||item.index>=40||exceptional.has(item.index)||capture.samples[item.index])throw new RangeError('Ambiguous captured frame');
  exceptional.set(item.index,item);
 }
 let state=null,started=false,ended=false;const frames=Array(40).fill(null);
 if(launch!==null){
  if(launch.input!==capture.input || launch.graphics_sha256!==capture.graphics_sha256 || !Number.isSafeInteger(launch.free_steps) || launch.free_steps<0 || launch.free_steps>1000 || !Array.isArray(launch.vector) || launch.vector.length!==3 || nativePenaltyShotDirection(launch.input_word,launch.flags).index!==launch.index)throw new RangeError('Invalid captured launch');
  for(const [index,key] of ['vx','vy','vz'].entries())if(!Number.isInteger(launch.vector[index]) || (launch.vector[index]&0xffffff)!==launch.initial?.[key])throw new RangeError('Invalid launch vector');
  state={...launch.initial};
  for(let i=0;i<launch.free_steps;i++)state=advanceNativePenaltyFreeFlight(state,gravity);
 }
 for(let index=0;index<40;index++){
  const sample=capture.samples[index]??exceptional.get(index);
  if(!sample){if(started)ended=true;continue;}
  if(ended)throw new RangeError('Gap in captured trajectory');
  if(!started){if(state===null)state={...sample.before};started=true;}
  for(const field of ['x','y','z','vx','vy','vz']){
   const value=['x','y','z'].includes(field)?state[field]&0xffff:state[field];
   if(value!==sample.before[field])throw new RangeError(`Discontinuous captured ${field}`);
  }
  if(sample.kind==='ground_bounce'){
   if(state.vx!==0||state.vy!==0)throw new RangeError('Unvalidated bounce');
   state=advanceNativePenaltyGroundStep(state,gravity,{frictionX:false,frictionY:false,bounce:true});
  }else if(sample.kind===undefined||sample.kind==='goal_crossing'){
   state=advanceNativePenaltyFreeFlight(state,gravity);
   if(sample.kind==='goal_crossing'){
    const post=nativePenaltyPostCrossing({flags:sample.postFlags,height:sample.postHeight,vx:state.vx,vy:state.vy,vz:state.vz});
    if(post.route!=='8e25')throw new RangeError('Unvalidated goal continuation');
    state={...state,vx:post.vx,vy:post.vy,vz:post.vz};
   }
  }else throw new RangeError('Unsupported motion branch');
  const point=nativeOamProjectionPart({x:(state.x>>>8)&0xffff,y:(state.y>>>8)&0xffff,height:(state.z>>>8)&0xffff,partX:sample.partX,partY:sample.partY,size:sample.size});
  const x=point.x&255,y=point.y&255;
  if(x!==sample.oamX||y!==sample.oamY)throw new RangeError('Captured projection mismatch');
  frames[index]={x,y,size:sample.size,kind:sample.kind??'free_flight'};
 }
 if(!started)throw new RangeError('Empty captured trajectory');
 return frames;
}
