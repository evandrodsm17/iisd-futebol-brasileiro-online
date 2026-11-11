import test from 'node:test';
import assert from 'node:assert/strict';
import {createGameServer} from './app.mjs';
import {attachLobby} from './lobby.mjs';
import {setupOnlineLobby} from '../dist/online-lobby.mjs';

function mockDocument(){
 const elements=new Map();
 return {createElement(){return {value:'',textContent:''};},getElementById(id){if(!elements.has(id))elements.set(id,{value:'',textContent:'',disabled:false,hidden:false,events:{},replaceChildren(){},setAttribute(){},addEventListener(type,fn){this.events[type]=fn;},click(){this.events.click?.();}});return elements.get(id);}};
}
async function until(check){const end=Date.now()+2000;while(!check()){if(Date.now()>end)throw new Error('Tempo esgotado aguardando estado da sala');await new Promise(resolve=>setTimeout(resolve,10));}}
test('browser lobby connects two participants and handles leaving',async t=>{
 const server=await createGameServer({root:'dist'}),lobby=await attachLobby(server);
 await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
 const location={protocol:'http:',host:`127.0.0.1:${server.address().port}`};
 const a=mockDocument(),b=mockDocument();let back=false;
 const first=setupOnlineLobby(a,()=>{back=true;},WebSocket,location),second=setupOnlineLobby(b,()=>{},WebSocket,location);
 t.after(async()=>{a.getElementById('online-back').click();b.getElementById('online-back').click();for(const ws of lobby.clients)ws.terminate();await new Promise(r=>lobby.close(r));await new Promise(r=>server.close(r));});
 first.open();second.open();await until(()=>!a.getElementById('online-create').disabled&&!b.getElementById('online-create').disabled);
 a.getElementById('online-create').click();await until(()=>!a.getElementById('online-room').hidden);
 b.getElementById('online-input').value=a.getElementById('online-code').textContent;b.getElementById('online-join').click();
 await until(()=>a.getElementById('online-players').textContent.includes('2 de 2')&&b.getElementById('online-players').textContent.includes('2 de 2'));
 a.getElementById('online-team').value='0';a.getElementById('online-team').events.change();
 await until(()=>b.getElementById('online-selections').textContent.includes('Italy'));
 b.getElementById('online-team').value='1';b.getElementById('online-team').events.change();
 await until(()=>a.getElementById('online-selections').textContent.includes('Holland'));
 a.getElementById('online-ready').click();await until(()=>b.getElementById('online-readiness').textContent.includes('1P: pronto'));
 b.getElementById('online-ready').click();await until(()=>a.getElementById('online-readiness').textContent.includes('2P: pronto'));
 await until(()=>a.getElementById('online-status').textContent.includes('Ambos estão prontos'));
 await until(()=>a.getElementById('online-validation').textContent.includes('verificados')&&b.getElementById('online-validation').textContent.includes('verificados'));
 a.getElementById('online-stadium').value='6';a.getElementById('online-time').value='0';a.getElementById('online-stadium').events.change();
 await until(()=>b.getElementById('online-stadium').value==='6'&&b.getElementById('online-time').value==='0');
 assert.equal(b.getElementById('online-stadium').disabled,true);assert.match(a.getElementById('online-readiness').textContent,/1P: aguardando/);
 assert.equal(a.getElementById('online-validation').textContent,'');assert.equal(b.getElementById('online-validation').textContent,'');
 b.getElementById('online-back').click();await until(()=>a.getElementById('online-players').textContent.includes('1 de 2'));
 assert.match(a.getElementById('online-readiness').textContent,/1P: aguardando/);
 a.getElementById('online-back').click();assert.equal(back,true);
});
