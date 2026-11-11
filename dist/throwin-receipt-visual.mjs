/** Narrow visual gate for the one captured airborne throw-in reception.
 * Screen direction 5 uses the existing inverse mapping for native direction 3.
 * Browser/native scaling is provisional; this is presentation, not physics. */
export function canShowCapturedReceipt(actor, context, projectionActive, renderer, request){
 if(!actor||!context||projectionActive||context.side!=='lower'||context.power!=='pass'||![0,1].includes(context.sourceTeam)||actor.team!==context.sourceTeam||context.nativeHeight!==0xffe9||actor.facingDirection!==5||actor.roster?.position==='GK'||actor.formationRole==='GK'||actor.actionVisual||actor.throwVisual)return false;
 return !!renderer?.supports(request);
}

// The second reference is an opponent meeting the long throw, native direction
// 2. Screen direction 4 follows the project's existing locomotion mapping.
export function canShowContestedReceipt(actor,context,projectionActive,renderer,request){
 if(!actor||!context||projectionActive||context.side!=='lower'||context.power!=='shot'||context.nativeHeight!==0xffee||![0,1].includes(context.sourceTeam)||![0,1].includes(actor.team)||actor.team===context.sourceTeam||actor.facingDirection!==4||actor.roster?.position==='GK'||actor.formationRole==='GK'||actor.actionVisual||actor.throwVisual)return false;
 return !!renderer?.supports(request);
}
