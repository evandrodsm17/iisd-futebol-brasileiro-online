// Restricted native movement of the penalty goalkeeper proxy (8C:A125).
// The caller supplies the linked object's flags and schedules animation impulses.
const MASK=0xffffff;
const abs16=value=>{const word=value&0xffff;return word&0x8000?(-word)&0xffff:word;};
export function advanceNativePenaltyKeeper(state,linkedFlags){
 const keys=['x','y','z','vx','vy','vz'];
 if(keys.some(key=>!Number.isInteger(state?.[key])||state[key]<0||state[key]>MASK)||!Number.isInteger(linkedFlags)||linkedFlags<0||linkedFlags>0xffff)throw new RangeError('Invalid native keeper state');
 const next={...state,x:(state.x+state.vx)&MASK,y:(state.y+state.vy)&MASK,z:(state.z+state.vz)&MASK};
 let height=(next.z>>>8)&0xffff;
 if((height|(next.vz&0xffff))!==0){
  next.vz=(next.vz+0x38)&MASK;
  if((height&0x8000)===0){next.z&=0xff;next.vz=0;}
 }else{
  if(linkedFlags&2)return next;
  const slow=(v,negativeStep)=>((v+((((v&0xffff)+1)&0x8000)?negativeStep:-0x30))&MASK);
  next.vx=slow(next.vx,0x3e);next.vy=slow(next.vy,0x38);
 }
 height=(next.z>>>8)&0xffff;
 if(abs16(next.vz)<0x40&&abs16(height)<2){next.vz=0;next.z=0;}
 if(abs16(next.vx)<0x40&&((next.z>>>8)&0xffff)===0)next.vx=0;
 if(abs16(next.vy)<0x40&&((next.z>>>8)&0xffff)===0)next.vy=0;
 return next;
}
