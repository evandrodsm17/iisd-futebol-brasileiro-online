-- Isolated replay; observes pre-instruction hooks, leaves ROM and state file intact.
local state=assert(os.getenv('ISSD_MOVE_STATE'))
local output=assert(os.getenv('ISSD_MOVE_OUTPUT'))
local out=assert(io.open(output,'w'))
local step=0
local function u(a) return mainmemory.read_u16_le(a) end
local function reg(n) local ok,v=pcall(emu.getregister,n); return ok and type(v)=='number' and v or -1 end
local function actor(d) return d>=0x0500 and d<=0x1a00 and d%0x100==0 end
for _,h in ipairs({{0x80dd9f,'entry'},{0x80dd9d,'carry'},{0x80ddb4,'increment'},{0x80ddbe,'project'}}) do
 local addr,name=h[1],h[2]
 assert(event.onmemoryexecute(function()
  local d=reg('D'); if step==0 or not actor(d) then return end
  out:write(string.format('{"type":"hook","step":%d,"frame":%d,"site":"%s","actor":%d,"timer":%d,"level":%d,"limit":%d,"delay":%d,"x":%d,"z":%d,"dir":%d,"state":%d,"y":%d}\n',step,emu.framecount(),name,d,u(d+0x72),u(d+0x64),u(d+0x62),u(d+0x66),u(d+8),u(d+12),u(d+0x2e),u(d+0x32),reg('Y')))
 end,addr,'movement-'..name))
end
assert(savestate.load(state,true),'Unable to load isolated state')
for i=1,240 do
 step=i;joypad.set({},1);joypad.set({Right=true},2);emu.frameadvance()
end
step=0;joypad.set({},1);joypad.set({},2);out:close();client.exit()
