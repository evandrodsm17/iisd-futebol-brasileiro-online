-- Controlled X-hold durations from the same pre-action replay state.
local seed=assert(os.getenv('ISSD_HOLD_STATE'));local output=assert(os.getenv('ISSD_HOLD_OUTPUT'));local out=assert(io.open(output,'w'))
local trial,step=0,0
local function u(a)return mainmemory.read_u16_le(a)end
local function reg(n)local ok,v=pcall(emu.getregister,n);return ok and type(v)=='number' and v or -1 end
for _,h in ipairs({{0x80da68,'80DA68'},{0x85f685,'85F685'},{0x85f694,'85F694'},{0x85f6ba,'85F6BA'},{0x85f70c,'85F70C'},{0x85f871,'85F871'},{0x85f89b,'85F89B'},{0x85f8d6,'85F8D6'}}) do
 local addr,name=h[1],h[2];assert(event.onmemoryexecute(function()
  if trial==0 or reg('D')~=0x1900 then return end
  out:write(string.format('{"type":"hook","trial":%d,"step":%d,"frame":%d,"site":"%s","x":%d,"y":%d,"held":%d,"charge":%d,"mask":%d,"flags":%d,"carrier":%d,"ballType":%d,"vz":%d}\n',trial,step,emu.framecount(),name,reg('X'),reg('Y'),u(0x22),u(0x1982),u(0x1980),u(0x196e),u(0xa6),u(0x430),u(0x436)))
 end,addr,'hold-'..name))
end
for _,duration in ipairs({1,3,6,10,15,20}) do
 trial=trial+1;step=0;assert(savestate.load(seed,true));assert(u(0xa6)==0x1900 and u(0x192e)==4,'unexpected possession or facing')
 out:write(string.format('{"type":"case","trial":%d,"heldFrames":%d,"initialFrame":%d,"initialBallType":%d,"initialCharge":%d}\n',trial,duration,emu.framecount(),u(0x430),u(0x1982)))
 for i=1,45 do
  step=i;joypad.set({},1);joypad.set(i<=duration and {X=true} or {},2);emu.frameadvance()
  out:write(string.format('{"type":"frame","trial":%d,"step":%d,"held":%d,"charge":%d,"mask":%d,"flags":%d,"script":%d,"carrier":%d,"ballType":%d,"vx":%d,"vxFrac":%d,"vy":%d,"vyFrac":%d,"vz":%d,"vzFrac":%d}\n',trial,step,u(0x22),u(0x1982),u(0x1980),u(0x196e),u(0x191c),u(0xa6),u(0x430),u(0x424),u(0x422),u(0x428),u(0x426),u(0x436),u(0x434)))
 end
end
trial=0;joypad.set({},1);joypad.set({},2);out:close();client.exit()
