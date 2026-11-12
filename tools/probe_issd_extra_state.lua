-- Observe roster +8; optional override temporarily writes only isolated emulator RAM.
local output=assert(os.getenv('ISSD_EXTRA_OUTPUT'))
local automation=assert(os.getenv('ISSD_INIT_AUTOMATION'))
local out=assert(io.open(output,'w'))
client.speedmode(800)
local function reg(n) local ok,v=pcall(emu.getregister,n);return ok and type(v)=='number' and v or -1 end
local function u(a) return mainmemory.read_u16_le(a) end
local first,last=string.match(os.getenv('ISSD_EXTRA_WRITE_WINDOW') or '', '^(%d+):(%d+)$')
first,last=tonumber(first),tonumber(last)
local overrideText=os.getenv('ISSD_EXTRA_OVERRIDE')
local override=overrideText and tonumber(overrideText) or nil
assert(not overrideText or (override and override%1==0 and override>=0 and override<=65535),'invalid synthetic seed')
local forceFlag=os.getenv('ISSD_EXTRA_FORCE_FLAG')=='1'
assert(not (forceFlag and override),'use only one synthetic intervention')
local entries,restoreValue,ends=0,nil,0
local restoreFlags
local watch
local function watchSeed()
 watch={}
 for _,address in ipairs({0x0078,0x7e0078}) do
  watch[#watch+1]=assert(event.onmemorywrite(function()
   local frame=emu.framecount();if frame<first or frame>last then return end
   out:write(string.format('{"site":"seed_write","frame":%d,"watch":%d,"pc":%d,"d":%d,"a":%d,"p":%d,"value":%d,"addend":%d}\n',frame,address,reg('PC'),reg('D'),reg('A'),reg('P'),u(0x78),u(0x3a)))
  end,address,'extra-seed-writes-'..address,'System Bus'))
 end
end
for _,h in ipairs({{0x83c593,'entry'},{0x83c579,'override'},{0x83c589,'override_assign'},{0x83c58d,'override_stored'},{0x83c592,'override_return'},{0x83c5ba,'team'},{0x83c600,'assign'},{0x83c609,'stored'},{0x83c639,'end'},{0x83c9fb,'actor_init'}}) do
 local address,name=h[1],h[2]
 assert(event.onmemoryexecute(function()
  local d=reg('D');if d<0 or d>0xff00 then return end
  local x=reg('X')
  local frame=emu.framecount()
  if name=='entry' then
   entries=entries+1
   if override and entries==5 then
    restoreValue=u(d+0x78);ends=0
    mainmemory.write_u16_le(d+0x78,override)
    out:write(string.format('{"site":"intervention","frame":%d,"original":%d,"replacement":%d}\n',frame,restoreValue,override))
   end
   if forceFlag and entries==5 then
    restoreFlags=u(0xde07)
    assert(restoreFlags%512<256,'flag unexpectedly already set')
    mainmemory.write_u16_le(0xde07,restoreFlags+0x100)
    out:write(string.format('{"site":"flag_intervention","frame":%d,"original":%d,"replacement":%d}\n',frame,restoreFlags,u(0xde07)))
   end
  end
  if name=='entry' and first and not watch and frame<first and frame>=first-200 then watchSeed() end
  out:write(string.format('{"site":"%s","frame":%d,"d":%d,"x":%d,"a":%d,"p":%d,"seed":%d,"source":%d,"shift":%d,"bits":%d,"remaining":%d,"flags":%d,"record_extra":%d}\n',name,emu.framecount(),d,x,reg('A'),reg('P'),u(d+0x78),u(d),u(d+2),u(d+8),u(d+4),u(0xde07),u((x%0x10000)+8)))
  out:flush()
  if name=='entry' and watch and frame>=last then for _,id in ipairs(watch) do event.unregisterbyid(id) end;watch=nil end
  if name=='override_return' and restoreFlags then
   mainmemory.write_u16_le(0xde07,restoreFlags)
   out:write(string.format('{"site":"flag_restore","frame":%d,"value":%d}\n',frame,restoreFlags));out:flush()
   restoreFlags=nil
  end
  if name=='end' and restoreValue then
   ends=ends+1
   if ends==2 then
    mainmemory.write_u16_le(0x78,restoreValue)
    out:write(string.format('{"site":"restore","frame":%d,"value":%d}\n',frame,restoreValue));out:flush()
    restoreValue=nil
   end
  end
 end,address,'extra-'..name))
end
local ok,problem=xpcall(function() dofile(automation) end,debug.traceback)
if not ok then
 local detail=tostring(problem):match('^[^\r\n]*'):gsub('\\','\\\\'):gsub('"','\\"')
 out:write('{"site":"error","detail":"'..detail..'"}\n')
end
out:close();client.exit()
