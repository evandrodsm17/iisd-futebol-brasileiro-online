import test from 'node:test';
import assert from 'node:assert/strict';
import {createGameServer} from './app.mjs';
import {attachLobby} from './lobby.mjs';
import {setupOnlineLobby} from '../dist/online-lobby.mjs';

function mockDocument(){
 const elements=new Map();
 return {getElementById(id){if(!elements.has(id))elements.set(id,{value:'',textContent:'',disabled:false,hidden:false,events:{},addEventListener(type,fn){this.events[type]=fn;},click(){this.events.click?.();}});return elements.get(id);}};
}
async function until(check){const end=Date.now()+2000;while(!check()){if(Date.now()>end)throw new Error('Tempo esgotado aguardando estado da sala');await new Promise(resolve=>setTimeout(resolve,10));}}
test('browser lobby connects two participants and handles leaving',async t=>{
 const server=await createGameServer({root:'dist'}),lobby=attachLobby(server);
 await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
 const location={protocol:'http:',host:`127.0.0.1:${server.address().port}`};
 const a=mockDocument(),b=mockDocument();let back=false;
 const first=setupOnlineLobby(a,()=>{back=true;},WebSocket,location),second=setupOnlineLobby(b,()=>{},WebSocket,location);
 t.after(async()=>{a.getElementById('online-back').click();b.getElementById('online-back').click();for(const ws of lobby.clients)ws.terminate();await new Promise(r=>lobby.close(r));await new Promise(r=>server.close(r));});
 first.open();second.open();await until(()=>!a.getElementById('online-create').disabled&&!b.getElementById('online-create').disabled);
 a.getElementById('online-create').click();await until(()=>!a.getElementById('online-room').hidden);
 b.getElementById('online-input').value=a.getElementById('online-code').textContent;b.getElementById('online-join').click();
 await until(()=>a.getElementById('online-players').textContent.includes('2 de 2')&&b.getElementById('online-players').textContent.includes('2 de 2'));
 b.getElementById('online-back').click();await until(()=>a.getElementById('online-players').textContent.includes('1 de 2'));
 a.getElementById('online-back').click();assert.equal(back,true);
});
