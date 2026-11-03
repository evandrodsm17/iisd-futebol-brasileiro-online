import {browserContact} from './ball-contact.mjs';

// A playable interception, not a recovered ISSD tackle/slide state machine.
export function canStealBall(player,ball,now,lastAttempt){
 if(!player||!ball||!Number.isFinite(now)||(!Number.isFinite(lastAttempt)&&lastAttempt!==-Infinity))return false;
 if(now-lastAttempt<420||!ball.owner||ball.owner===player||ball.owner.team===player.team||ball.z!==0)return false;
 return browserContact(player,ball);
}
