// Dispatch in input order, resolving the current team member after switches.
// The caller owns match state; reset is intentionally local-player-only.
export function dispatchHumanActions(team,input,handlers){
 for(const action of input.actions){
  if(action==='reset'){if(team===0)handlers.reset();continue;}
  if(action==='switch'){handlers.switchPlayer(team);continue;}
  const actor=handlers.getActor(team);
  if(!actor)continue;
  if(action==='shot')handlers.shoot(actor,input);
  else if(action==='pass')handlers.pass(actor,input);
  else if(action==='press')handlers.press(actor,input);
 }
}
