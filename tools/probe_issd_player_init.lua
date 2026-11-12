-- Wrapper for automated startup; any optional edit touches only emulator RAM.
local output=assert(os.getenv('ISSD_INIT_OUTPUT'))
local automation=assert(os.getenv('ISSD_INIT_AUTOMATION'))
local patch=os.getenv('ISSD_INIT_PATCH')=='1'
local out=assert(io.open(output,'w'))
local function reg(n) local ok,v=pcall(emu.getregister,n);return ok and type(v)=='number' and v or -1 end
local function byte(a) return mainmemory.read_u8(a) end
local function word(a) return mainmemory.read_u16_le(a) end
local patched=false
client.speedmode(800)
assert(event.onmemoryexecute(function()
 local d,x=reg('D'),reg('X')
 if d<0x0500 or d>0x1a00 or d%0x100~=0 or x<0x3e00 or x>0x3f8e then return end
 local before=byte(x)
 if patch and not patched and d==0x1a00 then mainmemory.write_u8(x,0x93);patched=true end
 out:write(string.format('{"site":"before","frame":%d,"actor":%d,"record":%d,"original":%d,"raw":%d,"extra":%d}\n',emu.framecount(),d,x,before,byte(x),byte(x+8)))
 out:flush()
end,0x83c9fb,'attribute-init-before'))
assert(event.onmemoryexecute(function()
 local d,x=reg('D'),reg('X')
 if d<0x0500 or d>0x1a00 or d%0x100~=0 or x<0x3e00 or x>0x3f8e then return end
 out:write(string.format('{"site":"after","frame":%d,"actor":%d,"record":%d,"raw":%d,"extra":%d,"limit_low":%d,"delay_low":%d}\n',emu.framecount(),d,x,byte(x),byte(x+8),byte(d+0x62),byte(d+0x66)))
 out:flush()
end,0x83ca15,'attribute-init-after'))
local ok,problem=xpcall(function() dofile(automation) end,debug.traceback)
if not ok then
 local detail=tostring(problem):match('^[^\r\n]*'):gsub('\\','\\\\'):gsub('"','\\"')
 out:write('{"site":"error","detail":"'..detail..'"}\n')
end
out:close();client.exit()
