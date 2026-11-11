import {nativeType5InitialVerticalVelocity,nativeType5AuxiliaryFields} from './native-shot-type5.mjs';

// The web has two height choices, not the ROM's measured charge control yet.
// These representative parameters and this scale are provisional: the scale
// keeps the existing high-shot launch height while using native acceleration.
const WEB_SHOT_HEIGHT_SCALE=2.8/2.5;
const WEB_SHOT_NATIVE_PARAMETER={low:2,high:11};
const FACING=[[0,-1],[1,-1],[1,0],[1,1],[0,1],[-1,1],[-1,0],[-1,-1]];
export function planShot(team,inputX,inputY,high=false,facingDirection){
 if(![0,1].includes(team)||![inputX,inputY].every(Number.isFinite))throw new RangeError('Chute inválido');
 let x=Math.sign(inputX),y=Math.sign(inputY);
 if(!x&&!y)[x,y]=FACING[facingDirection]??[team===0?1:-1,0];
 y*=0.55;const length=Math.hypot(x,y);
 const parameter=WEB_SHOT_NATIVE_PARAMETER[high?'high':'low'];
 const vertical=nativeType5InitialVerticalVelocity(parameter);
 const signed=(vertical.integer&0x8000)?vertical.integer-0x10000:vertical.integer;
 const vz=(signed+vertical.fraction/0x10000)*WEB_SHOT_HEIGHT_SCALE;
 const gravity=nativeType5AuxiliaryFields(parameter,0).field58/0x10000*WEB_SHOT_HEIGHT_SCALE;
 return {vx:6.5*x/length,vy:6.5*y/length,vz,gravity};
}

// Observed type-3 airborne order: update vertical velocity before position.
// The browser's units, acceleration, release and landing remain provisional.
export function advanceShotAirborne(ball,frames=1){
 if(![ball?.z,ball?.vz,ball?.gravity,frames].every(Number.isFinite)||frames<0)throw new RangeError('Estado aéreo inválido');
 const vz=ball.vz+ball.gravity*frames;
 return {z:ball.z+vz*frames,vz};
}
