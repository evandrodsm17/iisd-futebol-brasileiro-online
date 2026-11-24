import test from 'node:test';
import assert from 'node:assert/strict';
import {spawn} from 'node:child_process';
import {createServer} from 'node:net';
import {readFile} from 'node:fs/promises';
import {networkInterfaces} from 'node:os';
import {WebSocket} from 'ws';

async function availablePort(){
 const server=createServer();await new Promise((resolve,reject)=>server.once('error',reject).listen(0,'127.0.0.1',resolve));
 const {port}=server.address();await new Promise(resolve=>server.close(resolve));return port;
}
function connect(url){
 return new Promise((resolve,reject)=>{
  const socket=new WebSocket(url),queue=[],waiters=[];
  socket.on('error',reject);socket.on('message',data=>{const message=JSON.parse(data);if(waiters.length)waiters.shift()(message);else queue.push(message);});
  socket.once('open',()=>resolve({socket,next:()=>queue.length?Promise.resolve(queue.shift()):new Promise(r=>waiters.push(r)),send:message=>socket.send(JSON.stringify(message))}));
 });
}
test('LAN launcher serves the game and two clients can share a room',{timeout:20000},async t=>{
 const port=await availablePort(),child=spawn(process.execPath,['server/lan.mjs'],{env:{...process.env,PORT:String(port)},stdio:['ignore','pipe','pipe']});
 let output='';child.stdout.on('data',data=>output+=data);child.stderr.on('data',data=>output+=data);
 t.after(()=>child.kill());
 await new Promise((resolve,reject)=>{
  const timeout=setTimeout(()=>reject(new Error(`Servidor não iniciou: ${output}`)),12000);
  const done=()=>{if(output.includes('Mantenha esta janela aberta.')){clearTimeout(timeout);resolve();}};
  child.stdout.on('data',done);child.once('exit',code=>{clearTimeout(timeout);reject(new Error(`Servidor terminou (${code}): ${output}`));});
 });
 assert.match(output,new RegExp(`http://127\\.0\\.0\\.1:${port}/`));
 const interfaces=Object.values(networkInterfaces()).flat().filter(x=>x?.family==='IPv4'&&!x.internal);
 if(interfaces.length)assert.ok(output.includes(`http://${interfaces[0].address}:${port}/`));
 const response=await fetch(`http://127.0.0.1:${port}/`);assert.equal(response.status,200);
 const networkHost=interfaces[0]?.address??'127.0.0.1';
 if(interfaces.length)assert.equal((await fetch(`http://${networkHost}:${port}/`)).status,200);
 const identity=await readFile(new URL('../dist/online-build.mjs',import.meta.url),'utf8');
 const build=identity.match(/ONLINE_BUILD = '([0-9a-f]{64})'/)?.[1];assert.ok(build);
 const a=await connect(`ws://127.0.0.1:${port}/api/v1/lobby`),b=await connect(`ws://${networkHost}:${port}/api/v1/lobby`);
 t.after(()=>{a.socket.terminate();b.socket.terminate();});
 assert.equal((await a.next()).type,'connected');assert.equal((await b.next()).type,'connected');
 a.send({type:'create',protocol:2,build});const room=await a.next();assert.match(room.code,/^[A-F0-9]{8}$/);
 b.send({type:'join',protocol:2,build,code:room.code});assert.equal((await a.next()).players,2);assert.equal((await b.next()).players,2);
});

test('LAN launcher explains a port conflict and exits',{timeout:15000},async t=>{
 const occupied=createServer();await new Promise(resolve=>occupied.listen(0,'0.0.0.0',resolve));
 t.after(()=>occupied.close());
 const child=spawn(process.execPath,['server/lan.mjs'],{env:{...process.env,PORT:String(occupied.address().port)},stdio:['ignore','pipe','pipe']});
 let output='';child.stdout.on('data',data=>output+=data);child.stderr.on('data',data=>output+=data);
 t.after(()=>child.kill());
 const code=await new Promise((resolve,reject)=>{child.once('error',reject);child.once('exit',resolve);});
 assert.equal(code,1);assert.match(output,/porta .* já está em uso/i);
});
