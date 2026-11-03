-- Synthetic, isolated tests of the original palette routine during automatic navigation.
-- The team fields and destination palette word are restored before the caller resumes.
local directory=assert(os.getenv('ISSD_AUTO_OUTPUT_DIR'),'Missing isolated output directory')
local output=assert(io.open(directory..'/detail-color-probe.jsonl','w'))
local cases={{4,0},{5,1},{2,1},{2,0}}
local pending=nil
local nextcase=1
local function reg(n) return emu.getregister(n) end
local function read(a) return mainmemory.read_u16_le(a) end
local function write(a,v) mainmemory.write_u16_le(a,v) end
local entry=event.onmemoryexecute(function()
 if pending or nextcase>#cases then return end
 local y=reg('Y'); local destination=reg('A')%65536
 if (y~=0x0d00 and y~=0x0e00) or (destination~=0x2d98 and destination~=0x2db8) then return end
 local c=cases[nextcase]
 pending={y=y,destination=destination,team=read(y+0xa0),flags=read(y+0xa4),color=read(destination),case=c}
 write(y+0xa0,c[1]*2)
 local flags=read(y+0xa4)
 if c[2]==1 then flags=bit.bor(flags,8) else flags=bit.band(flags,0xfff7) end
 write(y+0xa4,flags);write(destination,0x1234)
end,0x8bd151,'issd-detail-color-enter')
local finish=event.onmemoryexecute(function()
 if not pending then return end
 local p=pending
 output:write(string.format('{"team":%d,"kit":%d,"seed":4660,"result":%d,"destination":%d,"frame":%d}\n',p.case[1],p.case[2],read(p.destination),p.destination,emu.framecount()))
 output:flush()
 write(p.y+0xa0,p.team);write(p.y+0xa4,p.flags);write(p.destination,p.color)
 pending=nil;nextcase=nextcase+1
end,0x8bd175,'issd-detail-color-exit')
assert(entry and finish,'Unable to register palette routine hooks')
dofile(assert(os.getenv('ISSD_AUTO_PROBE_SCRIPT'),'Missing automatic probe script'))
output:close()
