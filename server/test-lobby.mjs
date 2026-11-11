import {createOnlineInputSession} from '../dist/online-input-session.mjs';
import {prepareOnlineMatch} from '../dist/online-match-setup.mjs';
import {readFileSync} from 'node:fs';
import {decodePairedInputs} from '../dist/paired-inputs.mjs';
import {dispatchTeamInputs,moveTeamInputs} from '../dist/team-inputs.mjs';
import {ONLINE_BUILD} from '../dist/online-build.mjs';
import test from 'node:test';
import assert from 'node:assert/strict';
import {WebSocket} from 'ws';
import {createGameServer} from './app.mjs';
import {attachLobby} from './lobby.mjs';

function connect(url){return new Promise((resolve,reject)=>{const ws=new WebSocket(url),queue=[],waiters=[];ws.on('error',reject);ws.on('message',data=>{const msg=JSON.parse(data);if(waiters.length)waiters.shift()(msg);else queue.push(msg);});ws.on('open',()=>resolve({ws,next:()=>queue.length?Promise.resolve(queue.shift()):new Promise(r=>waiters.push(r)),send:msg=>ws.send(JSON.stringify(msg))}));});}
test('two clients create, join, leave and clean up an ephemeral room',async t=>{
 const server=await createGameServer({root:'dist'}),lobby=await attachLobby(server);
 await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
 const url=`ws://127.0.0.1:${server.address().port}/api/v1/lobby`;
 const a=await connect(url),b=await connect(url),c=await connect(url);
 t.after(async()=>{for(const p of [a,b,c])p.ws.terminate();await new Promise(r=>lobby.close(r));await new Promise(r=>server.close(r));});
 for(const p of [a,b,c]){const hello=await p.next();assert.equal(hello.type,'connected');assert.equal(hello.protocol,2);assert.equal(hello.teams.length,36);}
 a.send({type:'create'});assert.equal((await a.next()).code,'protocol_mismatch');
 a.send({type:'create',protocol:2,build:'outdated'});assert.equal((await a.next()).code,'build_mismatch');
 a.send({type:'create',protocol:2,build:ONLINE_BUILD});const room=await a.next();assert.match(room.code,/^[A-F0-9]{8}$/);assert.equal(room.players,1);assert.equal(room.phase,'waiting');
 b.send({type:'join',protocol:1,code:room.code});assert.equal((await b.next()).code,'protocol_mismatch');
 b.send({type:'join',protocol:2,build:ONLINE_BUILD,code:room.code.toLowerCase()});assert.equal((await a.next()).players,2);assert.equal((await b.next()).players,2);
 c.send({type:'join',protocol:2,build:ONLINE_BUILD,code:room.code});assert.equal((await c.next()).code,'room_full');
 b.send({type:'settings',stadium:6,gameTime:0});assert.equal((await b.next()).code,'host_only');
 a.send({type:'settings',stadium:999,gameTime:0});assert.equal((await a.next()).code,'invalid_settings');
 c.send({type:'ready',ready:true});assert.equal((await c.next()).code,'not_in_room');
 a.send({type:'ready',ready:'true'});assert.equal((await a.next()).code,'invalid_ready');
 a.send({type:'ready',ready:true});assert.equal((await a.next()).code,'selection_required');
 a.send({type:'selection',team:999,kit:0});assert.equal((await a.next()).code,'invalid_selection');
 a.send({type:'input-test',input:{tick:0,held:0,actions:[]}});assert.equal((await a.next()).code,'room_not_ready');
 a.send({type:'selection',team:0,kit:1});assert.equal((await a.next()).participants[0].team,0);assert.equal((await b.next()).participants[0].kit,1);
 a.send({type:'ready',ready:true});assert.equal((await a.next()).participants[0].ready,true);assert.equal((await b.next()).participants[0].ready,true);
 b.send({type:'selection',team:1,kit:0});assert.equal((await a.next()).participants[0].ready,false);await b.next();
 a.send({type:'ready',ready:true});await a.next();await b.next();
 b.send({type:'ready',ready:true});const readyA=await a.next(),readyB=await b.next();assert.equal(readyA.phase,'ready');assert.equal(readyB.phase,'ready');assert.equal(readyA.inputEpoch,readyB.inputEpoch);assert.deepEqual(readyA.matchSetup,readyB.matchSetup);const baseCatalog=JSON.parse(readFileSync(new URL('../dist/data/issd-rom-catalog.json',import.meta.url),'utf8')),layouts=JSON.parse(readFileSync(new URL('../dist/data/issd-stadium-layouts.json',import.meta.url),'utf8')).layouts;const preparedA=prepareOnlineMatch(readyA.matchSetup,baseCatalog,layouts,ONLINE_BUILD),preparedB=prepareOnlineMatch(readyB.matchSetup,baseCatalog,layouts,ONLINE_BUILD);assert.ok(preparedA);assert.deepEqual(preparedA,preparedB);assert.deepEqual(readyA.matchSetup,{epoch:readyA.inputEpoch,build:ONLINE_BUILD,settings:{stadium:1,gameTime:1},sides:[{team:0,kit:'away'},{team:1,kit:'home'}]});const epoch=readyA.inputEpoch;assert.match(epoch,/^[0-9a-f]{32}$/);
 a.send({type:'prepared',epoch:'old'});assert.equal((await a.next()).code,'stale_input_epoch');
 a.send({type:'prepared',epoch});const acknowledgementA=await a.next(),acknowledgementB=await b.next();assert.equal(acknowledgementA.participants[0].prepared,true);assert.equal(acknowledgementB.participants[1].prepared,false);
 b.send({type:'prepared',epoch});assert.ok((await a.next()).participants.every(player=>player.prepared));assert.ok((await b.next()).participants.every(player=>player.prepared));
 a.send({type:'input-test',epoch,input:{tick:0,held:1,actions:['pass','shot']}});assert.deepEqual(await b.next(),{type:'input-test',epoch,seat:1,input:{tick:0,held:1,actions:['pass','shot']}});
 a.send({type:'input-test',epoch,input:{tick:0,held:1,actions:[]}});assert.equal((await a.next()).code,'unexpected_tick');
 a.send({type:'input-test',epoch,input:{tick:1,held:32,actions:[]}});assert.equal((await a.next()).code,'invalid_input');
 b.send({type:'input-test',epoch,input:{tick:0,held:16,actions:['press']}});assert.deepEqual(await a.next(),{type:'input-test',epoch,seat:2,input:{tick:0,held:16,actions:['press']}});
 a.send({type:'input-pair-test',epoch,input:{tick:0,held:1,actions:['pass']}});
 b.send({type:'input-pair-test',epoch,input:{tick:0,held:16,actions:['press']}});
 const pairA=await a.next(),pairB=await b.next();
 assert.deepEqual(pairA,{type:'input-pair-test',epoch,tick:0,inputs:[{tick:0,held:1,actions:['pass']},{tick:0,held:16,actions:['press']}]});assert.deepEqual(pairB,pairA);
 const decoded=decodePairedInputs(pairA,epoch,0),actors=new Map([[0,{team:0,x:0,y:0,vx:0,vy:0}],[1,{team:1,x:0,y:0,vx:0,vy:0}]]),actions=[];
 const handlers={getActor:team=>actors.get(team),pass:actor=>actions.push(['pass',actor.team]),press:actor=>actions.push(['press',actor.team]),shoot:()=>{},switchPlayer:()=>{},reset:()=>{}};
 dispatchTeamInputs(decoded,handlers);moveTeamInputs(decoded,handlers.getActor,1/60,(_actor,x,y)=>({x,y}));
 assert.deepEqual(actions,[['pass',0],['press',1]]);assert.ok(actors.get(0).y<0);assert.equal(actors.get(1).y,0);

 a.send({type:'input-pair-test',epoch,input:{tick:1,held:0,actions:[]}});
 a.send({type:'settings',stadium:6,gameTime:0});const settingsA=await a.next(),settingsB=await b.next();assert.deepEqual(settingsA.settings,{stadium:6,gameTime:0});assert.deepEqual(settingsA.settings,settingsB.settings);assert.equal(settingsA.matchSetup,null);assert.ok(settingsA.participants.every(player=>!player.ready&&!player.prepared));
 a.send({type:'ready',ready:true});await a.next();await b.next();b.send({type:'ready',ready:true});const updatedReady=await a.next();await b.next();assert.deepEqual(updatedReady.matchSetup.settings,{stadium:6,gameTime:0});
 b.send({type:'ready',ready:false});const changedA=await a.next();await b.next();assert.notEqual(changedA.inputEpoch,epoch);assert.equal(changedA.matchSetup,null);
 b.send({type:'ready',ready:true});const newA=await a.next();await b.next();assert.notEqual(newA.inputEpoch,epoch);
 a.send({type:'input-test',epoch,input:{tick:0,held:0,actions:[]}});assert.equal((await a.next()).code,'stale_input_epoch');
 a.send({type:'input-test',epoch:newA.inputEpoch,input:{tick:0,held:0,actions:[]}});assert.equal((await b.next()).epoch,newA.inputEpoch);
 a.send({type:'input-pair-test',epoch,input:{tick:1,held:0,actions:[]}});assert.equal((await a.next()).code,'stale_input_epoch');
 a.send({type:'input-pair-test',epoch:newA.inputEpoch,input:{tick:0,held:2,actions:[]}});
 b.send({type:'input-pair-test',epoch:newA.inputEpoch,input:{tick:0,held:1,actions:[]}});
 assert.equal((await a.next()).tick,0);assert.equal((await b.next()).tick,0);
 b.send({type:'leave'});const afterLeave=await a.next();assert.equal(afterLeave.players,1);assert.equal(afterLeave.matchSetup,null);assert.equal(afterLeave.participants[0].ready,false);assert.equal((await b.next()).type,'left');
 a.send({type:'leave'});assert.equal((await a.next()).type,'left');
 c.send({type:'join',protocol:2,build:ONLINE_BUILD,code:room.code});assert.equal((await c.next()).code,'room_not_found');
 c.send({type:'join',protocol:2,build:ONLINE_BUILD,code:'../x'});assert.equal((await c.next()).code,'invalid_room_code');
});

test('heartbeat removes an unresponsive participant',async t=>{
 const server=await createGameServer({root:'dist'}),lobby=await attachLobby(server,{heartbeatMs:50});
 await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
 const url=`ws://127.0.0.1:${server.address().port}/api/v1/lobby`;
 const active=await connect(url);
 const silent=new WebSocket(url,{autoPong:false});
 const queue=[];silent.on('message',data=>queue.push(JSON.parse(data)));
 await new Promise((resolve,reject)=>{silent.once('open',resolve);silent.once('error',reject);});
 t.after(async()=>{active.ws.terminate();silent.terminate();await new Promise(r=>lobby.close(r));await new Promise(r=>server.close(r));});
 await active.next();active.send({type:'create',protocol:2,build:ONLINE_BUILD});const room=await active.next();
 silent.send(JSON.stringify({type:'join',protocol:2,build:ONLINE_BUILD,code:room.code}));assert.equal((await active.next()).players,2);
 const update=await Promise.race([active.next(),new Promise((_,reject)=>setTimeout(()=>reject(new Error('heartbeat timed out')),1000))]);
 assert.equal(update.players,1);assert.equal(update.phase,'waiting');
});

test('host transfers on departure and remains host when a new player joins',async t=>{
 const server=await createGameServer({root:'dist'}),lobby=await attachLobby(server);
 await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
 const url=`ws://127.0.0.1:${server.address().port}/api/v1/lobby`;
 const a=await connect(url),b=await connect(url),c=await connect(url);
 t.after(async()=>{for(const p of [a,b,c])p.ws.terminate();await new Promise(r=>lobby.close(r));await new Promise(r=>server.close(r));});
 await a.next();await b.next();await c.next();
 a.send({type:'create',protocol:2,build:ONLINE_BUILD});const room=await a.next();
 b.send({type:'join',protocol:2,build:ONLINE_BUILD,code:room.code});await a.next();await b.next();
 a.send({type:'leave'});const alone=await b.next();await a.next();assert.equal(alone.hostSeat,2);
 c.send({type:'join',protocol:2,build:ONLINE_BUILD,code:room.code});const bState=await b.next(),cState=await c.next();assert.equal(bState.hostSeat,2);assert.equal(cState.hostSeat,2);assert.equal(cState.seat,1);
 c.send({type:'settings',stadium:6,gameTime:1});assert.equal((await c.next()).code,'host_only');
 b.send({type:'settings',stadium:6,gameTime:1});assert.equal((await b.next()).settings.stadium,6);assert.equal((await c.next()).settings.stadium,6);
});


test('two clients exchange bounded ordered inputs and stop after room changes',async t=>{
 const server=await createGameServer({root:'dist'}),lobby=await attachLobby(server);
 await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
 const url=`ws://127.0.0.1:${server.address().port}/api/v1/lobby`;
 const a=await connect(url),b=await connect(url);
 t.after(async()=>{a.ws.terminate();b.ws.terminate();await new Promise(r=>lobby.close(r));await new Promise(r=>server.close(r));});
 await a.next();await b.next();a.send({type:'create',protocol:2,build:ONLINE_BUILD});const room=await a.next();
 b.send({type:'join',protocol:2,build:ONLINE_BUILD,code:room.code});await a.next();await b.next();
 a.send({type:'selection',team:0,kit:0});await a.next();await b.next();
 b.send({type:'selection',team:1,kit:1});await a.next();await b.next();
 a.send({type:'ready',ready:true});await a.next();await b.next();
 b.send({type:'ready',ready:true});const stateA=await a.next(),stateB=await b.next();assert.equal(stateA.inputEpoch,stateB.inputEpoch);
 const sessionA=createOnlineInputSession(a.ws,1,stateA.inputEpoch),sessionB=createOnlineInputSession(b.ws,2,stateB.inputEpoch);
 const left={up:false,down:false,left:true,right:false,run:false,actions:['pass']},right={up:false,down:false,left:false,right:true,run:true,actions:[]};
 for(let tick=0;tick<8;tick++){assert.equal(sessionA.submit(left).tick,tick);assert.equal(sessionB.submit(right).tick,tick);}
 assert.equal(sessionA.submit(left).reason,'window_full');
 for(let tick=0;tick<8;tick++){
  assert.equal(sessionA.receive(await a.next()),true);assert.equal(sessionB.receive(await b.next()),true);
  const frameA=sessionA.take(),frameB=sessionB.take();assert.equal(frameA.tick,tick);assert.equal(frameB.tick,tick);
  assert.equal(frameA.inputs.get(0).left,true);assert.equal(frameB.inputs.get(1).right,true);
 }
 assert.equal(sessionA.submit(left).tick,8);assert.equal(sessionB.submit(right).tick,8);
 assert.equal(sessionA.receive(await a.next()),true);assert.equal(sessionB.receive(await b.next()),true);
 assert.equal(sessionA.take().tick,8);assert.equal(sessionB.take().tick,8);
 b.send({type:'ready',ready:false});sessionA.receive(await a.next());sessionB.receive(await b.next());
 assert.equal(sessionA.state,'room_changed');assert.equal(sessionB.state,'room_changed');assert.equal(sessionA.submit(left).ok,false);
});

// The diagnostic consumes its own cycle zero; an experimental match uses a
// separate epoch and queue and cannot start before both clients are prepared.
test('experimental match start uses a fresh input epoch and is invalidated',async t=>{
 const server=await createGameServer({root:'dist'}),lobby=await attachLobby(server);
 await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
 const url=`ws://127.0.0.1:${server.address().port}/api/v1/lobby`;
 const a=await connect(url),b=await connect(url);
 t.after(async()=>{a.ws.terminate();b.ws.terminate();await new Promise(r=>lobby.close(r));await new Promise(r=>server.close(r));});
 await a.next();await b.next();a.send({type:'create',protocol:2,build:ONLINE_BUILD});const room=await a.next();
 b.send({type:'join',protocol:2,build:ONLINE_BUILD,code:room.code});await a.next();await b.next();
 a.send({type:'match-test-start',epoch:room.inputEpoch});assert.equal((await a.next()).code,'room_not_prepared');
 a.send({type:'selection',team:0,kit:0});await a.next();await b.next();
 b.send({type:'selection',team:1,kit:1});await a.next();await b.next();
 a.send({type:'ready',ready:true});await a.next();await b.next();
 b.send({type:'ready',ready:true});const ready=await a.next();await b.next();
 a.send({type:'prepared',epoch:ready.inputEpoch});await a.next();await b.next();
 b.send({type:'prepared',epoch:ready.inputEpoch});await a.next();await b.next();
 a.send({type:'input-pair-test',epoch:ready.inputEpoch,input:{tick:0,held:0,actions:[]}});b.send({type:'input-pair-test',epoch:ready.inputEpoch,input:{tick:0,held:0,actions:[]}});assert.equal((await a.next()).tick,0);assert.equal((await b.next()).tick,0);
 b.send({type:'match-test-start',epoch:ready.inputEpoch});assert.equal((await b.next()).code,'host_only');
 a.send({type:'match-test-start',epoch:'old'});assert.equal((await a.next()).code,'stale_input_epoch');
 a.send({type:'match-test-start',epoch:ready.inputEpoch});const startA=await a.next(),startB=await b.next();
 assert.equal(startA.seat,1);assert.equal(startB.seat,2);assert.deepEqual(startA.setup,startB.setup);assert.notEqual(startA.setup.epoch,ready.inputEpoch);
 a.send({type:'match-test-start',epoch:ready.inputEpoch});assert.equal((await a.next()).code,'match_test_active');
 a.send({type:'match-test-input',epoch:ready.inputEpoch,input:{tick:0,held:1,actions:[]}});assert.equal((await a.next()).code,'stale_input_epoch');
 a.send({type:'match-test-input',epoch:startA.setup.epoch,input:{tick:0,held:1,actions:[]}});
 b.send({type:'match-test-input',epoch:startA.setup.epoch,input:{tick:0,held:2,actions:[]}});
 const pairA=await a.next(),pairB=await b.next();assert.deepEqual(pairA,pairB);assert.equal(pairA.type,'match-test-pair');assert.equal(pairA.tick,0);
 b.send({type:'ready',ready:false});await a.next();await b.next();
 a.send({type:'match-test-input',epoch:startA.setup.epoch,input:{tick:1,held:0,actions:[]}});assert.equal((await a.next()).code,'match_test_inactive');
});
