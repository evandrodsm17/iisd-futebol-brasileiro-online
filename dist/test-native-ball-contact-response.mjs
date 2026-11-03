import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { nativeType2Response } from './native-ball-contact-response.mjs';

const report = JSON.parse(readFileSync(new URL('../docs/issd-ball-contact-route-observation.json', import.meta.url)));
const entry = report.events.find(e => e.address === '84BAB7');
const target = report.events.find(e => e.address === '85F8BF');
const base = {ballType:entry.ball_type,ballAge:entry.ball_age,actorTeam:entry.actor_team,
  referenceTeam:entry.ref_c8_team,actorFlags:entry.actor_field60,direction:1,randomWord:0};
const result = nativeType2Response(base);
assert.deepEqual(result, {route:'85:F088',ballType:1,angle:target.a,parameter:target.y});
assert.equal(target.x, result.ballType);
assert.equal(nativeType2Response({...base,ballAge:10}).route, 'other');
assert.equal(nativeType2Response({...base,ballType:1}).route, 'other');
assert.equal(nativeType2Response({...base,referenceTeam:base.actorTeam}).route, 'other');
assert.equal(nativeType2Response({...base,actorFlags:0}).route, 'unresolved');
assert.equal(nativeType2Response({...base,direction:7,randomWord:3}).angle, 0x38);
assert.equal(nativeType2Response({...base,direction:7,randomWord:3}).parameter, 4);
assert.throws(() => nativeType2Response({...base,direction:8}), RangeError);
console.log('OK: ramo nativo de contato tipo 2 e parâmetros do replay');
