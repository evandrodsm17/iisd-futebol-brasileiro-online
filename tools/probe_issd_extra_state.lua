-- Observe roster +8 initialization during automated startup, without memory writes.
local output=assert(os.getenv('ISSD_EXTRA_OUTPUT'))
local automation=assert(os.getenv('ISSD_INIT_AUTOMATION'))
local out=assert(io.open(output,'w'))
client.speedmode(800)
local function reg(n) local ok,v=pcall(emu.getregister,n);return ok and type(v)=='number' and v or -1 end
local function u(a) return mainmemory.read_u16_le(a) end
for _,h in ipairs({{0x83c593,'entry'},{0x83c579,'override'},{0x83c5ba,'team'},{0x83c600,'assign'},{0x83c609,'stored'},{0x83c639,'end'},{0x83c9fb,'actor_init'}}) do
 local address,name=h[1],h[2]
 assert(event.onmemoryexecute(function()
  local d=reg('D');if d<0 or d>0xff00 then return end
  local x=reg('X')
  out:write(string.format('{"site":"%s","frame":%d,"d":%d,"x":%d,"a":%d,"p":%d,"seed":%d,"source":%d,"shift":%d,"bits":%d,"remaining":%d,"flags":%d,"record_extra":%d}\n',name,emu.framecount(),d,x,reg('A'),reg('P'),u(d+0x78),u(d),u(d+2),u(d+8),u(d+4),u(0xde07),u((x%0x10000)+8)))
  out:flush()
 end,address,'extra-'..name))
end
local ok,problem=xpcall(function() dofile(automation) end,debug.traceback)
if not ok then
 local detail=tostring(problem):match('^[^\r\n]*'):gsub('\\','\\\\'):gsub('"','\\"')
 out:write('{"site":"error","detail":"'..detail..'"}\n')
end
out:close();client.exit()
