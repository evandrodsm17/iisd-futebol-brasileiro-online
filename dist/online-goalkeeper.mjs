import {goalkeeperShotContact,applyGoalkeeperShotContact} from './goalkeeper-model.mjs';
import {classifyFieldExitWithTime} from './field-events.mjs';

// Same provisional ordering as local play: an earlier line crossing wins;
// equal times favour the keeper.
export function resolveOnlineGoalkeeperShot(previous,ball,players,field,lastTouchTeam){
 const contact=goalkeeperShotContact(previous,ball,players,field,lastTouchTeam);
 const boundary=classifyFieldExitWithTime(previous,ball,field,lastTouchTeam);
 if(!contact||(boundary&&contact.t>boundary.time))return null;
 const team=applyGoalkeeperShotContact(ball,contact);
 return {team,keeper:contact.keeper,kind:contact.kind};
}
