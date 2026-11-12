// Experimental adapter; preserves native provenance and does not alter game physics.
// Edited ratings use the project's lossy inverse quantization, not an ISSD formula.
function projection(nibble){
  const native=Math.max(2,Math.min(9,nibble));
  const band=Array.from({length:100},(_,i)=>i).filter(i=>2+Math.floor((i*7+49)/99)===native);
  return Math.floor((band[0]+band.at(-1))/2);
}
function nativeLevel(value){return 2+Math.floor((value*7+49)/99);}

export function resolveNativeMovementAttributes(player,extraState){
  const raw=player?.raw?.attributes_hex;
  if(typeof raw!=='string'||!/^[0-9a-f]{14}$/i.test(raw))return null;
  if(!Number.isInteger(extraState)||extraState<0||extraState>4)throw new RangeError('Estado nativo fora do domínio validado');
  const original=parseInt(raw.slice(0,2),16),changes={};
  let effective=original;
  for(const [name,shift] of [['acceleration',4],['speed',0]]){
    const value=player.attributes?.[name],nibble=(original>>shift)&15;
    if(!Number.isInteger(value)||value<0||value>99)throw new RangeError('Atributo ausente ou inválido: '+name);
    const edited=value!==projection(nibble);
    if(edited){
      if(value<1)throw new RangeError('Atributo editado deve estar entre 1 e 99');
      effective=(effective&~(15<<shift))|(nativeLevel(value)<<shift);
    }
    changes[name]=edited;
  }
  if((effective>>4)>9)throw new RangeError('Aceleração nativa fora do domínio validado');
  const delta=Math.min(0,extraState*2-4);
  return {originalByte:original,effectiveByte:effective,edited:changes,extraState,
    limitLow:Math.max(0,(effective&15)+delta),delayLow:Math.min(9,9-(effective>>4)-delta)};
}
