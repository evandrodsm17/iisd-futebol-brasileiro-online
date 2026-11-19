import {chromium} from 'playwright';import assert from 'node:assert/strict';import {createGameServer} from '../server/app.mjs';
const server=await createGameServer({root:'dist'});await new Promise(r=>server.listen(0,'127.0.0.1',r));
const chrome=process.env.PLAYWRIGHT_CHROME_PATH||(process.platform==='win32'?'C:/Program Files/Google/Chrome/Application/chrome.exe':undefined);let browser;
try{
 browser=await chromium.launch({headless:true,...(chrome?{executablePath:chrome}:{})});const page=await browser.newPage(),errors=[];page.on('pageerror',e=>errors.push(e.message));
 const url=`http://127.0.0.1:${server.address().port}/editor/locomotion-lab.html`;
 await page.goto(url);await page.waitForFunction(()=>!document.querySelector('#penalty-synthetic-keeper-play').disabled);
 const slider=page.locator('#penalty-synthetic-keeper-frame'),direction=page.locator('#penalty-synthetic-keeper-direction'),status=page.locator('#penalty-synthetic-keeper-status');
 const pixels=()=>page.locator('#penalty-synthetic-keeper').evaluate(canvas=>{const data=canvas.getContext('2d').getImageData(0,0,canvas.width,canvas.height).data;let count=0;for(let i=3;i<data.length;i+=4)if(data[i])count++;return count;});
 for(const dir of ['Left','Right']){
  await direction.selectOption(dir);await slider.fill('1');assert.match(await status.innerText(),/sem associação validada/);assert.equal(await pixels(),0);
  for(const frame of ['2','10','20','40']){await slider.fill(frame);assert.match(await status.innerText(),/Quadro validado/);assert.ok(await pixels()>50);}
 }
 await page.locator('#penalty-synthetic-keeper-play').click();await page.waitForFunction(()=>document.querySelector('#penalty-synthetic-keeper-frame').value==='40');assert.deepEqual(errors,[]);
 const missing=await browser.newPage();await missing.route('**/penalty-keeper-synthetic-local.json',route=>route.fulfill({status:404,body:''}));await missing.goto(url);
 await missing.waitForFunction(()=>document.querySelector('#penalty-synthetic-keeper-status').textContent.includes('indisponíveis'));assert.equal(await missing.locator('#penalty-synthetic-keeper-play').isDisabled(),true);
 console.log('OK: synthetic keeper captures, missing frames and playback');
}finally{if(browser)await browser.close();await new Promise(r=>server.close(r));}
