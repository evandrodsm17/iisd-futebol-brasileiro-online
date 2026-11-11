// Local calibration diagnostic: presentation ratio is a hypothesis, not ROM physics.
import {readFileSync,writeFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {planShot,advanceShotAirborne} from '../dist/shot-model.mjs';
import {nativeDimensions,fieldDimensions} from '../dist/native-field.mjs';
const bodyPath=new URL('../dist/assets/issd/runtime-body-local.json',import.meta.url);
const bodyBytes=readFileSync(bodyPath),body=JSON.parse(bodyBytes);
if(body.schema!=='issd-runtime-body-local/v1')throw Error('Unexpected locomotion schema');
const game=readFileSync(new URL('../dist/game.js',import.meta.url),'utf8');
const match=game.match(/player:\s*\{\s*w:\s*\d+(?:\.\d+)?,\s*h:\s*(\d+(?:\.\d+)?)/);
if(!match)throw Error('Player render height not found');
const playerHeight=Number(match[1]),cycleHeights={};
for(const motion of ['walking','running']){
 const cycles=body.cycles?.[motion];
 if(!Array.isArray(cycles)||cycles.length!==8||cycles.some(c=>!Number.isInteger(c.height)||c.height<=0))throw Error('Incomplete directional cycles');
 cycleHeights[motion]=cycles.map(c=>c.height);
}
const unique=[...new Set(Object.values(cycleHeights).flat())];
if(unique.length!==1)throw Error('Player render scale differs by locomotion direction');
const scale=playerHeight/unique[0];
const shot=planShot(0,1,0,true),ball={z:0,vz:shot.vz,gravity:shot.gravity};let minZ=0,apexFrame=0,landingFrame=null;
for(let frame=1;frame<=300;frame++){
 Object.assign(ball,advanceShotAirborne(ball));
 if(ball.z<minZ){minZ=ball.z;apexFrame=frame;}
 if(ball.z>=0){landingFrame=frame;break;}
}
if(!landingFrame)throw Error('Simulated shot did not land');
const dimensions=nativeDimensions[1],field=fieldDimensions(1);
const result={schema:'issd-native-web-scale-diagnostic/v1',source:{locomotionSha256:createHash('sha256').update(bodyBytes).digest('hex'),heightEvidence:'docs/issd-ball-height-pixels.json',nativeCrossbarCandidate:'dist/native-crossbar.mjs'},player:{renderHeightWorld:playerHeight,nativeCellHeights:cycleHeights,renderWorldUnitsPerNativeCellPixel:scale},field:{stadium:1,nativeWidth:dimensions[0],nativeHeight:dimensions[1],browserWidth:field.w,browserHeight:field.h,browserUnitsPerNativeX:field.w/dimensions[0],browserUnitsPerNativeY:field.h/dimensions[1]},conditionalHeightProjection:{assumption:'One native screenshot pixel maps through the locomotion cell scale; unverified as a physics conversion.',nativeCandidateHeights:[56,64],browserWorldCandidateHeights:[56*scale,64*scale]},browserShot:{input:'team 0, right, high',initialVz:shot.vz,gravity:shot.gravity,simulatedPeakHeight:-minZ,apexFrame,landingFrame,method:'advanceShotAirborne, one fixed tick at a time, no impacts'},limitations:['The 38/52 ratio describes the captured runtime-body and action reference scale; other rendering fallbacks may differ.', 'Locomotion cells contain transparency; their render scale does not prove a native-to-web physical unit mapping.','Native height-to-pixel observations cover only two heights from one synthetic scene.','Shot simulation excludes player contact, crossbar collision, and rebounds; it is not proof of every in-game trajectory.','Native field X/Y ratios are browser design choices; crossbar and net geometry are not established by this calculation.']};
writeFileSync(new URL('../docs/issd-native-web-scale-diagnostic.json',import.meta.url),JSON.stringify(result,null,2)+'\n');
console.log(`OK: cells ${unique[0]} -> ${playerHeight}; conditional -56 = ${(56*scale).toFixed(2)} web units; free high-shot peak ${(-minZ).toFixed(2)}`);
