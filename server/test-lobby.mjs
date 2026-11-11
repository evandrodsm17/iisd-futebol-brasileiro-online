import test from 'node:test';
import assert from 'node:assert/strict';
import {WebSocket} from 'ws';
import {createGameServer} from './app.mjs';
import {attachLobby} from './lobby.mjs';

function connect(url){return new Promise((resolve,reject)=>{const ws=new WebSocket(url),queue=[],waiters=[];ws.on('error',reject);ws.on('message',data=>{const msg=JSON.parse(data);if(waiters.length)waiters.shift()(msg);else queue.push(msg);});ws.on('open',()=>resolve({ws,next:()=>queue.length?Promise.resolve(queue.shift()):new Promise(r=>waiters.push(r)),send:msg=>ws.send(JSON.stringify(msg))}));});}
test('two clients create, join, leave and clean up an ephemeral room',async t=>{
 const server=await createGameServer({root:'dist'}),lobby=attachLobby(server);
 await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
 const url=`ws://127.0.0.1:${server.address().port}/api/v1/lobby`;
 const a=await connect(url),b=await connect(url),c=await connect(url);
 t.after(async()=>{for(const p of [a,b,c])p.ws.terminate();await new Promise(r=>lobby.close(r));await new Promise(r=>server.close(r));});
 for(const p of [a,b,c])assert.deepEqual(await p.next(),{type:'connected',protocol:1});
 a.send({type:'create'});const room=await a.next();assert.match(room.code,/^[A-F0-9]{8}$/);assert.equal(room.players,1);
 b.send({type:'join',code:room.code.toLowerCase()});assert.equal((await a.next()).players,2);assert.equal((await b.next()).players,2);
 c.send({type:'join',code:room.code});assert.equal((await c.next()).code,'room_full');
 c.send({type:'ready',ready:true});assert.equal((await c.next()).code,'not_in_room');
 a.send({type:'ready',ready:'true'});assert.equal((await a.next()).code,'invalid_ready');
 a.send({type:'ready',ready:true});assert.equal((await a.next()).participants[0].ready,true);assert.equal((await b.next()).participants[0].ready,true);
 b.send({type:'leave'});const afterLeave=await a.next();assert.equal(afterLeave.players,1);assert.equal(afterLeave.participants[0].ready,false);assert.equal((await b.next()).type,'left');
 a.send({type:'leave'});assert.equal((await a.next()).type,'left');
 c.send({type:'join',code:room.code});assert.equal((await c.next()).code,'room_not_found');
 c.send({type:'join',code:'../x'});assert.equal((await c.next()).code,'invalid_room_code');
});
