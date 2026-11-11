import assert from 'node:assert/strict';
import { DEFAULT_BINDINGS, loadBindings, saveBindings, validBindings } from './control-bindings.mjs';
const legacy={up:'KeyW',down:'KeyS',left:'KeyA',right:'KeyD',run:'ShiftLeft',shot:'Space',pass:'KeyX',press:'KeyF',switch:'KeyQ',reset:'KeyR'};
function storage(data={}) { const values=new Map(Object.entries(data));return {getItem:key=>values.get(key)??null,setItem:(key,value)=>values.set(key,value)}; }
assert.deepEqual(loadBindings(storage()),DEFAULT_BINDINGS);
assert.deepEqual(loadBindings(storage({'issd-web-controls-v1':JSON.stringify(legacy)})),DEFAULT_BINDINGS);
const custom={...legacy,shot:'KeyZ'};
const store=storage({'issd-web-controls-v1':JSON.stringify(custom)});
const migrated=loadBindings(store);
assert.equal(migrated.shot,'KeyZ');assert.equal(migrated.up,'KeyW');assert.equal(migrated.right,'KeyD');assert.ok(validBindings(migrated));
assert.ok(saveBindings(migrated,store));assert.deepEqual(loadBindings(store),migrated);
console.log('OK: novos controles e migracao das configuracoes existentes');
