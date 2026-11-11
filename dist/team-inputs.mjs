import {dispatchHumanActions} from './human-actions.mjs';
import {applyHumanMovement} from './human-movement.mjs';

// Browser experiment: fixed side order; it does not establish the ROM's order.
// Call actions and movement at their respective points in the simulation tick.
export function dispatchTeamInputs(inputs,handlers){
 for(const team of [0,1]){
  const input=inputs.get(team);
  if(input && handlers.getActor(team))dispatchHumanActions(team,input,handlers);
 }
}
export function moveTeamInputs(inputs,getActor,dt,toWorld,canMove=()=>true){
 for(const team of [0,1]){
  const input=inputs.get(team),actor=getActor(team);
  if(input && actor && canMove(actor))applyHumanMovement(actor,input,dt,toWorld);
 }
}
