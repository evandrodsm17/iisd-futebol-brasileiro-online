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
 c.send({type:'ready',ready:true});assert.equal((await c.next()).code,'not_in_room');
 a.send({type:'ready',ready:'true'});assert.equal((await a.next()).code,'invalid_ready');
 a.send({type:'ready',ready:true});assert.equal((await a.next()).code,'selection_required');
 a.send({type:'selection',team:999,kit:0});assert.equal((await a.next()).code,'invalid_selection');
 a.send({type:'selection',team:0,kit:1});assert.equal((await a.next()).participants[0].team,0);assert.equal((await b.next()).participants[0].kit,1);
 a.send({type:'ready',ready:true});assert.equal((await a.next()).participants[0].ready,true);assert.equal((await b.next()).participants[0].ready,true);
 b.send({type:'selection',team:1,kit:0});assert.equal((await a.next()).participants[0].ready,false);await b.next();
 a.send({type:'ready',ready:true});await a.next();await b.next();
 b.send({type:'ready',ready:true});assert.equal((await a.next()).phase,'ready');assert.equal((await b.next()).phase,'ready');
 b.send({type:'leave'});const afterLeave=await a.next();assert.equal(afterLeave.players,1);assert.equal(afterLeave.participants[0].ready,false);assert.equal((await b.next()).type,'left');
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
