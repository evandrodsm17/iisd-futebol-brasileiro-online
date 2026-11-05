import assert from 'node:assert/strict';
import {beginCapturedTackleFall,isFallen,stopFallenPlayers} from './tackle-reaction.mjs';
const victim={vx:2,vy:3,roster:{position:'FW'}},request={screenDirection:5};
const renderer={duration:40,supports:r=>r.screenDirection===5};
assert.equal(beginCapturedTackleFall(victim,100,renderer,request,32),true);
assert.equal(victim.actionVisual.kind,'fall');
assert.equal(victim.vx,0);assert.equal(victim.vy,0);
assert.equal(isFallen(victim,139),true);assert.equal(isFallen(victim,140),false);
victim.vx=4;victim.vy=-2;const standing={vx:3,vy:2};
stopFallenPlayers([victim,standing],139);
assert.deepEqual([victim.vx,victim.vy],[0,0]);assert.deepEqual([standing.vx,standing.vy],[3,2]);
victim.vx=1;stopFallenPlayers([victim],140);assert.equal(victim.vx,1,'recuperado pode voltar a mover');
for(const [actor,body,req,height] of [[{roster:{position:'GK'}},renderer,request,32],[{},renderer,{screenDirection:6},32],[{},null,request,32],[{},renderer,request,null]]){
 assert.equal(beginCapturedTackleFall(actor,100,body,req,height),false);
 assert.equal(isFallen(actor,100),false);
}
console.log('OK: reação capturada, duração e contextos não suportados');
