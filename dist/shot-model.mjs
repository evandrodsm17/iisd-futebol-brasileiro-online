// Browser shot controls pending calibration against native velocity units.
// Shift (run) modifies shot height; horizontal input may shoot backwards.
export function planShot(team,inputX,inputY,high=false){
 if(![0,1].includes(team)||![inputX,inputY].every(Number.isFinite))throw new RangeError('Chute inválido');
 const x=Math.sign(inputX)||(team===0?1:-1),y=Math.sign(inputY)*0.55,length=Math.hypot(x,y);
 return {vx:6.5*x/length,vy:6.5*y/length,vz:high?-2.8:-0.65,gravity:0.125};
}
