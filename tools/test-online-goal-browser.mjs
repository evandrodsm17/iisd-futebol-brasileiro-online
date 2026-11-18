import {chromium} from 'playwright';
import assert from 'node:assert/strict';
import {createGameServer} from '../server/app.mjs';
import {attachLobby} from '../server/lobby.mjs';

const server=await createGameServer({root:'dist'}),lobby=await attachLobby(server);
await new Promise(r=>server.listen(0,'127.0.0.1',r));
const url=`http://127.0.0.1:${server.address().port}/?online-debug=1`;
const chrome=process.env.PLAYWRIGHT_CHROME_PATH || (process.platform==='win32'?'C:/Program Files/Google/Chrome/Application/chrome.exe':undefined);
let browser;const contexts=[];
try{
 browser=await chromium.launch({headless:true,...(chrome?{executablePath:chrome}:{})});
 const a=await browser.newContext(),b=await browser.newContext();contexts.push(a,b);
 const p=await a.newPage(),q=await b.newPage(),errors=[];
 for(const page of [p,q]){
  page.on('pageerror',e=>errors.push(e.message));await page.goto(url);
  await page.locator('[data-mode="online"]').click();await page.locator('#confirm-mode').click();
  await page.waitForFunction(()=>!document.querySelector('#online-create').disabled);
 }
 await p.locator('#online-create').click();await p.locator('#online-room').waitFor({state:'visible'});
 const code=await p.locator('#online-code').innerText();
 await q.locator('#online-input').fill(code);await q.locator('#online-join').click();await q.locator('#online-room').waitFor({state:'visible'});
 await p.locator('#online-open-selection').click();await q.locator('#online-open-selection').click();
 await p.locator('#setup-teams').waitFor({state:'visible'});await q.locator('#setup-teams').waitFor({state:'visible'});
 await p.getByRole('button',{name:'Brazil',exact:true}).click();await q.locator('#next-group').click();
 await q.getByRole('button',{name:'England',exact:true}).click();
 for(const page of [p,q])await page.waitForFunction(()=>!document.querySelector('#next-kits').disabled);
 await p.locator('#next-kits').click();await q.locator('#next-kits').click();
 for(const page of [p,q])await page.waitForFunction(()=>!document.querySelector('#next-settings').disabled);
 await p.locator('#next-settings').click();await q.locator('#next-settings').click();
 await p.locator('#online-ready').click();await q.locator('#online-ready').click();
 await p.waitForFunction(()=>!document.querySelector('#online-start-test').disabled,{timeout:10000});
 await p.locator('#online-start-test').click();
 for(const page of [p,q])await page.waitForFunction(()=>window.__onlineTestState?.tick>75,{timeout:15000});
 assert.equal((await p.evaluate(()=>window.__onlineTestState)).ball.owner,0);
 await q.keyboard.down('ArrowUp');await q.waitForTimeout(1300);await q.keyboard.up('ArrowUp');
 await p.keyboard.down('KeyE');await p.keyboard.down('ArrowRight');
 await p.waitForFunction(()=>window.__onlineTestState?.players.find(p=>p.team===0)?.x>1198,{timeout:12000});
 await p.keyboard.up('ArrowRight');await p.keyboard.up('KeyE');
 assert.equal((await p.evaluate(()=>window.__onlineTestState)).ball.owner,0,'attacker still has the ball');
 for(const page of [p,q])await page.evaluate(()=>{window.__goalSamples={};window.__goalSampler=setInterval(()=>{
  const state=window.__onlineTestState;if(state)window.__goalSamples[state.tick]=structuredClone(state);
 },4);});
 await p.keyboard.down('ArrowRight');await p.keyboard.down('ArrowDown');await p.keyboard.press('KeyA');
 await p.keyboard.up('ArrowDown');await p.keyboard.up('ArrowRight');
 for(const page of [p,q])await page.waitForFunction(()=>window.__onlineTestState?.score[0]===1,{timeout:10000});
 const start=await p.evaluate(()=>window.__onlineTestState.tick);
 await q.keyboard.down('ArrowLeft');
 await p.waitForFunction(t=>window.__onlineTestState?.tick>=t+20,start,{timeout:10000});
 const [home,away]=await Promise.all([p.evaluate(()=>window.__onlineTestState),q.evaluate(()=>window.__onlineTestState)]);
 for(const state of [home,away]){
  assert.deepEqual(state.score,[1,0]);assert.equal(state.fieldEvent.type,'goal');
  assert.equal(state.ball.owner,1);assert.equal(state.ball.x,640);assert.equal(state.ball.y,313.5);
 }
 const samples=await Promise.all([p.evaluate(()=>window.__goalSamples),q.evaluate(()=>window.__goalSamples)]);
 const shared=Object.keys(samples[0]).filter(t=>samples[1][t]&&samples[0][t].score[0]===1).map(Number).sort((x,y)=>x-y);
 assert.ok(shared.length>0,'both clients recorded a shared goal tick');
 for(const tick of shared){assert.deepEqual(samples[0][tick].ball,samples[1][tick].ball);assert.deepEqual(samples[0][tick].score,samples[1][tick].score);}
 await q.waitForFunction(t=>window.__onlineTestState?.tick>=t+65,start,{timeout:10000});
 await q.keyboard.press('KeyX');await q.keyboard.up('ArrowLeft');
 for(const page of [p,q])await page.waitForFunction(()=>window.__onlineTestState?.ball.owner===null&&window.__onlineTestState?.ball.passRolling,{timeout:10000});
 assert.deepEqual(errors,[]);
 console.log(`OK: synchronized goal, stable kickoff and resumed play across ${shared.length} shared ticks`);
}finally{
 for(const context of contexts)await context.close();if(browser)await browser.close();
 for(const ws of lobby.clients)ws.terminate();await new Promise(r=>lobby.close(r));await new Promise(r=>server.close(r));
}
