/** Narrow visual gate for the one captured airborne throw-in reception.
 * Screen direction 5 uses the existing inverse mapping for native direction 3.
 * Browser/native scaling is provisional; this is presentation, not physics. */
export function canShowCapturedReceipt(actor, context, projectionActive, renderer, request){
 if(!actor||!context||projectionActive||context.side!=='lower'||context.nativeHeight!==0xffe9||actor.facingDirection!==5||actor.roster?.position==='GK'||actor.formationRole==='GK'||actor.actionVisual||actor.throwVisual)return false;
 return !!renderer?.supports(request);
}
