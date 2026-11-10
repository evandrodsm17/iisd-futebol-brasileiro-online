// Browser shot controls pending calibration against native velocity units.
// Shift (run) modifies shot height; the last facing direction is used when
// no direction is pressed. Speed and trajectory remain provisional.
const FACING=[[0,-1],[1,-1],[1,0],[1,1],[0,1],[-1,1],[-1,0],[-1,-1]];
export function planShot(team,inputX,inputY,high=false,facingDirection){
 if(![0,1].includes(team)||![inputX,inputY].every(Number.isFinite))throw new RangeError('Chute inválido');
 let x=Math.sign(inputX),y=Math.sign(inputY);
 if(!x&&!y)[x,y]=FACING[facingDirection]??[team===0?1:-1,0];
 y*=0.55;const length=Math.hypot(x,y);
 return {vx:6.5*x/length,vy:6.5*y/length,vz:high?-2.8:-0.65,gravity:0.125};
}

// Observed type-3 airborne order: update vertical velocity before position.
// The browser's units, acceleration, release and landing remain provisional.
export function advanceShotAirborne(ball,frames=1){
 if(![ball?.z,ball?.vz,ball?.gravity,frames].every(Number.isFinite)||frames<0)throw new RangeError('Estado aéreo inválido');
 const vz=ball.vz+ball.gravity*frames;
 return {z:ball.z+vz*frames,vz};
}
