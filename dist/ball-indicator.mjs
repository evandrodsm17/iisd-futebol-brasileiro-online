// Presentation only: player indicators never change actor selection or physics.
export const BALL_SPRITE_PATH='./assets/issd/ball/ball-original-8x8.png';
export const BALL_SOURCE_SIZE=8;
export const INDICATOR_ARROW_PATH='./assets/issd/ui/controlled-arrow.png';
export const INDICATOR_ARROW_WIDTH=18;
export const INDICATOR_ARROW_HEIGHT=15;
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
// All dimensions are match-world pixels, before the camera transform.
export function drawPlayerIndicator(ctx,actor,mode='arrow-name',arrowSprite=null){
 if(mode==='off'||!actor||!INDICATOR_MODES.includes(mode))return;
 ctx.save();
 ctx.translate(actor.x,actor.y);
 const arrowTop=-46;
 if(arrowSprite?.complete&&arrowSprite.naturalWidth===INDICATOR_ARROW_WIDTH&&arrowSprite.naturalHeight===INDICATOR_ARROW_HEIGHT){
  ctx.imageSmoothingEnabled=false;
  ctx.drawImage(arrowSprite,-INDICATOR_ARROW_WIDTH/2,arrowTop,INDICATOR_ARROW_WIDTH,INDICATOR_ARROW_HEIGHT);
 }else{
  // Only for a missing asset; shipped UI uses the transparent pixel-art PNG.
  ctx.beginPath();ctx.moveTo(-7,arrowTop);ctx.lineTo(7,arrowTop);ctx.lineTo(0,arrowTop+12);ctx.closePath();
  ctx.fillStyle='#ffdd52';ctx.fill();
 }
 if(mode==='arrow-name'){
  const text=playerDisplayName(actor);
  ctx.font='700 9px "Silkscreen", monospace';
  ctx.textAlign='center';ctx.textBaseline='middle';
  ctx.fillStyle='#fff8dc';
  ctx.shadowColor='rgba(0,0,0,0.98)';
  ctx.shadowOffsetX=1.5;ctx.shadowOffsetY=2;ctx.shadowBlur=1;
  // No background, label box or border. Shadow is attached to glyphs only.
  ctx.fillText(text,0,-57);
 }
 ctx.restore();
}
