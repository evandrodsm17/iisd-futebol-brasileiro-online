// Browser-only provisional dribble contact, measured in match-world units.
// This is not a recovered SNES constant or ball collision implementation.
export const DRIBBLE = Object.freeze({
  footYOffset: 4.5,
  forwardOffset: 10.5,
  settlePerFrame: 0.55,
  maxExtraSpeedPerFrame: 0.7,
  minimumSettleSpeed: 0.8,
  releaseDistance: 20,
  pickupDistance: 14,
});
const DIRECTIONS = [
  [0,-1],[Math.SQRT1_2,-Math.SQRT1_2],[1,0],
  [Math.SQRT1_2,Math.SQRT1_2],[0,1],
  [-Math.SQRT1_2,Math.SQRT1_2],[-1,0],[-Math.SQRT1_2,-Math.SQRT1_2],
];
export function ballFootTarget(actor) {
  const vx=Number(actor.vx)||0,vy=Number(actor.vy)||0;
  const speed=Math.hypot(vx,vy);
  const fallback=DIRECTIONS[actor.facingDirection]??(actor.team===0?DIRECTIONS[2]:DIRECTIONS[6]);
  const [dx,dy]=speed>0.25?[vx/speed,vy/speed]:fallback;
  return {x:actor.x+dx*DRIBBLE.forwardOffset,y:actor.y+DRIBBLE.footYOffset+dy*DRIBBLE.forwardOffset};
}
export function settleDribble(ball,actor,frames=1) {
  if(!Number.isFinite(frames)||frames<0)throw new RangeError('Invalid frame delta');
  const destination=ballFootTarget(actor),dx=destination.x-ball.x,dy=destination.y-ball.y;
  const distance=Math.hypot(dx,dy);
  const speed=Math.hypot(Number(actor.vx)||0,Number(actor.vy)||0);
  const available=Math.max(DRIBBLE.minimumSettleSpeed,speed+DRIBBLE.maxExtraSpeedPerFrame)*frames;
  const desiredStep=distance*(1-Math.pow(1-DRIBBLE.settlePerFrame,frames));
  const step=Math.min(distance,available,desiredStep);
  const ux=distance?dx/distance:0,uy=distance?dy/distance:0;
  ball.x+=ux*step;
  ball.y+=uy*step;
  ball.vx=frames?ux*step/frames:0;
  ball.vy=frames?uy*step/frames:0;
  return {distanceBefore:distance,distanceAfter:Math.hypot(ball.x-actor.x,ball.y-actor.y)};
}
