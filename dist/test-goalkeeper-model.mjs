import {inputAxes} from './input-frame.mjs';
import assert from 'node:assert/strict';
import {goalkeeperHome,goalkeeperShotContact,applyGoalkeeperShotContact,predictGoalkeeperShot} from './goalkeeper-model.mjs';
import {classifyFieldExit,classifyFieldExitWithTime} from './field-events.mjs';
import {planShot,planCpuShotVertical,planShotVertical,advanceShotAirborne} from './shot-model.mjs';
import {screenDirectionForVector} from './action-visual.mjs';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';
const field={x:0,y:0,w:200,h:100,goalH:40};
const left={team:0,x:32,y:50,roster:{position:'GK'}},right={team:1,x:168,y:50,formationRole:'GK'};
assert.deepEqual(goalkeeperHome(left,{y:99},field),{x:32,y:60});
assert.deepEqual(goalkeeperHome(right,{y:0},field),{x:168,y:40});
const low=planShot(0,1,0),high=planShot(0,1,0,true),reverse=planShot(0,-1,1);
assert.ok(Math.abs(low.vz+0.56)<1e-12&&Math.abs(low.gravity-0.07)<1e-12,'low shot uses scaled native type-5 parameter 2');
assert.ok(Math.abs(high.vz+2.8)<1e-12&&Math.abs(high.gravity-0.14)<1e-12,'high shot uses scaled native type-5 parameter 11');
assert.deepEqual(planShot(1,-1,0,true).gravity,high.gravity,'both teams share the same vertical trajectory');
assert.deepEqual(planCpuShotVertical(true),planShotVertical(4),'CPU goal attempt uses provisional native parameter 4');
assert.deepEqual(planCpuShotVertical(false),{vz:high.vz,gravity:high.gravity},'CPU clearance shares the high trajectory');
assert.deepEqual(advanceShotAirborne({z:0,vz:-7,gravity:7168/65536}),{z:-6.890625,vz:-6.890625},'native sample applies acceleration before moving');
assert.deepEqual(advanceShotAirborne({z:-6.890625,vz:-6.890625,gravity:7168/65536}),{z:-13.671875,vz:-6.78125},'second observed airborne step');
assert.throws(()=>advanceShotAirborne({z:0,vz:0,gravity:NaN}),RangeError);
assert.ok(low.vx>0&&high.vz<low.vz&&reverse.vx<0&&reverse.vy>0);
assert.equal(screenDirectionForVector(reverse.vx,reverse.vy,0,2),5,'a diagonal shot keeps its diagonal visual sector');
const diagonalRight=planShot(0,1,-1);
assert.equal(screenDirectionForVector(diagonalRight.vx,diagonalRight.vy,0,2),1,'opposite diagonal is recognized');
const diagonalDown=planShot(0,1,1),diagonalLeft=planShot(0,-1,-1);
assert.equal(screenDirectionForVector(diagonalDown.vx,diagonalDown.vy,0,2),3);
assert.equal(screenDirectionForVector(diagonalLeft.vx,diagonalLeft.vy,0,2),7);
for(const [direction,x,y] of [[0,0,-1],[1,1,-1],[2,1,0],[3,1,1],[4,0,1],[5,-1,1],[6,-1,0],[7,-1,-1]]){
 const shot=planShot(0,0,0,false,direction);
 assert.equal(Math.sign(shot.vx),x,`facing ${direction} horizontal`);
 assert.equal(Math.sign(shot.vy),y,`facing ${direction} vertical`);
 assert.ok(Math.abs(Math.hypot(shot.vx,shot.vy)-6.5)<1e-9);
}
assert.equal(planShot(0,0,0).vx,6.5,'missing facing uses attacking direction');
assert.equal(planShot(1,0,0).vx,-6.5,'fallback respects the other team');
const before={x:150,y:50,z:-1},ball={x:174,y:50,z:-1,vx:5,vy:0,vz:0,owner:null,actionKind:'shot'};
const incoming={x:100,y:50,z:0,vx:7,vy:0,vz:0,gravity:.125,owner:null,actionKind:'shot'};
assert.equal(predictGoalkeeperShot(incoming,[left,right],field,0)?.keeper,right,'anticipates an incoming shot');
assert.equal(predictGoalkeeperShot({...incoming,vx:-7},[left,right],field,0),null,'does not anticipate a shot moving away');
assert.equal(predictGoalkeeperShot({...incoming,actionKind:'pass'},[left,right],field,0),null,'does not apply the shot heuristic to passes');
let contact=goalkeeperShotContact(before,ball,[left,right],field,0);assert.equal(contact?.keeper,right);assert.equal(contact.kind,'catch');
assert.equal(applyGoalkeeperShotContact(ball,contact),1);assert.equal(ball.owner,right);assert.equal(ball.vx,0);
const highBall={x:174,y:59,z:-15,vx:6.5,vy:0,vz:0,owner:null,actionKind:'shot'};
contact=goalkeeperShotContact({...before,y:59,z:-15},highBall,[left,right],field,0);assert.equal(contact.kind,'parry');
assert.equal(applyGoalkeeperShotContact(highBall,contact),1);assert.equal(highBall.owner,null);assert.ok(highBall.vx<0);assert.ok(highBall.vy>0);
const wide={x:174,y:65,z:-15,vx:6.5,vy:0,vz:0,owner:null,actionKind:'shot'};
const wideContact=goalkeeperShotContact({...before,y:65,z:-15},wide,[right],field,0);assert.equal(wideContact.kind,'parry');applyGoalkeeperShotContact(wide,wideContact);assert.ok(wide.vx>0&&wide.vy>0,'desvio lateral pode seguir para a linha de fundo');
const wideExit=classifyFieldExit({x:wide.x,y:wide.y,z:0},{x:wide.x+wide.vx*17,y:wide.y+wide.vy*17,z:0},field,1);assert.equal(wideExit.type,'corner');
assert.equal(goalkeeperShotContact(before,{...ball,owner:null,actionKind:'pass'},[right],field,0),null);
assert.equal(goalkeeperShotContact(before,{...ball,owner:null,actionKind:'shot',x:174,y:90},[right],field,0),null,'chute fora do alcance passa');
assert.equal(goalkeeperShotContact(before,{...ball,owner:null,actionKind:'shot',x:174,z:-30},[right],field,0),null,'bola alta demais não é defendida');
const corner=classifyFieldExit({x:190,y:10,z:0},{x:210,y:10,z:0},field,1);assert.equal(corner.type,'corner','último toque do defensor concede escanteio');
const source=readFileSync(new URL('./game.js',import.meta.url),'utf8'),shoot=source.match(/^function shoot\(actor,input\) \{.*\}$/m);assert.ok(shoot);
const orderBlock=source.match(/  const keeperContact=goalkeeperShotContact\(previousBall,ball,players,field,lastTouchTeam\);[\s\S]*?  const exit=boundary\?\.event\?\?null;/);assert.ok(orderBlock);
function shotOrder(team,keeperX){
 return vm.runInNewContext(`(()=>{const previousBall={x:team?10:190,y:50,z:-1},ball={x:team?-20:220,y:50,z:-1,vx:team?-30:30,vy:0,vz:0,owner:null,actionKind:'shot'},players=[{team:1-team,x:keeperX,y:50,roster:{position:'GK'}}];let lastTouchTeam=team;${orderBlock[0]};return {exit,ball,lastTouchTeam};})()`,{team,keeperX,field,goalkeeperShotContact,applyGoalkeeperShotContact,classifyFieldExitWithTime});
}
for(const [team,before,after] of [[0,200,210],[1,0,-10]]){
 const saved=shotOrder(team,before),goal=shotOrder(team,after);
 assert.equal(saved.exit,null,'keeper contact before crossing prevents the original goal event');
 assert.equal(saved.lastTouchTeam,1-team);
 assert.equal(goal.exit?.type,'goal','crossing before contact scores even if the keeper reaches the ball later');
 assert.equal(goal.lastTouchTeam,team);
}
const flightBlock=source.match(/  if\(ball\.owner\) \{[\s\S]*?(?=  if\(ball\.z >= 0\))/);assert.ok(flightBlock);
const flight=vm.runInNewContext(`(()=>{const ball={owner:null,actionKind:'shot',x:0,y:0,z:-30,vx:6,vy:-2,vz:-1,gravity:.07},frames=1;for(let i=0;i<5;i++){${flightBlock[0]}}return ball;})()`,{advanceShotAirborne,Math,Object});
assert.deepEqual([flight.x,flight.y,flight.vx,flight.vy],[30,-10,6,-2],'free airborne shots retain horizontal velocity');
const verticalBlock=source.match(/  \/\/ Only the shot's observed airborne branch[\s\S]*?(?=  const predictedKeeper)/);assert.ok(verticalBlock);
function verticalStep(kind){return vm.runInNewContext(`(()=>{const ball={owner:null,actionKind:kind,z:0,vz:-7,gravity:7168/65536,vx:1,vy:0},frames=1,PASS_FRICTION=.04;${verticalBlock[0]};return {z:ball.z,vz:ball.vz};})()`,{kind,advanceShotAirborne,Math,Object});}
assert.deepEqual({...verticalStep('shot')},{z:-6.890625,vz:-6.890625},'game applies observed order to shot flight');
assert.deepEqual({...verticalStep('pass')},{z:-7,vz:-6.890625},'other ball modes retain existing order');
const input=vm.runInNewContext(`(()=>{const controlled={team:0},ball={owner:controlled},keys=new Set(['up','run']),bindings={right:'right',left:'left',up:'up',down:'down',run:'run'};let applied=null;const simulationNow=()=>100,resetAt=0,launchShot=(actor,aim,plan)=>{applied=plan;};${shoot[0]};shoot(controlled,{up:keys.has('up'),down:keys.has('down'),left:keys.has('left'),right:keys.has('right'),run:keys.has('run')});return applied;})()`,{inputAxes,planShot,screenToWorldVector:(_p,x,y)=>({x,y})});
assert.equal(input.vx,0,'cima sem direção horizontal não adiciona componente lateral');assert.ok(input.vy<0);assert.equal(input.vz,high.vz,'correr + chute seleciona trajetória alta');
console.log('OK: direção e altura do chute, posicionamento, defesa e rebote');
