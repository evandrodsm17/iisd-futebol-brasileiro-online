import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createNativeJumpBody} from '../dist/native-jump-body.mjs';
import {createJumpCapture} from '../dist/editor/jump-lab.mjs';
const read=p=>JSON.parse(readFileSync(p,'utf8')),root='dist/';
const data=read(root+'assets/issd/slide-lab-local/jump-directions.json'),preview=read(root+'assets/issd/editor-preview-local.json'),detail=read(root+'data/issd-team-detail-colors.json'),catalog=read(root+'data/issd-rom-catalog.json');
const make=(w,h)=>{const c={};c.getContext=()=>c;c.createImageData=()=>({data:new Uint8ClampedArray(w*h*4)});c.putImageData=im=>{c.pixels=im.data};return c;};
const renderer=createNativeJumpBody(data,preview,detail,make);
for(const [direction,file] of [[6,'jump.json'],[0,'jump-up.json'],[1,'jump-upright.json'],[2,'jump-right.json'],[3,'jump-downright.json'],[5,'jump-downleft.json'],[7,'jump-upleft.json'],[4,'jump-down.json']]){
 const original=createJumpCapture(read(root+'assets/issd/slide-lab-local/'+file),make),req={team:2,kit:'home',skin:0,shirtNumber:10,screenDirection:direction,palette:catalog.teams[2].kit.home.sprite_palette};
 assert.ok(renderer.supports(req));for(let tick=0;tick<23;tick++)assert.deepEqual(renderer.frame(tick,req).pixels,original.frame(tick).pixels,`direction ${direction} tick ${tick}`);
}
let count=0;for(let team=0;team<36;team++)for(const kit of ['home','away'])for(let skin=0;skin<2;skin++)for(let shirtNumber=1;shirtNumber<=20;shirtNumber++)for(const screenDirection of [0,1,2,3,4,5,6,7]){const req={team,kit,skin,shirtNumber,screenDirection,palette:catalog.teams[team].kit[kit].sprite_palette};assert.ok(renderer.supports(req),JSON.stringify({team,kit,skin,shirtNumber,screenDirection}));count++;}
assert.equal(renderer.supports({team:2,kit:'home',skin:0,shirtNumber:10,screenDirection:8,palette:catalog.teams[2].kit.home.sprite_palette}),false);
console.log(`OK: 184 reference frames exact; ${count} team, kit, skin, shirt and direction contexts supported`);
