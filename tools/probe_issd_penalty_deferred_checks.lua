-- Isolated replay: capture native values immediately before deferred checks.
local output=assert(os.getenv('ISSD_PENALTY_DEFERRED_OUTPUT'))
local automation=assert(os.getenv('ISSD_INIT_AUTOMATION'))
assert(os.getenv('ISSD_AUTO_FAST_COMPETITION')=='1' and os.getenv('ISSD_AUTO_MENU_MODE')=='world_series' and os.getenv('ISSD_AUTO_PENALTY_DIRECTION')=='Right' and os.getenv('ISSD_AUTO_PENALTY_CONTROLLER')=='p1','Unexpected capture configuration')
local out=assert(io.open(output,'w'))
local function u(a)return mainmemory.read_u16_le(a)end
local function reg(n)local ok,v=pcall(emu.getregister,n);return ok and type(v)=='number' and v or -1 end
out:write('{"site":"session_start"}\n');out:flush();client.speedmode(800)
for _,item in ipairs({{0x8c8e62,'check'},{0x8c8e6f,'finalize'},{0x8c8dc1,'resolved'}}) do
 local addr,name=item[1],item[2]
 assert(event.onmemoryexecute(function()
  local frame,d=emu.framecount(),reg('D')
  if d~=0x700 or not ((frame>=10278 and frame<=10316) or (frame>=11238 and frame<=11276)) then return end
  out:write(string.format('{"site":"%s","frame":%d,"side":%d,"round":%d,"d":%d,"x":%d,"y":%d,"height":%d,"timer":%d,"field28":%d,"field29":%d,"field32":%d,"field33":%d,"flags":%d,"home":%d,"away":%d}\n',name,frame,u(0x1440),u(0x1704),d,u(d+8),u(d+0xc),u(d+0x10),u(d+0x24),u(d+0x28),u(d+0x29),u(d+0x32),u(d+0x33),u(0x14aa),mainmemory.read_u8(0xd442),mainmemory.read_u8(0xd443)))
  out:flush()
 end,addr,'penalty-deferred-check-'..name))
end
local ok,problem=xpcall(function()dofile(automation)end,debug.traceback)
if not ok then local message=tostring(problem):match('^[^\r\n]*'):gsub('\\','\\\\'):gsub('"','\\"');out:write('{"site":"error","detail":"'..message..'"}\n') end
out:write('{"site":"session_end"}\n');out:close();client.exit()
