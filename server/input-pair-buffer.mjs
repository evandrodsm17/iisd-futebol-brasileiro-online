import {decodeOnlineInput} from '../dist/online-input.mjs';

// Experimental lockstep input collection; no simulation or clock is driven here.
export function createInputPairBuffer(maxAhead=8){
 if(!Number.isInteger(maxAhead)||maxAhead<1)throw new RangeError('maxAhead');
 let nextTick=0;
 const expected=new Map([[1,0],[2,0]]),pending=new Map();
 return {
  submit(seat,packet){
   if(seat!==1&&seat!==2)return {error:'invalid_seat'};
   const decoded=decodeOnlineInput(packet);
   if(!decoded)return {error:'invalid_input'};
   if(decoded.tick!==expected.get(seat))return {error:'unexpected_tick'};
   if(decoded.tick>=nextTick+maxAhead)return {error:'input_window_full'};
   let pair=pending.get(decoded.tick);if(!pair){pair=new Map();pending.set(decoded.tick,pair);}
   pair.set(seat,{tick:decoded.tick,held:packet.held,actions:decoded.frame.actions});
   expected.set(seat,decoded.tick+1);
   if(pair.size<2)return {pair:null};
   const result={tick:nextTick,inputs:[pair.get(1),pair.get(2)]};
   pending.delete(nextTick);nextTick++;
   return {pair:result};
  },
 };
}
