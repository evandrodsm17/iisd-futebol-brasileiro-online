-- Isolated replay: inspect native branch inputs for eight previously identified frames.
local output=assert(os.getenv('ISSD_PENALTY_GATES_OUTPUT'))
local automation=assert(os.getenv('ISSD_INIT_AUTOMATION'))
assert(os.getenv('ISSD_AUTO_FAST_COMPETITION')=='1' and os.getenv('ISSD_AUTO_MENU_MODE')=='world_series' and os.getenv('ISSD_AUTO_PENALTY_DIRECTION')=='Right' and os.getenv('ISSD_AUTO_PENALTY_CONTROLLER')=='p1','Unexpected capture configuration')
local out=assert(io.open(output,'w'))
local targets={[9850]=true,[9851]=true,[10276]=true,[10293]=true,[11236]=true,[11253]=true,[11682]=true,[11683]=true}
local function u(a)return mainmemory.read_u16_le(a)end
local function u24(a)return u(a)+mainmemory.read_u8(a+2)*65536 end
local function reg(name)local ok,v=pcall(emu.getregister,name);return ok and type(v)=='number' and v or -1 end
out:write('{"site":"session_start","scope":"eight-recorded-frames"}\n');out:flush()
client.speedmode(800)
for _,item in ipairs({{0x8c9fa7,'move_start'},{0x8c9ff9,'friction_start'},{0x8ca027,'friction_x_gate'},{0x8ca055,'friction_end'},{0x8c9fb9,'gravity_start'},{0x8c9fd2,'bounce'},{0x8c9ff8,'move_end'},{0x8ca056,'stop_start'},{0x8ca0a2,'stop_end'}}) do
 local addr,name=item[1],item[2]
 assert(event.onmemoryexecute(function()
  local frame,d=emu.framecount(),reg('D')
  if not targets[frame] or d~=0x700 then return end
  out:write(string.format('{"site":"%s","frame":%d,"side":%d,"round":%d,"d":%d,"x":%d,"y":%d,"z":%d,"vx":%d,"vy":%d,"vz":%d,"gravity":%d}\n',name,frame,u(0x1440),u(0x1704),d,u24(d+7),u24(d+0x0b),u24(d+0x0f),u24(d+0x28),u24(d+0x32),u24(d+0x2b),u24(0x172e)))
  out:flush()
 end,addr,'penalty-ground-gate-'..name))
end
local ok,problem=xpcall(function()dofile(automation)end,debug.traceback)
if not ok then local message=tostring(problem):match('^[^\r\n]*'):gsub('\\','\\\\'):gsub('"','\\"');out:write('{"site":"error","detail":"'..message..'"}\n') end
out:write('{"site":"session_end"}\n');out:close();client.exit()
