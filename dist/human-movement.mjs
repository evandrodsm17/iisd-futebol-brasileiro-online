import {inputAxes} from './input-frame.mjs';
import {approachMovement} from './movement-profile.mjs';
import {moveFixed} from './fixed-motion.mjs';

// The caller selects the actor; this function is independent of team and DOM.
export function applyHumanMovement(actor,input,dt,toWorld){
 let {x,y}=inputAxes(input);
 const length=Math.hypot(x,y)||1;x/=length;y/=length;
 const move=toWorld(actor,x,y);
 approachMovement(actor,move.x,move.y,input.run,dt);
 if(!x&&!y&&Math.hypot(actor.vx,actor.vy)<.25){actor.vx=0;actor.vy=0;}
 moveFixed(actor,actor.vx*dt*60,actor.vy*dt*60);
}
