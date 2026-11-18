-- Isolated replay from a locally captured pre-shot savestate. No ROM writes.
local seed=assert(os.getenv('ISSD_HOLD_STATE'))
local output=assert(os.getenv('ISSD_HOLD_OUTPUT'))
local out=assert(io.open(output,'w'))
local trial,step=0,0
local function u(a)return mainmemory.read_u16_le(a)end
local function reg(n)local ok,v=pcall(emu.getregister,n);return ok and type(v)=='number' and v or -1 end
local hooks={{0x80e770,'80E770'},{0x80e781,'80E781'},{0x80e788,'80E788'},
 {0x85f694,'85F694'},{0x85f6be,'85F6BE'},{0x85f70c,'85F70C'},
 {0x85f871,'85F871'},{0x85f89b,'85F89B'}}
for _,item in ipairs(hooks) do
 local addr,name=item[1],item[2]
 assert(event.onmemoryexecute(function()
  local d=reg('D');if trial==0 or d~=0x1900 then return end
  out:write(string.format('{"type":"hook","trial":%d,"step":%d,"frame":%d,"site":"%s","d":%d,"x":%d,"y":%d,"flags":%d,"actor40":%d,"actor2a":%d,"middle":%d,"charge":%d,"carrier":%d,"ballType":%d}\n',trial,step,emu.framecount(),name,d,reg('X'),reg('Y'),u(d+0x6e),u(d+0x40),u(d+0x2a),u(0x12f2),u(d+0x82),u(0xa6),u(0x430)));out:flush()
 end,addr,'shot-detail-'..name))
end
out:write('{"type":"session_start"}\n')
for _,duration in ipairs({1,3,6,10,15,20}) do
 trial=trial+1;step=0;assert(savestate.load(seed,true));assert(u(0xa6)==0x1900 and u(0x192e)==4,'unexpected replay state')
 out:write(string.format('{"type":"case","trial":%d,"heldFrames":%d}\n',trial,duration))
 for i=1,45 do
  step=i;joypad.set({},1);joypad.set(i<=duration and {X=true} or {},2);emu.frameadvance()
  out:write(string.format('{"type":"frame","trial":%d,"step":%d,"flags":%d,"actor40":%d,"actor2a":%d,"middle":%d,"charge":%d,"carrier":%d,"ballType":%d}\n',trial,step,u(0x196e),u(0x1940),u(0x192a),u(0x12f2),u(0x1982),u(0xa6),u(0x430)))
 end
end
trial=0;joypad.set({},1);joypad.set({},2);out:write('{"type":"session_end"}\n');out:close();client.exit()
