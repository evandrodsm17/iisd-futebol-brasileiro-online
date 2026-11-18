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
 assert.equal((await p.evaluate(()=>window.__onlineTestState)).ball.owner,0,'host begins with possession');
 await q.keyboard.down('ArrowUp');await q.waitForTimeout(900);await q.keyboard.up('ArrowUp');
 for(const page of [p,q])await page.evaluate(()=>{
  window.__shotSamples={};window.__shotSampler=setInterval(()=>{const s=window.__onlineTestState;
   if(s)window.__shotSamples[s.tick]=structuredClone(s.ball);},5);
 });
 await p.keyboard.down('KeyE');await p.keyboard.press('KeyA');await p.waitForTimeout(120);await p.keyboard.up('KeyE');
 for(const page of [p,q])await page.waitForFunction(()=>Object.values(window.__shotSamples).some(b=>b.owner===null&&b.z<0),{timeout:10000});
 await p.waitForTimeout(400);
 const snapshots=[];
 for(const page of [p,q])snapshots.push(await page.evaluate(()=>{clearInterval(window.__shotSampler);return window.__shotSamples;}));
 const ticks=Object.keys(snapshots[0]).filter(t=>snapshots[1][t]&&snapshots[0][t].owner===null&&snapshots[0][t].z<0);
 assert.ok(ticks.length>0,'both clients observed the same airborne simulation tick');
 for(const tick of ticks)assert.deepEqual(snapshots[0][tick],snapshots[1][tick],`shot state agrees at tick ${tick}`);
 await p.waitForFunction(()=>window.__onlineTestState?.keeperSave?.team===1,{timeout:12000});
 await q.waitForFunction(()=>window.__onlineTestState?.keeperSave?.team===1,{timeout:12000});
 const saveA=await p.evaluate(()=>window.__onlineTestState.keeperSave),saveB=await q.evaluate(()=>window.__onlineTestState.keeperSave);
 assert.deepEqual(saveA,saveB,'goalkeeper save is synchronized');
 assert.equal(saveA.kind,'catch','the tested low-speed arrival is caught');
 for(const page of [p,q])await page.waitForFunction(()=>{
  const s=window.__onlineTestState,k=s?.keepers.find(x=>x.team===1),p=s?.players.find(x=>x.team===1);
  return s?.ball.owner===1&&k&&p&&k.x===p.x&&k.y===p.y;
 },{timeout:10000});
 await q.keyboard.down('ArrowLeft');await q.keyboard.press('KeyX');await q.waitForTimeout(120);await q.keyboard.up('ArrowLeft');
 for(const page of [p,q])await page.waitForFunction(()=>window.__onlineTestState?.ball.owner===null&&window.__onlineTestState?.ball.passRolling,{timeout:10000});
 assert.deepEqual(errors,[]);
 console.log(`OK: online shot synchronized across ${ticks.length} shared ticks; goalkeeper catch and release synchronized`);
}finally{
 for(const context of contexts)await context.close();if(browser)await browser.close();
 for(const ws of lobby.clients)ws.terminate();await new Promise(r=>lobby.close(r));await new Promise(r=>server.close(r));
}
