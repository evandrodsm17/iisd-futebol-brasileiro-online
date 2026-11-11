import {composeOam} from './native-oam-compositor.mjs';
import {teamDetailColor} from './native-team-detail-color.mjs';
const decode=value=>Uint8Array.from(atob(value),c=>c.charCodeAt(0));
const directionToRom=[6,7,0,1,2,3,4,5];

// Body geometry is captured; palettes and uniform details are derived locally.
export function createNativeThrowBody(data,locomotion,makeCanvas,preview,detailManifest,options={}){
 const expectedSchema=options.schema??'issd-throwin-dynamic-local/v1',duration=options.duration??20,required=options.required??[0,4];
 if(data?.schema!==expectedSchema||data.width!==96||data.height!==96||!Array.isArray(data.detail_pool)||locomotion?.schema!=='issd-runtime-body-local/v1'||preview?.schema!=='issd-editor-preview-local/v1')throw Error('Dados locais de lateral incompatíveis');
 const cache=new Map(),directions=data,cycles=data.cycles;
 if(!cycles||!required.every(direction=>cycles[direction]))throw Error('Orientações de lateral indisponíveis');
 for(const [direction,frames] of Object.entries(cycles)){
  if(!Number.isInteger(+direction)||+direction<0||+direction>7||!Array.isArray(frames)||frames.length!==duration||frames.reduce((sum,f)=>sum+f.ticks,0)!==duration||frames.some(f=>!Number.isInteger(f.ticks)||f.ticks<1||!Array.isArray(f.tiles)||!Array.isArray(f.parts)||f.parts.some(p=>![0,4].includes((p.attr>>1)&7))||f.parts.some(p=>((p.attr>>1)&7)===4)&&(!Array.isArray(f.detail_variants)||f.detail_variants.length!==720||!Number.isInteger(f.detail_address))))throw Error('Quadro de lateral inválido');
 }
 const decodedDetails=new Map(),heldBallCache=new Map();
 function detailTile(index){if(!Number.isInteger(index)||typeof directions?.detail_pool?.[index]!=='string')return null;if(!decodedDetails.has(index)){try{const bytes=decode(directions.detail_pool[index]);if(bytes.length!==32)return null;decodedDetails.set(index,bytes);}catch{return null;}}return decodedDetails.get(index);}
 function usesColor(tile,index){for(let y=0;y<8;y++){let mask=255;for(let plane=0;plane<4;plane++){const byte=tile[(plane<2?0:16)+2*y+(plane%2)];mask&=(index&(1<<plane))?byte:(~byte&255);}if(mask)return true;}return false;}
 const validWords=p=>Array.isArray(p)&&p.length===16&&p.every(w=>Number.isInteger(w)&&w>=0&&w<=0x7fff);
 const validColors=p=>Array.isArray(p)&&p.length===16&&p.every(c=>typeof c==='string'&&/^#[0-9a-f]{6}$/i.test(c));
 function referenceHeight(dir){const h=locomotion.cycles?.walking?.[directionToRom[dir]]?.height;return Number.isInteger(h)&&h>0&&h<=256?h:null;}
 function supports({team,kit,appearance,position,screenDirection,palette,shirtNumber}){
  if(!Number.isInteger(team)||team<0||team>=36||!['home','away'].includes(kit)||position==='GK'||![0,1].includes(appearance?.skin_tone)||!Number.isInteger(appearance?.hair_style)||appearance.hair_style<0||appearance.hair_style>13||!validColors(palette)||!validWords(preview.teams?.[team]?.palettes?.[appearance.skin_tone])||!cycles[screenDirection]||!referenceHeight(screenDirection))return false;
  const needsDetail=cycles[screenDirection].some(f=>f.detail_variants);
  if(!needsDetail)return true;
  if(!Number.isInteger(shirtNumber)||shirtNumber<1||shirtNumber>20||!detailManifest||!directions)return false;
  let color;try{color=teamDetailColor(detailManifest,team,kit);}catch{return false;}
  return cycles[screenDirection].every(f=>{if(!f.detail_variants)return true;const tile=detailTile(f.detail_variants[team*20+shirtNumber-1]);if(!tile)return false;for(let i=1;i<16;i++)if(![10,12,13,14,15].includes(i)&&usesColor(tile,i))return false;const teamPalette=directions.team_palette?.[team],hasTeamPalette=Array.isArray(teamPalette)&&teamPalette.length===4&&teamPalette.every(w=>Number.isInteger(w)&&w>=0&&w<=0x7fff);return (!usesColor(tile,12)||color!==null||hasTeamPalette)&&(![13,14,15].some(i=>usesColor(tile,i))||hasTeamPalette)&&(!usesColor(tile,10)||(Number.isInteger(directions.palette10)&&directions.palette10>=0&&directions.palette10<=0x7fff));});
 }
 return {duration,referenceHeight,supports,
  heldBall(ticks,request){
   if(!supports(request)||!Number.isFinite(ticks)||ticks<0||ticks>=4)return null;
   const index=Math.floor(ticks),key=request.screenDirection+':'+index;
   if(heldBallCache.has(key))return heldBallCache.get(key);
   const b=cycles[request.screenDirection][index].held_ball;
   if(!b||![b.x,b.y,b.width,b.height].every(Number.isInteger)||b.width<1||b.height<1||b.width>16||b.height>16||typeof b.front!=='boolean')return null;
   let rgba;try{rgba=decode(b.rgba);}catch{return null;}if(rgba.length!==b.width*b.height*4)return null;
   const canvas=makeCanvas(b.width,b.height),ctx=canvas.getContext('2d'),image=ctx.createImageData(b.width,b.height);image.data.set(rgba);ctx.putImageData(image,0,0);
   const result={canvas,x:b.x,y:b.y,width:b.width,height:b.height,front:b.front};heldBallCache.set(key,result);return result;
  },
  frame(ticks,request){
   if(!supports(request)||!Number.isFinite(ticks)||ticks<0||ticks>=duration)return null;
   const frames=cycles[request.screenDirection];let remaining=Math.floor(ticks),index=0;while(remaining>=frames[index].ticks){remaining-=frames[index].ticks;index++;}
   const {team,kit,appearance,palette,shirtNumber}=request,key=JSON.stringify([request.screenDirection,index,team,kit,appearance.skin_tone,palette,shirtNumber]);if(cache.has(key))return cache.get(key);
   const f=frames[index],vram=new Uint8Array(65536);
   for(const tile of f.tiles){const bytes=decode(tile.data);if(bytes.length!==32||!Number.isInteger(tile.address)||tile.address<0||tile.address+32>vram.length)throw Error('Tile de lateral inválido');vram.set(bytes,tile.address);}
   const cgram=decode(f.cgram),skin=preview.teams[team].palettes[appearance.skin_tone];if(cgram.length!==512)throw Error('Paleta de lateral inválida');
   for(let i=0;i<16;i++){let word=skin[i];if(i>=7){const color=palette[i],r=Math.round(parseInt(color.slice(1,3),16)*31/255),g=Math.round(parseInt(color.slice(3,5),16)*31/255),b=Math.round(parseInt(color.slice(5,7),16)*31/255);word=r|(g<<5)|(b<<10);}const address=(128+i)*2;cgram[address]=word&255;cgram[address+1]=word>>8;}
   if(f.detail_variants){const tile=detailTile(f.detail_variants[team*20+shirtNumber-1]);if(tile.length!==32||f.detail_address<0||f.detail_address+32>vram.length)throw Error('Detalhe de uniforme inválido');vram.set(tile,f.detail_address);const rgb=teamDetailColor(detailManifest,team,kit),teamPalette=directions.team_palette?.[team];if(Array.isArray(teamPalette))for(let i=0;i<4;i++){const address=(128+4*16+12+i)*2;cgram[address]=teamPalette[i]&255;cgram[address+1]=teamPalette[i]>>8;}if(usesColor(tile,10)){const address=(128+4*16+10)*2;cgram[address]=directions.palette10&255;cgram[address+1]=directions.palette10>>8;}if(rgb){const word=rgb.reduce((w,c,i)=>w|(Math.round(c*31/255)<<(5*i)),0),address=(128+4*16+12)*2;cgram[address]=word&255;cgram[address+1]=word>>8;}}
   const result=composeOam({vram,cgram,obsel:f.obsel,parts:f.parts,width:96,height:96}),canvas=makeCanvas(96,96),ctx=canvas.getContext('2d'),image=ctx.createImageData(96,96);image.data.set(result.rgba);ctx.putImageData(image,0,0);if(cache.size>=512)cache.delete(cache.keys().next().value);cache.set(key,canvas);return canvas;
  }
 };
}
export function createNativeReceiptBody(data,locomotion,makeCanvas,preview,detailManifest){
 return createNativeThrowBody(data,locomotion,makeCanvas,preview,detailManifest,{schema:'issd-receipt-dynamic-local/v1',duration:44,required:[3]});
}

export async function loadNativeThrowBody(){
 const [r,m,p,c]=await Promise.all([fetch('./assets/issd/slide-lab-local/throwin-dynamic.json'),fetch('./assets/issd/runtime-body-local.json'),fetch('./assets/issd/editor-preview-local.json'),fetch('./data/issd-team-detail-colors.json')]);
 if(!r.ok||!m.ok||!p.ok||!c.ok)throw Error('Dados locais de lateral indisponíveis');
 return createNativeThrowBody(await r.json(),await m.json(),(w,h)=>{const canvas=document.createElement('canvas');canvas.width=w;canvas.height=h;return canvas;},await p.json(),await c.json());
}

export async function loadNativeReceiptBody(){
 const [r,m,p,c]=await Promise.all([fetch('./assets/issd/slide-lab-local/receipt-dynamic.json'),fetch('./assets/issd/runtime-body-local.json'),fetch('./assets/issd/editor-preview-local.json'),fetch('./data/issd-team-detail-colors.json')]);
 if(!r.ok||!m.ok||!p.ok||!c.ok)throw Error('Dados locais de recepção indisponíveis');
 return createNativeReceiptBody(await r.json(),await m.json(),(w,h)=>{const canvas=document.createElement('canvas');canvas.width=w;canvas.height=h;return canvas;},await p.json(),await c.json());
}
