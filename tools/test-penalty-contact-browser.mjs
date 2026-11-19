import {chromium} from 'playwright';import assert from 'node:assert/strict';import {createGameServer} from '../server/app.mjs';
const server=await createGameServer({root:'dist'});await new Promise(r=>server.listen(0,'127.0.0.1',r));
const chrome=process.env.PLAYWRIGHT_CHROME_PATH||(process.platform==='win32'?'C:/Program Files/Google/Chrome/Application/chrome.exe':undefined);let browser;
try{
 browser=await chromium.launch({headless:true,...(chrome?{executablePath:chrome}:{})});const page=await browser.newPage(),errors=[];page.on('pageerror',e=>errors.push(e.message));const url=`http://127.0.0.1:${server.address().port}/editor/locomotion-lab.html`;
 await page.goto(url);await page.waitForFunction(()=>!document.querySelector('#penalty-contact-shot').disabled);
 const shot=page.locator('#penalty-contact-shot'),keeper=page.locator('#penalty-contact-keeper'),status=page.locator('#penalty-contact-status');
 for(const s of ['left','neutral','right'])for(const k of ['left','neutral','right']){
  await shot.selectOption(s);await keeper.selectOption(k);
  if(s===k){assert.match(await status.innerText(),/Contato selecionado.*conferida/);assert.match(await status.innerText(),/1 × 0 → 1 × 0/);}
  else{assert.match(await status.innerText(),/ramo de gol/);assert.match(await status.innerText(),/1 × 0 → 2 × 0/);}
 }
 assert.deepEqual(errors,[]);
 const missing=await browser.newPage();await missing.route('**/penalty-hitbox-tables-local.json',route=>route.fulfill({status:404,body:''}));await missing.goto(url);await missing.waitForFunction(()=>!document.querySelector('#penalty-contact-shot').disabled);assert.match(await missing.locator('#penalty-contact-status').innerText(),/Tabelas locais indisponíveis/);
 console.log('OK: nine captured contact comparisons and missing local tables');
}finally{if(browser)await browser.close();await new Promise(r=>server.close(r));}
