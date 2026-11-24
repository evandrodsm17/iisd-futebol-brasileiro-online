import {chromium} from 'playwright';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {createGameServer} from '../server/app.mjs';

const reference=readFileSync(new URL('../dist/assets/issd/slide-lab-local/goalkeeper-throw-sheet.png',import.meta.url));
const audit=JSON.parse(readFileSync(new URL('../docs/issd-goalkeeper-throw-sequence-audit.json',import.meta.url),'utf8'));
assert.equal(createHash('sha256').update(reference).digest('hex'),audit.sheet_sha256,'local reference must be the validated captured sheet');
const server=await createGameServer({root:'dist'});await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
const chrome=process.env.PLAYWRIGHT_CHROME_PATH||(process.platform==='win32'?'C:/Program Files/Google/Chrome/Application/chrome.exe':undefined);
let browser;
try{
 browser=await chromium.launch({headless:true,...(chrome?{executablePath:chrome}:{})});
 const page=await browser.newPage(),errors=[];page.on('pageerror',error=>errors.push(error.message));
 const url=`http://127.0.0.1:${server.address().port}/editor/locomotion-lab.html`;
 await page.goto(url);await page.waitForFunction(()=>!document.querySelector('#keeper-throw-palette').disabled&&!document.querySelector('#keeper-throw-play').disabled);
 await page.locator('#keeper-throw-play').click();
 const slider=page.locator('#keeper-throw-tick');
 for(const [index,tick] of [[0,0],[1,1],[2,3],[3,5],[4,8]]){
  await slider.fill(String(tick));
  const difference=await page.evaluate(async index=>{
   const canvas=document.querySelector('#keeper-throw-sequence'),actual=canvas.getContext('2d').getImageData(0,0,96,96).data;
   const image=new Image();image.src='../assets/issd/slide-lab-local/goalkeeper-throw-sheet.png';await image.decode();
   const reference=document.createElement('canvas');reference.width=reference.height=96;const context=reference.getContext('2d');context.drawImage(image,index*96,0,96,96,0,0,96,96);
   const expected=context.getImageData(0,0,96,96).data;let count=0;for(let i=0;i<actual.length;i++)if(actual[i]!==expected[i])count++;return count;
  },index);
  assert.equal(difference,0,`frame ${index} matches the validated local reference`);
 }
 const original=await page.locator('#keeper-throw-sequence').evaluate(canvas=>canvas.toDataURL());
 await page.locator('#keeper-throw-palette').selectOption('0');
 assert.match(await page.locator('#keeper-throw-sequence-status').innerText(),/Paleta experimental/);
 const teamSkin0=await page.locator('#keeper-throw-sequence').evaluate(canvas=>canvas.toDataURL());assert.notEqual(teamSkin0,original);
 await page.locator('#keeper-throw-skin').selectOption('1');assert.notEqual(await page.locator('#keeper-throw-sequence').evaluate(canvas=>canvas.toDataURL()),teamSkin0);
 await page.locator('#keeper-throw-direction').selectOption('7');assert.equal(await page.locator('#keeper-throw-palette').isDisabled(),true);
 await page.locator('#keeper-throw-direction').selectOption('0');await page.waitForFunction(()=>!document.querySelector('#keeper-throw-play').disabled);assert.match(await page.locator('#keeper-throw-sequence-status').innerText(),/Paleta experimental/);
 assert.deepEqual(errors,[]);
 const missing=await browser.newPage();await missing.route('**/native-keeper-throw-local.json',route=>route.fulfill({status:404,body:''}));await missing.goto(url);
 await missing.waitForFunction(()=>!document.querySelector('#keeper-throw-play').disabled);assert.equal(await missing.locator('#keeper-throw-palette').isDisabled(),true);
 console.log('OK: five dynamic goalkeeper frames match the captured sheet; palette fallback works');
}finally{if(browser)await browser.close();await new Promise(resolve=>server.close(resolve));}
