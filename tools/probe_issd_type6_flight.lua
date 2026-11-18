-- Isolated saved-state replay, with native controller inputs and no RAM writes.
local seed=assert(os.getenv('ISSD_HOLD_STATE'))
local out=assert(io.open(assert(os.getenv('ISSD_HOLD_OUTPUT')),'w'))
local trial,step=0,0
local function u(a)return mainmemory.read_u16_le(a)end
local function reg(n)local ok,v=pcall(emu.getregister,n);return ok and type(v)=='number' and v or -1 end
local hooks={{0x83941f,'83941F'},{0x83942e,'83942E'},{0x83882a,'83882A'},
 {0x838863,'838863'},{0x838865,'838865'},{0x838883,'838883'}}
if os.getenv('ISSD_BOUNCE_TRACE')=='1' then
 for _,h in ipairs({{0x838941,'838941'},{0x83895d,'83895D'},{0x838962,'838962'},
  {0x838866,'838866'},{0x83898d,'83898D'},{0x8389af,'8389AF'},
  {0x8389c4,'8389C4'},{0x8389ce,'8389CE'},{0x8388bb,'8388BB'}}) do hooks[#hooks+1]=h end
end
for _,item in ipairs(hooks) do
 local addr,name=item[1],item[2]
 assert(event.onmemoryexecute(function()
  if trial==0 or u(0xa6)~=0 or u(0x430)~=6 then return end
  out:write(string.format('{"type":"vertical","trial":%d,"step":%d,"frame":%d,"site":"%s","x":%d,"a":%d,"z":%d,"zFrac":%d,"vz":%d,"vzFrac":%d,"vx":%d,"vxFrac":%d,"vy":%d,"vyFrac":%d,"gravity":%d,"parameter":%d,"flags":%d,"weather":%d,"ballType":%d,"carrier":%d}\n',trial,step,emu.framecount(),name,reg('X'),reg('A'),u(0x410),u(0x40e),u(0x436),u(0x434),u(0x424),u(0x422),u(0x428),u(0x426),u(0x458),u(0x456),u(0x46e),u(0x1e4c),u(0x430),u(0xa6)));out:flush()
 end,addr,'type6-flight-'..name))
end
out:write('{"type":"session_start","synthetic":false}\n')
for _,direction in ipairs({'Right','UpRight','DownRight'}) do
 trial=trial+1;step=0;assert(savestate.load(seed,true));assert(u(0xa6)==0x1900 and u(0x192e)==4,'unexpected replay state')
 out:write(string.format('{"type":"case","trial":%d,"direction":"%s","buttonFrames":6}\n',trial,direction))
 for i=1,160 do
  step=i;local input={Right=true};if direction=='UpRight' then input.Up=true elseif direction=='DownRight' then input.Down=true end
  if i<=6 then input.X=true end
  joypad.set({},1);joypad.set(input,2);emu.frameadvance()
  out:write(string.format('{"type":"frame","trial":%d,"step":%d,"ballType":%d,"carrier":%d,"z":%d,"zFrac":%d,"vz":%d,"vzFrac":%d,"gravity":%d}\n',trial,step,u(0x430),u(0xa6),u(0x410),u(0x40e),u(0x436),u(0x434),u(0x458)))
 end
end
trial=0;joypad.set({},1);joypad.set({},2);out:write('{"type":"session_end"}\n');out:close();client.exit()
