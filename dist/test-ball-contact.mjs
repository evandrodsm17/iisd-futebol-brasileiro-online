import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { nativeCommonContact, browserContact, closestContactPlayer, pickupPlayer, collectAirborneThrow } from './ball-contact.mjs';

const replay = JSON.parse(readFileSync(new URL('../docs/issd-ball-contact-geometry-observation.json', import.meta.url)));
let checked = 0;
for (const result of replay.results) {
  const e = result.entry;
  if (!e.actor_68 || e.actor_3e || (e.global_11fa & 0x8000)) continue;
  assert.equal(nativeCommonContact({x:e.actor_x,y:e.actor_y,z:e.actor_z},
    {x:e.x_pos,y:e.y_pos,z:e.z_pos}), result.carry === 0);
  checked++;
}
assert.ok(checked >= 25, 'Expected observed common-branch returns');
assert.equal(nativeCommonContact({x:158,y:119,z:0},{x:160,y:121,z:0xfff9}),true);
assert.equal(nativeCommonContact({x:158,y:119,z:0},{x:160,y:121,z:0xffe8}),false);
assert.equal(browserContact({x:100,y:100},{x:100,y:100,z:0}),true);
assert.equal(browserContact({x:100,y:100},{x:10000,y:100,z:0}),false);
assert.equal(browserContact({x:100,y:100},{x:100,y:100,z:-100}),false);
const invalidNearest={x:100,y:107}, eligible={x:107.2,y:100}, ball={x:100,y:100,z:0};
assert.equal(browserContact(invalidNearest,ball),false);
assert.equal(browserContact(eligible,ball),true);
assert.equal(closestContactPlayer([invalidNearest,eligible],ball),eligible);
assert.equal(closestContactPlayer([],ball),null);
const sender={x:100,y:100,team:0}, opponent={x:102,y:100,team:1};
assert.equal(pickupPlayer([sender,opponent],ball,0,0),opponent);
assert.equal(pickupPlayer([sender],ball,0,260),null);
assert.equal(pickupPlayer([sender],ball,0,261),sender);
assert.equal(pickupPlayer([sender],ball,0,Infinity),sender);
assert.equal(pickupPlayer([sender],ball,0,NaN),null);
console.log(`OK: contato nativo, adaptador provisório e ${checked} comparações com a ROM`);

// Throw-in observations: compare only geometry, without inferring how the ROM
// chooses the recipient or when possession is assigned.
const throwContacts=JSON.parse(readFileSync(new URL('../docs/issd-throwin-contact-audit.json',import.meta.url)));
assert.equal(throwContacts.cases.length,2);
for(const entry of throwContacts.cases){
  const [ax,ay,az]=entry.actor_xyz,[bx,by,bz]=entry.ball_xyz;
  assert.equal(nativeCommonContact({x:ax,y:ay,z:az},{x:bx,y:by,z:bz}),entry.contact_carry===0);
}
console.log('OK: contato geométrico coincide com dois laterais observados');

const aerialReceiver={team:1,x:100,y:100,vx:0,vy:0,facingDirection:2};
const aerialBall={x:100,y:100,z:-8,vx:1,vy:2,vz:1,owner:null,actionKind:'throw_in'};
assert.equal(collectAirborneThrow([aerialReceiver],aerialBall,0,0),aerialReceiver);
assert.equal(aerialBall.owner,aerialReceiver);assert.equal(aerialBall.z,0);assert.equal(aerialBall.actionKind,null);
const unrelated={x:100,y:100,z:-8,owner:null,actionKind:'shot'};
assert.equal(collectAirborneThrow([aerialReceiver],unrelated,0,1000),null);
console.log('OK: recepção aérea limitada à bola de lateral');

const teammate={team:0,x:100,y:100,vx:0,vy:0,facingDirection:2};
const tooSoon={x:100,y:100,z:-8,owner:null,actionKind:'throw_in'};
assert.equal(collectAirborneThrow([teammate],tooSoon,0,100),null,'same-team browser cooldown is preserved');
assert.equal(collectAirborneThrow([teammate],tooSoon,0,261),teammate,'eligible teammate may receive after cooldown');
const tooHigh={x:100,y:100,z:-100,owner:null,actionKind:'throw_in'};
assert.equal(collectAirborneThrow([aerialReceiver],tooHigh,0,1000),null,'high balls outside contact geometry are not collected');
