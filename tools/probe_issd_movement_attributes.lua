-- Synthetic effective-field interventions in a disposable emulator only.
local seed=assert(os.getenv('ISSD_MOVE_STATE'))
local output=assert(os.getenv('ISSD_MOVE_OUTPUT'))
local out=assert(io.open(output,'w'))
local ok,problem=xpcall(function()
local function u(a) return mainmemory.read_u16_le(a) end
local cases={{'baseline',nil,nil},{'limit3',3,nil},{'limit9',9,nil},{'delay0',nil,0},{'delay8',nil,8}}
for _,case in ipairs(cases) do
 assert(savestate.load(seed,true),'Unable to load seed')
 for i=1,90 do joypad.set({},1);joypad.set(i<=2 and {X=true} or {},2);emu.frameadvance() end
 local actor=u(0x1afc)
 assert(actor>=0x0500 and actor<=0x1a00 and actor%0x100==0,'invalid controlled actor')
 local oldLimit,oldDelay=u(actor+0x62),u(actor+0x66)
 if case[2] then mainmemory.write_u8(actor+0x62,case[2]) end
 if case[3] then mainmemory.write_u8(actor+0x66,case[3]) end
 out:write(string.format('{"type":"setup","case":"%s","actor":%d,"old_limit":%d,"old_delay":%d,"limit":%d,"delay":%d}\n',case[1],actor,oldLimit,oldDelay,u(actor+0x62),u(actor+0x66)))
 for step=1,120 do
  joypad.set({},1);joypad.set({Right=true,Y=true},2);emu.frameadvance()
  local selected=u(0x1afc)
  out:write(string.format('{"type":"frame","case":"%s","step":%d,"frame":%d,"actor":%d,"selected":%d,"x":%d,"x_frac":%d,"z":%d,"z_frac":%d,"vx":%d,"vx_frac":%d,"vz":%d,"vz_frac":%d,"reference_x":%d,"reference_z":%d,"dir":%d,"state":%d,"timer":%d,"level":%d,"limit":%d,"delay":%d}\n',case[1],step,emu.framecount(),actor,selected,u(actor+8),u(actor+6),u(actor+12),u(actor+10),u(actor+0x24),u(actor+0x22),u(actor+0x28),u(actor+0x26),u(0x98),u(0x9a),u(actor+0x2e),u(actor+0x32),u(actor+0x72),u(actor+0x64),u(actor+0x62),u(actor+0x66)))
 end
end
joypad.set({},1);joypad.set({},2)
end,debug.traceback)
if not ok then
 local detail=tostring(problem):match('^[^\r\n]*'):gsub('\\','\\\\'):gsub('"','\\"')
 out:write('{"type":"error","detail":"'..detail..'"}\n')
end
out:close();client.exit()
