import assert from 'node:assert/strict';
import {X_NATIVE_PER_WORLD,Y_NATIVE_PER_WORLD} from '../dist/ball-contact.mjs';
import { fieldDimensions, resizeField, nativeDimensions } from '../dist/native-field.mjs';
assert.deepEqual(fieldDimensions(1), {w:1150,h:523});
assert.equal(fieldDimensions(3).w / 1150, 2048 / 1856);
assert.throws(() => fieldDimensions(8), RangeError);
const field = {x:65,y:52,w:1150,h:523};
const entity = {x:640,y:313.5,homeX:65,homeY:52};
resizeField(field, 7, [entity]);
assert.equal(entity.x, field.x + field.w / 2);
assert.equal(entity.y, field.y + field.h / 2);
resizeField(field, 1, [entity]);
assert.ok(Math.abs(entity.x-640)<1e-9);
assert.ok(Math.abs(entity.y-313.5)<1e-9);
assert.equal(entity.homeX,65);
assert.equal(entity.homeY,52);
console.log('Native field: dimension and coordinate preservation checks passed');

// Internal consistency only: the existing Canvas mapping is provisional.
for(let id=0;id<nativeDimensions.length;id++){
 const size=fieldDimensions(id),[nativeWidth,nativeHeight]=nativeDimensions[id];
 assert.ok(Math.abs(size.w*X_NATIVE_PER_WORLD-nativeWidth)<1e-9);
 assert.ok(Math.abs(size.h*Y_NATIVE_PER_WORLD-nativeHeight)<1e-9);
}
console.log('Native field: provisional contact scale agrees with all eight stadium dimensions');
