// Comparison of recorded native flight and current web prototype. The height
// projection below is explicitly conditional, not a calibrated physics scale.
import {readFileSync,writeFileSync} from 'node:fs';
import {pathToFileURL} from 'node:url';
import {planShot,advanceShotAirborne} from '../dist/shot-model.mjs';
import {createSimulationClock} from '../dist/simulation-clock.mjs';

const signed=n=>(n>=0x80000000?n-0x100000000:n)/65536;
export function summarizeNativeFlight(cases){
 if(!Array.isArray(cases)||cases.length===0)throw new RangeError('Missing native cases');
 return cases.map(c=>{
  if(!Array.isArray(c.steps)||c.steps.length<2)throw new RangeError('Insufficient native steps');
  const steps=c.steps,intervals={};
  for(let i=1;i<steps.length;i++){
   const delta=steps[i].frame-steps[i-1].frame;
   if(!Number.isInteger(delta)||delta<1)throw new RangeError('Invalid native frame sequence');
   intervals[delta]=(intervals[delta]??0)+1;
  }
  return {direction:c.direction,updates:steps.length,firstFrame:steps[0].frame,lastFrame:steps.at(-1).frame,
    impactFrame:c.first_impact_frame,elapsedFramesToImpact:c.first_impact_frame-steps[0].frame,
    peakNativeHeight:-Math.min(...steps.map(s=>signed(s.position_after))),intervals};
 });
}

export function simulateWebHighShot(){
 const shot=planShot(0,1,0,true),ball={z:0,vz:shot.vz,gravity:shot.gravity};
 let peak=0,peakTick=0,landingTick=null;
 for(let tick=1;tick<=300;tick++){
  Object.assign(ball,advanceShotAirborne(ball));
  if(ball.z<peak){peak=ball.z;peakTick=tick;}
  if(ball.z>=0){landingTick=tick;break;}
 }
 if(landingTick===null)throw Error('Web shot did not land');
 let ticks=0;const clock=createSimulationClock(()=>ticks++);
 for(let i=0;i<60;i++)clock.advance(1/60);
 if(ticks!==60)throw Error('Unexpected simulation cadence');
 return {initialVelocity:shot.vz,gravity:shot.gravity,peakHeight:-peak,peakTick,landingTick,simulationTicksPerSecond:ticks};
}

export function buildComparison(native,scaleDiagnostic){
 const cases=summarizeNativeFlight(native.cases),browser=simulateWebHighShot();
 const scale=scaleDiagnostic.player.renderWorldUnitsPerNativeCellPixel;
 if(!Number.isFinite(scale)||scale<=0)throw new RangeError('Invalid presentation scale');
 return {schema:'issd-type6-web-comparison/v1',nativeCases:cases,browserHighShot:browser,
  conditionalProjection:{worldUnitsPerNativeScreenshotPixel:scale,
   projectedNativePeaks:cases.map(c=>({direction:c.direction,worldHeight:c.peakNativeHeight*scale})),
   assumptions:['One native height unit equals one screenshot pixel for these trajectories.',
    'The body-cell presentation scale is applicable to the ball and camera.',
    'The web high shot and the observed native type-6 shot need not represent the same input.']},
  limitations:['Native frame intervals describe one saved state and are not a verified universal update schedule.',
   'Browser simulation runs fixed ticks, while native frame durations and dropped updates need further investigation.',
   'No collision, goalkeeper, crossbar or bounce is simulated in the browser comparison.',
   'Conditional projection does not establish a physics scale or justify changing shot strength.']};
}

if(process.argv[1]&&import.meta.url===pathToFileURL(process.argv[1]).href){
 const root=new URL('../',import.meta.url);
 const native=JSON.parse(readFileSync(new URL('docs/issd-shot-type6-flight.json',root),'utf8'));
 const scale=JSON.parse(readFileSync(new URL('docs/issd-native-web-scale-diagnostic.json',root),'utf8'));
 const result=buildComparison(native,scale);
 writeFileSync(new URL('docs/issd-type6-web-comparison.json',root),JSON.stringify(result,null,2)+'\n');
 console.log(`OK: ${result.nativeCases.length} native trajectories and current web shot compared`);
}
