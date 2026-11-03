import assert from 'node:assert/strict';
import {readFileSync,existsSync} from 'node:fs';
import {join} from 'node:path';
import {decodeOamParts,composeOam,applyDescriptorRows,applyHairTile} from './native-oam-compositor.mjs';
import {buildDescriptorParts} from './native-descriptor-geometry.mjs';

const oam=new Uint8Array(544),vram=new Uint8Array(65536),cgram=new Uint8Array(512);
// Two overlapping sprites: lower slot wins even when its priority differs.
oam.set([1,2,0,0x30],0);oam.set([1,2,1,0],4);
vram[0]=0x80;vram[32+1]=0x80;cgram[(128+1)*2]=31;cgram[(128+2)*2+1]=0x7c;
let parts=decodeOamParts(oam,0,[1,0]);let result=composeOam({oam,vram,cgram,obsel:0,parts,width:16,height:16});
assert.deepEqual([...result.rgba.slice((2*16+1)*4,(2*16+1)*4+4)],[255,0,0,255]);
assert.throws(()=>decodeOamParts(oam,0,[0,0]));
assert.throws(()=>composeOam({vram,cgram,obsel:0,parts:[{...parts[0],size:12}]}));
const source=new Uint8Array(0x600).fill(7),original=new Uint8Array(65536).fill(3);
const applied=applyDescriptorRows(original,source,{obsel:3,baseTile:232,bank:0});
assert.equal(applied[(1536+232)*32],7);assert.equal(applied[(1536+255)*32],3);assert.equal(original[(1536+232)*32],3);
assert.equal(applyDescriptorRows(original,source,{obsel:3,baseTile:232,bank:0,detailValidated:true})[(1536+255)*32],7);

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

const bridgePath=new URL('./assets/issd/hair-lab-local/descriptor-bridge-demo-local.json',import.meta.url);
if(existsSync(bridgePath)){
 const bridge=JSON.parse(readFileSync(bridgePath,'utf8'));assert.equal(bridge.frames.length,10);
 const b64=value=>new Uint8Array(Buffer.from(value,'base64'));
 for(const f of bridge.frames){
  const v=b64(f.vram),c=b64(f.cgram),p=decodeOamParts(b64(f.oam),f.obsel,f.slots);
  assert.deepEqual(buildDescriptorParts(f),p,`geometria descritor ${f.descriptor}`);
  const before=composeOam({vram:v,cgram:c,obsel:f.obsel,parts:p});
  assert.equal(f.detail_validated,true);
  const replaced=applyDescriptorRows(v,b64(f.rows),{obsel:f.obsel,baseTile:f.base_tile,bank:f.bank,detailValidated:true});
  const after=composeOam({vram:replaced,cgram:c,obsel:f.obsel,parts:p});
  assert.deepEqual(after.rgba,before.rgba,`descritor ${f.descriptor}`);
 }
 console.log('OK: dez descritores recompõem as peças capturadas');
 const atlasPath=new URL('./assets/issd/hair-lab-local/hair-descriptor-tiles-local.json',import.meta.url);
 if(existsSync(atlasPath)){
  const atlas=JSON.parse(readFileSync(atlasPath,'utf8'));
  for(const style of [1,2,13])for(const f of bridge.frames){
   const folder=style===1?'bsnes-hair-detail-selector':`bsnes-hair-long-style${style}`;
   const root=new URL(`../analysis/${folder}/`,import.meta.url),name=`frame-${String(f.ppu_step).padStart(3,'0')}`;
   if(!existsSync(new URL(`${name}-vram.bin`,root)))continue;
   const expectedVram=new Uint8Array(readFileSync(new URL(`${name}-vram.bin`,root)));
   const capturedOam=new Uint8Array(readFileSync(new URL(`${name}-oam.bin`,root)));
   const capturedCgram=new Uint8Array(readFileSync(new URL(`${name}-cgram.bin`,root)));
   const parts=decodeOamParts(b64(f.oam),f.obsel,f.slots),expectedParts=decodeOamParts(capturedOam,f.obsel,f.slots);
   const tile=atlas.styles[String(style)],selector=tile.selectors[String(f.descriptor)];
   const body=applyDescriptorRows(b64(f.vram),b64(f.rows),{obsel:f.obsel,baseTile:f.base_tile,bank:f.bank,detailValidated:true});
   const reconstructed=applyHairTile(body,b64(tile.tiles[String(selector)]),{obsel:f.obsel,part:parts.find(p=>p.slot===f.hair_slot)});
   const actual=composeOam({vram:reconstructed,cgram:b64(f.cgram),obsel:f.obsel,parts});
   const expected=composeOam({vram:expectedVram,cgram:capturedCgram,obsel:f.obsel,parts:expectedParts});
   assert.deepEqual(actual.rgba,expected.rgba,`estilo ${style}, descritor ${f.descriptor}`);
  }
  console.log('OK: cabelo dos três estilos coincide com as capturas disponíveis');
 }
}
