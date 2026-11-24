import {chromium} from 'playwright';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {createGameServer} from '../server/app.mjs';

const audit=JSON.parse(readFileSync(new URL('../docs/issd-goalkeeper-throw-sequence-audit.json',import.meta.url),'utf8'));
const directed=JSON.parse(readFileSync(new URL('../docs/issd-goalkeeper-directed-throw-audit.json',import.meta.url),'utf8'));
for(const [name,expected] of [['sheet',audit.sheet_sha256],['7',directed.directions['7'].sheet_sha256],['1',directed.directions['1'].sheet_sha256]]){
 const reference=readFileSync(new URL(`../dist/assets/issd/slide-lab-local/goalkeeper-throw-${name}.png`,import.meta.url));
 assert.equal(createHash('sha256').update(reference).digest('hex'),expected,`${name} reference must be the validated captured sheet`);
}
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
 for(const [orientation,name,ticks] of [['0','sheet',[0,1,3,5,8]],['7','7',[0,2,4,6,8]],['1','1',[0,2,4,6,9]]]){
  await page.locator('#keeper-throw-direction').selectOption(orientation);await page.waitForFunction(()=>!document.querySelector('#keeper-throw-play').disabled);
  assert.equal(await page.locator('#keeper-throw-palette').isDisabled(),false);
  for(const [index,tick] of ticks.entries()){
   await slider.fill(String(tick));
   const difference=await page.evaluate(async ({index,name})=>{
   const canvas=document.querySelector('#keeper-throw-sequence'),actual=canvas.getContext('2d').getImageData(0,0,96,96).data;
   const image=new Image();image.src=`../assets/issd/slide-lab-local/goalkeeper-throw-${name}.png`;await image.decode();
   const reference=document.createElement('canvas');reference.width=reference.height=96;const context=reference.getContext('2d');context.drawImage(image,index*96,0,96,96,0,0,96,96);
   const expected=context.getImageData(0,0,96,96).data;let count=0;for(let i=0;i<actual.length;i++)if(actual[i]!==expected[i])count++;return count;
   },{index,name});
   assert.equal(difference,0,`orientation ${orientation}, frame ${index} matches the validated local reference`);
  }
 }
 await page.locator('#keeper-throw-direction').selectOption('0');await page.waitForFunction(()=>!document.querySelector('#keeper-throw-play').disabled);await slider.fill('8');
 const original=await page.locator('#keeper-throw-sequence').evaluate(canvas=>canvas.toDataURL());
 await page.locator('#keeper-throw-palette').selectOption('0');
 assert.match(await page.locator('#keeper-throw-sequence-status').innerText(),/Paleta experimental/);
 const teamSkin0=await page.locator('#keeper-throw-sequence').evaluate(canvas=>canvas.toDataURL());assert.notEqual(teamSkin0,original);
 await page.locator('#keeper-throw-skin').selectOption('1');assert.notEqual(await page.locator('#keeper-throw-sequence').evaluate(canvas=>canvas.toDataURL()),teamSkin0);
 await page.locator('#keeper-throw-direction').selectOption('7');await page.waitForFunction(()=>!document.querySelector('#keeper-throw-play').disabled);assert.equal(await page.locator('#keeper-throw-palette').isDisabled(),false);assert.match(await page.locator('#keeper-throw-sequence-status').innerText(),/Paleta experimental/);
 assert.deepEqual(errors,[]);
 const missing=await browser.newPage();await missing.route('**/native-keeper-throw-local.json',route=>route.fulfill({status:404,body:''}));await missing.goto(url);
 await missing.waitForFunction(()=>!document.querySelector('#keeper-throw-play').disabled);assert.equal(await missing.locator('#keeper-throw-palette').isDisabled(),true);
 const runtime=JSON.parse(readFileSync(new URL('../dist/assets/issd/native-keeper-throw-local.json',import.meta.url),'utf8'));
 const legacy={schema:'issd-keeper-throw-runtime-local/v1',width:runtime.width,height:runtime.height,palette:runtime.palette,...runtime.cycles['0']};
 const old=await browser.newPage();await old.route('**/native-keeper-throw-local.json',route=>route.fulfill({json:legacy}));await old.goto(url);await old.waitForFunction(()=>!document.querySelector('#keeper-throw-palette').disabled);
 await old.locator('#keeper-throw-direction').selectOption('7');assert.equal(await old.locator('#keeper-throw-palette').isDisabled(),true);
 console.log('OK: fifteen dynamic goalkeeper frames match the captured sheets; missing and legacy data fallbacks work');
}finally{if(browser)await browser.close();await new Promise(resolve=>server.close(resolve));}
