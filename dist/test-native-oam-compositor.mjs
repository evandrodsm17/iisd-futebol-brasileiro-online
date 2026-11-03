import assert from 'node:assert/strict';
import {readFileSync,existsSync} from 'node:fs';
import {join} from 'node:path';
import {decodeOamParts,composeOam} from './native-oam-compositor.mjs';

const oam=new Uint8Array(544),vram=new Uint8Array(65536),cgram=new Uint8Array(512);
// Two overlapping sprites: lower slot wins even when its priority differs.
oam.set([1,2,0,0x30],0);oam.set([1,2,1,0],4);
vram[0]=0x80;vram[32+1]=0x80;cgram[(128+1)*2]=31;cgram[(128+2)*2+1]=0x7c;
let parts=decodeOamParts(oam,0,[1,0]);let result=composeOam({oam,vram,cgram,obsel:0,parts,width:16,height:16});
assert.deepEqual([...result.rgba.slice((2*16+1)*4,(2*16+1)*4+4)],[255,0,0,255]);
assert.throws(()=>decodeOamParts(oam,0,[0,0]));
assert.throws(()=>composeOam({vram,cgram,obsel:0,parts:[{...parts[0],size:12}]}));

const fixtureRoot=new URL('../analysis/oam-compositor-fixtures/',import.meta.url);
if(existsSync(new URL('manifest.json',fixtureRoot))){
 const manifest=JSON.parse(readFileSync(new URL('manifest.json',fixtureRoot),'utf8'));
 assert.equal(manifest.schema,'issd-oam-fixtures-local/v1');assert.ok(manifest.frames.length>=10);
 for(const f of manifest.frames){
  const read=suffix=>new Uint8Array(readFileSync(join(manifest.capture,`${f.prefix}-${suffix}.bin`)));
  const capturedOam=read('oam');parts=decodeOamParts(capturedOam,f.obsel,f.slots);
  result=composeOam({vram:read('vram'),cgram:read('cgram'),obsel:f.obsel,parts});
  assert.deepEqual(Buffer.from(result.rgba),readFileSync(new URL(f.expected,fixtureRoot)),`frame ${f.step}`);
 }
 console.log(`OK: ${manifest.frames.length} quadros da captura coincidem pixel a pixel`);
}else console.log('OK: casos sintéticos; captura local não disponível');
