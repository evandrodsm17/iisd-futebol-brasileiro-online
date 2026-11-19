import {chromium} from 'playwright';import assert from 'node:assert/strict';import {createGameServer} from '../server/app.mjs';
const server=await createGameServer({root:'dist'});await new Promise(r=>server.listen(0,'127.0.0.1',r));
const chrome=process.env.PLAYWRIGHT_CHROME_PATH||(process.platform==='win32'?'C:/Program Files/Google/Chrome/Application/chrome.exe':undefined);let browser;
try{
 browser=await chromium.launch({headless:true,...(chrome?{executablePath:chrome}:{})});const page=await browser.newPage(),errors=[];page.on('pageerror',e=>errors.push(e.message));const url=`http://127.0.0.1:${server.address().port}/editor/locomotion-lab.html`;
 await page.goto(url);await page.waitForFunction(()=>!document.querySelector('#penalty-free-flight-shoot').disabled);
 const select=page.locator('#penalty-free-flight-direction'),status=page.locator('#penalty-free-flight-status'),canvas=page.locator('#penalty-free-flight-canvas');
 const pixels=()=>canvas.evaluate(c=>c.toDataURL());
 await select.selectOption('left');await page.locator('#penalty-free-flight-shoot').click();await page.waitForFunction(()=>document.querySelector('#penalty-free-flight-status').textContent.includes('Ponto de verificação'));assert.match(await status.innerText(),/não são calculados/);const left=await pixels();
 await select.selectOption('right');await page.locator('#penalty-free-flight-shoot').click();await page.waitForFunction(()=>document.querySelector('#penalty-free-flight-status').textContent.includes('Ponto de verificação'));const right=await pixels();assert.notEqual(left,right);
 await canvas.focus();await page.keyboard.down('ArrowUp');await page.keyboard.down('ArrowLeft');assert.equal(await select.inputValue(),'upLeft');await page.keyboard.press('KeyA');await page.keyboard.up('ArrowLeft');await page.keyboard.up('ArrowUp');await page.waitForFunction(()=>document.querySelector('#penalty-free-flight-status').textContent.includes('Ponto de verificação'));
 assert.deepEqual(errors,[]);const missing=await browser.newPage();await missing.route('**/penalty-shot-vectors-local.json',route=>route.fulfill({status:404,body:''}));await missing.goto(url);await missing.waitForFunction(()=>document.querySelector('#penalty-free-flight-status').textContent.includes('indisponíveis'));assert.equal(await missing.locator('#penalty-free-flight-shoot').isDisabled(),true);
 console.log('OK: interactive penalty flight preview, keyboard and missing tables');
}finally{if(browser)await browser.close();await new Promise(r=>server.close(r));}
