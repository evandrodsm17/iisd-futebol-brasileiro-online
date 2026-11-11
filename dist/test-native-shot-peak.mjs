import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {advanceNativeAirborneHeight} from './native-ball-fixed.mjs';
const report=JSON.parse(readFileSync(new URL('../docs/issd-natural-shot-peak.json',import.meta.url),'utf8'));
const split=value=>({integer:Math.floor(value/65536),fraction:value%65536});
assert.equal(report.updates.length,64);
for(const row of report.updates){
 const actual=advanceNativeAirborneHeight(split(row.position_before_raw),split(row.velocity_before_raw),row.gravity);
 assert.deepEqual(actual,{position:split(row.position_after_raw),velocity:split(row.velocity_after_raw)},`frame ${row.frame}`);
}
assert.equal(report.native_peak_height,220.5);
console.log('OK: 64 atualizações fixas da subida coincidem com o replay nativo');
