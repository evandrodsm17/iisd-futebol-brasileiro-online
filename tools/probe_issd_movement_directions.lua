-- Replay identical state with neutral and directional inputs, without writing ROM/state.
local seed=assert(os.getenv('ISSD_MOVE_STATE'))
local output=assert(os.getenv('ISSD_MOVE_OUTPUT'))
local out=assert(io.open(output,'w'))
local ok,problem=xpcall(function()
local function u(a) return mainmemory.read_u16_le(a) end
local function valid(d) return d>=0x0500 and d<=0x1a00 and d%0x100==0 end
local prep=os.getenv('ISSD_MOVE_PREP_SHOT')=='1'
local cases={{'neutral',{}},{'right',{Right=true}},{'left',{Left=true}},{'up',{Up=true}},{'down',{Down=true}}}
for _,case in ipairs(cases) do
 assert(savestate.load(seed,true),'Unable to load seed')
 if prep then
  for i=1,90 do joypad.set({},1);joypad.set(i<=2 and {X=true} or {},2);emu.frameadvance() end
 end
 for step=1,120 do
  joypad.set({},1);joypad.set(case[2],2);emu.frameadvance()
  for controller,address in ipairs({0x1acc,0x1afc}) do
   local d=u(address)
   if valid(d) then
    out:write(string.format('{"case":"%s","step":%d,"frame":%d,"controller":%d,"actor":%d,"x":%d,"x_frac":%d,"z":%d,"z_frac":%d,"vx":%d,"vx_frac":%d,"vz":%d,"vz_frac":%d,"dir":%d,"state":%d,"timer":%d,"level":%d,"limit":%d,"delay":%d}\n',case[1],step,emu.framecount(),controller,d,u(d+8),u(d+6),u(d+12),u(d+10),u(d+0x24),u(d+0x22),u(d+0x28),u(d+0x26),u(d+0x2e),u(d+0x32),u(d+0x72),u(d+0x64),u(d+0x62),u(d+0x66)))
   end
  end
 end
end
joypad.set({},1);joypad.set({},2)
end,debug.traceback)
if not ok then
 local detail=tostring(problem):match('^[^\r\n]*'):gsub('\\','\\\\'):gsub('"','\\"')
 out:write('{"type":"error","detail":"'..detail..'"}\n')
end
out:close();client.exit()
