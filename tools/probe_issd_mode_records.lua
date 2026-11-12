-- Passive observation of roster selector helpers during automated startup.
local output=assert(os.getenv('ISSD_MODE_RECORD_OUTPUT'))
local automation=assert(os.getenv('ISSD_INIT_AUTOMATION'))
local out=assert(io.open(output,'w'))
out:write('{"site":"session_start"}\n');out:flush()
client.speedmode(800)
local function u(a) return mainmemory.read_u16_le(a) end
local function reg(n) local ok,v=pcall(emu.getregister,n);return ok and type(v)=='number' and v or -1 end
for _,h in ipairs({{0x8b95df,'helper_before'},{0x8b9611,'helper_after'},{0x8b9f19,'ranking_start'},{0x8b9f74,'ranking_store'},{0x8b9f83,'ranking_end'},{0x8ba1e2,'selector_before'},{0x8ba1e6,'selector_after_helper'},{0x8ba21b,'selector_after'}}) do
 local address,name=h[1],h[2]
 assert(event.onmemoryexecute(function()
  out:write(string.format('{"site":"%s","frame":%d,"d":%d,"a":%d,"x":%d,"y":%d,"flags":%d,"stage":%d,"mode":%d,"team":%d,"first":%d,"second":%d,"candidate":%d,"saved_team":%d}\n',name,emu.framecount(),reg('D'),reg('A'),reg('X'),reg('Y'),u(0x1648),u(0x1642),u(0x1654),u(0x0da0),u(0xdd00),u(0xdd02),u(0xdd08),u(0xdde0)))
  out:flush()
 end,address,'mode-record-'..name))
end
local ok,problem=xpcall(function() dofile(automation) end,debug.traceback)
if not ok then
 local detail=tostring(problem):match('^[^\r\n]*'):gsub('\\','\\\\'):gsub('"','\\"')
 out:write('{"site":"error","detail":"'..detail..'"}\n')
end
out:write('{"site":"session_end"}\n')
out:close();client.exit()
