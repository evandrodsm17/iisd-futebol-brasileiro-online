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
 await shot.selectOption('left');await keeper.selectOption('left');
 const slider=page.locator('#penalty-contact-check'),detail=page.locator('#penalty-contact-check-status');
 assert.equal(await slider.isDisabled(),false);assert.match(await detail.innerText(),/sem contato.*conferida.*goleiro na posição inicial confirmada/);
 const diagram=page.locator('#penalty-contact-diagram');const initial=await diagram.evaluate(canvas=>canvas.toDataURL());
 await slider.fill(await slider.getAttribute('max'));assert.match(await detail.innerText(),/contato na área.*conferida.*goleiro calculado/);assert.notEqual(await diagram.evaluate(canvas=>canvas.toDataURL()),initial);
 const play=page.locator('#penalty-contact-play');await play.click();await page.waitForFunction(()=>{const slider=document.querySelector('#penalty-contact-check');return slider.value===slider.max&&document.querySelector('#penalty-contact-play').textContent==='Reproduzir sequência';});assert.match(await detail.innerText(),/contato na área/);
 await slider.fill('1');await play.click();await keeper.selectOption('neutral');await slider.fill(await slider.getAttribute('max'));assert.match(await detail.innerText(),/sem contato.*goleiro calculado/);
 await keeper.selectOption('right');assert.equal(await slider.isDisabled(),true);assert.equal(await play.isDisabled(),true);assert.match(await detail.innerText(),/não capturada/);
 assert.deepEqual(errors,[]);
 const missing=await browser.newPage();await missing.route('**/penalty-hitbox-tables-local.json',route=>route.fulfill({status:404,body:''}));await missing.goto(url);await missing.waitForFunction(()=>!document.querySelector('#penalty-contact-shot').disabled);assert.match(await missing.locator('#penalty-contact-status').innerText(),/Tabelas locais indisponíveis/);assert.match(await missing.locator('#penalty-contact-check-status').innerText(),/tabelas locais indisponíveis/);
 const noMotion=await browser.newPage();await noMotion.route('**/issd-penalty-keeper-motion.json',route=>route.fulfill({status:404,body:''}));await noMotion.goto(url);await noMotion.waitForFunction(()=>!document.querySelector('#penalty-contact-shot').disabled);const fallbackSlider=noMotion.locator('#penalty-contact-check');await fallbackSlider.fill(await fallbackSlider.getAttribute('max'));assert.match(await noMotion.locator('#penalty-contact-check-status').innerText(),/goleiro com posição registrada/);
 console.log('OK: nine captured contact comparisons and missing local tables');
}finally{if(browser)await browser.close();await new Promise(r=>server.close(r));}
