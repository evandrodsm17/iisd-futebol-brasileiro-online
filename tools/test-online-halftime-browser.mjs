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
  page.on('pageerror',e=>errors.push(e.message));await page.route('**/game.js*',async route=>{const response=await route.fetch();const source=await response.text();const patched=source.replace('matchClockBcd = clockInitialBcdByGameTime[setting] ?? clockInitialBcdByGameTime[1];','matchClockBcd = 0x0001;');assert.notEqual(patched,source);await route.fulfill({response,body:patched});});await page.goto(url);
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

 for(const page of [p,q])await page.waitForFunction(()=>window.__onlineTestState?.period===1,{timeout:10000});
 const states=await Promise.all([p.evaluate(()=>window.__onlineTestState),q.evaluate(()=>window.__onlineTestState)]);
 for(const state of states){
  assert.equal(state.teamsSwapped,true);assert.deepEqual(state.score,[0,0]);
  assert.equal(state.ball.owner,1);assert.equal(state.ball.x,640);assert.equal(state.ball.y,313.5);
  assert.ok(state.keepers.find(k=>k.team===0).x>640);
  assert.ok(state.keepers.find(k=>k.team===1).x<640);
 }
 assert.deepEqual(states[0].squad,states[1].squad);assert.deepEqual(errors,[]);
 console.log('OK: accelerated halftime swaps sides and starts team 1 in both browsers');
}finally{
 for(const context of contexts)await context.close();if(browser)await browser.close();
 for(const ws of lobby.clients)ws.terminate();await new Promise(r=>lobby.close(r));await new Promise(r=>server.close(r));
}

