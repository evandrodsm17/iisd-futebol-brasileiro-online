import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {nativeReceiptHeightBranch} from './native-throwin-receipt.mjs';

test('distinguishes the captured native contact paths',()=>{
 const evidence=JSON.parse(readFileSync(new URL('../docs/issd-throwin-contact-chain.json',import.meta.url),'utf8'));
 for(const item of evidence.cases)assert.equal(nativeReceiptHeightBranch(item.ball_z_word),item.path.includes('84BB84')?'high':'low');
});
test('follows 16-bit CMP negative-flag boundaries',()=>{
 assert.equal(nativeReceiptHeightBranch(0xffef),'high');assert.equal(nativeReceiptHeightBranch(0xfff0),'low');
 assert.equal(nativeReceiptHeightBranch(0xffff),'low');assert.equal(nativeReceiptHeightBranch(0x0000),'low');
 assert.equal(nativeReceiptHeightBranch(0x7ff0),'high');
 for(const invalid of [-1,65536,1.5,NaN])assert.throws(()=>nativeReceiptHeightBranch(invalid),RangeError);
});
