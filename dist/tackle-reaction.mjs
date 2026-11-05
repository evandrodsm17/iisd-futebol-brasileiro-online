// Browser prototype: a successful interception may display the one captured
// victim reaction whose link to a sliding tackle was observed. This does not
// reproduce the ROM's foul, collision, or evasion decision tree.
export function beginCapturedTackleFall(victim, tick, renderer, request, referenceHeight){
 if(!victim||victim.roster?.position==='GK'||victim.formationRole==='GK'||request?.screenDirection!==5||!Number.isInteger(tick)||!Number.isFinite(referenceHeight)||referenceHeight<=0||!renderer?.supports(request))return false;
 victim.actionVisual={kind:'fall',screenDirection:request.screenDirection,started:tick,nativeFall:true,request,referenceHeight};
 victim.fallUntil=tick+renderer.duration;
 victim.vx=0;victim.vy=0;
 return true;
}
export function isFallen(player,tick){return Number.isFinite(player?.fallUntil)&&tick<player.fallUntil;}
