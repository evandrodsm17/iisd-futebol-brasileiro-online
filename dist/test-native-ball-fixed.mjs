import assert from 'node:assert/strict';
import {advanceNativeBallAxis} from './native-ball-fixed.mjs';

// Independent emulator observations: 0, 7 and 1 after goalkeeper throws.
const cases = [
  {p:[[137,43918],[121,29958]],v:[[4,61922],[0,0]],shift:[65531,0],expected:[[137,40304],[121,29958]]},
  {p:[[92,46897],[121,29958]],v:[[2,43786],[65533,21750]],shift:[0,2],expected:[[95,25147],[120,51708]]},
  {p:[[100,906],[123,41264]],v:[[5,18866],[2,11028]],shift:[65530,0],expected:[[99,19772],[125,52292]]}
];
for (const test of cases) for (const axis of [0,1]) {
  const [integer,fraction]=test.p[axis], [vi,vf]=test.v[axis];
  assert.deepEqual(advanceNativeBallAxis({integer,fraction},{integer:vi,fraction:vf},test.shift[axis]),
    {integer:test.expected[axis][0],fraction:test.expected[axis][1]});
}
assert.deepEqual(advanceNativeBallAxis({integer:65535,fraction:65535},{integer:0,fraction:1}),{integer:0,fraction:0});
assert.throws(()=>advanceNativeBallAxis({integer:1,fraction:-1},{integer:0,fraction:0}),RangeError);
console.log('OK: integração nativa 16.16 e translação reproduzem três capturas');
import {advanceNativeAirborneHeight} from './native-ball-fixed.mjs';
assert.deepEqual(advanceNativeAirborneHeight({integer:0,fraction:0},{integer:0,fraction:0},7168),{position:{integer:0,fraction:0},velocity:{integer:0,fraction:0}},'stationary ball does not acquire vertical acceleration');
assert.throws(()=>advanceNativeAirborneHeight({integer:0,fraction:0},{integer:0,fraction:0},-1),RangeError);
const airborne=advanceNativeAirborneHeight({integer:65503,fraction:0},{integer:65533,fraction:49152},7168);
assert.deepEqual(airborne,{position:{integer:65500,fraction:56320},velocity:{integer:65533,fraction:56320}});
assert.equal(advanceNativeAirborneHeight({integer:0,fraction:65535},{integer:0,fraction:1},0),null);
console.log('OK: ramo aéreo vertical reproduz a captura e não extrapola o contato com o solo');
import {observedType2Bounce} from './native-ball-fixed.mjs';
const bounceInput={ballType:2,weather:1,flags:0,parameter:11,impactVelocity:{integer:1,fraction:32768},velocityX:{integer:7,fraction:3328},velocityY:{integer:0,fraction:28672}};
assert.deepEqual(observedType2Bounce(bounceInput),{positionZ:{integer:0,fraction:0},velocityZ:{integer:65535,fraction:16384},velocityX:{integer:5,fraction:18880},velocityY:{integer:0,fraction:21504},parameter:7,flags:1});
assert.equal(observedType2Bounce({...bounceInput,weather:2}),null);
assert.equal(observedType2Bounce({...bounceInput,velocityX:{integer:65535,fraction:0}}),null);
console.log('OK: ramo de quique tipo 2 reproduz a captura e rejeita ramos não validados');
import {observedType3ShotBounce} from './native-ball-fixed.mjs';
const shotBounce={ballType:3,weather:1,flags:0,parameter:11,impactVelocity:{integer:7,fraction:0},velocityX:{integer:5,fraction:13052},velocityY:{integer:2,fraction:8704}};
assert.deepEqual(observedType3ShotBounce(shotBounce),{positionZ:{integer:0,fraction:0},velocityZ:{integer:65532,fraction:32768},velocityX:{integer:3,fraction:58941},velocityY:{integer:1,fraction:39296},parameter:7,flags:1});
assert.equal(observedType3ShotBounce({...shotBounce,weather:2}),null);
assert.equal(observedType3ShotBounce({...shotBounce,ballType:5}),null);
assert.equal(observedType3ShotBounce({...shotBounce,velocityX:{integer:5,fraction:13053}}),null);
console.log('OK: quique nativo observado de chute tipo 3 sem extrapolar outras trajetórias');
import {observedType5ShotBounce} from './native-ball-fixed.mjs';
const type5Bounce={ballType:5,weather:1,flags:0,parameter:5,impactVelocity:{integer:2,fraction:4096},velocityX:{integer:65528,fraction:12288},velocityY:{integer:65535,fraction:47616}};
assert.deepEqual(observedType5ShotBounce(type5Bounce),{positionZ:{integer:0,fraction:0},velocityZ:{integer:65534,fraction:12800},velocityX:{integer:65529,fraction:10752},velocityY:{integer:65535,fraction:49856},parameter:3,flags:1});
assert.equal(observedType5ShotBounce({...type5Bounce,flags:1}),null);
assert.equal(observedType5ShotBounce({...type5Bounce,impactVelocity:{integer:2,fraction:4097}}),null);
console.log('OK: quique nativo observado de chute tipo 5 sem extrapolar outras trajetórias');
