// Presentation-only helpers. This does not change SNES actor ownership,
// player-selection logic or collision simulation.
export const BALL_SPRITE_PATH='./assets/issd/ball/ball-original-8x8.png';
export const BALL_SOURCE_SIZE=8;
export const INDICATOR_MODES=Object.freeze(['arrow-name','arrow','off']);
const KEY='issd-controlled-player-indicator-v1';
export function playerDisplayName(actor){
 const raw=actor?.roster?.name;
 const value=typeof raw==='string'?raw.trim().replace(/\s+/g,' '):'';
 return value?value.slice(0,24):(actor?.number!=null?'JOGADOR '+actor.number:'JOGADOR');
}
export function readIndicatorMode(storage=globalThis.localStorage){
 try{const value=storage.getItem(KEY);return INDICATOR_MODES.includes(value)?value:'arrow-name';}
 catch{return 'arrow-name';}
}
export function saveIndicatorMode(mode,storage=globalThis.localStorage){
 if(!INDICATOR_MODES.includes(mode))throw Error('Modo de indicador inválido');
 try{storage.setItem(KEY,mode);return true;}catch{return false;}
}
export function drawPlayerIndicator(ctx,actor,mode='arrow-name'){
 if(mode==='off'||!actor||!INDICATOR_MODES.includes(mode))return;
 const x=actor.x,y=actor.y;
 ctx.save();
 ctx.translate(x,y);
 ctx.lineWidth=1;
 // High-contrast triangle anchored above the native-sized body.
 const a=-41;
 ctx.beginPath();ctx.moveTo(0,a+10);ctx.lineTo(-6,a);ctx.lineTo(6,a);ctx.closePath();
 ctx.fillStyle='#ffe56b';ctx.strokeStyle='#1b2925';ctx.lineWidth=1.8;ctx.fill();ctx.stroke();
 if(mode==='arrow-name'){
  const text=playerDisplayName(actor);
  ctx.font='700 9px monospace';ctx.textAlign='center';ctx.textBaseline='middle';
  const w=Math.ceil(ctx.measureText(text).width)+12,h=15,top=a-22;
  ctx.fillStyle='rgba(6,22,20,.9)';ctx.strokeStyle='#f4e39a';
  ctx.lineWidth=1;ctx.fillRect(-w/2,top,w,h);ctx.strokeRect(-w/2,top,w,h);
  ctx.fillStyle='#ffffff';ctx.fillText(text,0,top+h/2);
 }
 ctx.restore();
}
