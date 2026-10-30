// Standard browser Gamepad API -> P1 logical actions. Provisional field-play
// preset, not a claimed SNES controller encoding. Native button functions
// depend on the current cartridge scene.
export const STANDARD_GAMEPAD_DEFAULTS = Object.freeze({
  up:12,down:13,left:14,right:15,
  press:0,pass:1,shot:2,run:3,switch:5,tactical:8,start:9,
});
const EDGE_ACTIONS=['shot','pass','press','switch','tactical','start'];
export function createGamepadSampler(mapping=STANDARD_GAMEPAD_DEFAULTS,deadzone=0.35){
  if(!Number.isFinite(deadzone)||deadzone<0.1||deadzone>=1)throw RangeError('invalid deadzone');
  const indices=Object.values(mapping);
  if(indices.some(i=>!Number.isInteger(i)||i<0)||new Set(indices).size!==indices.length)throw Error('invalid or overlapping buttons');
  let currentIndex=null,previous=new Set(),neutralRequired=true;
  function reset(){currentIndex=null;previous.clear();neutralRequired=true;}
  function sample(pads){
    const available=Array.from(pads??[]).filter(p=>p?.connected&&p.mapping==='standard');
    const pad=available.find(p=>p.index===currentIndex)??available[0];
    if(!pad){reset();return {connected:false,held:new Set(),pressed:[],padIndex:null};}
    if(pad.index!==currentIndex){currentIndex=pad.index;previous.clear();neutralRequired=true;}
    const held=new Set();
    for(const [action,i] of Object.entries(mapping))if(pad.buttons?.[i]?.pressed)held.add(action);
    const x=pad.axes?.[0]??0,y=pad.axes?.[1]??0;
    if(x<=-deadzone)held.add('left');if(x>=deadzone)held.add('right');
    if(y<=-deadzone)held.add('up');if(y>=deadzone)held.add('down');
    for(const [a,b] of [['left','right'],['up','down']])if(held.has(a)&&held.has(b)){held.delete(a);held.delete(b);}
    if(neutralRequired){
      if(!held.size)neutralRequired=false;
      previous=new Set(held);return {connected:true,held:new Set(),pressed:[],padIndex:pad.index};
    }
    const pressed=EDGE_ACTIONS.filter(a=>held.has(a)&&!previous.has(a));
    previous=new Set(held);
    return {connected:true,held,pressed,padIndex:pad.index};
  }
  return {sample,reset};
}
export function readBrowserGamepads(nav){
  try{return typeof nav?.getGamepads==='function'?nav.getGamepads():[];}catch{return [];}
}
