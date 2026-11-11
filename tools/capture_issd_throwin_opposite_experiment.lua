local root=assert(os.getenv('ISSD_THROW_EXPERIMENT_OUTPUT'),'Missing output directory'):gsub('\\','/')..'/'
local log=assert(io.open(root..'navigation.txt','w'))
-- Controlled experiment: change only the scenario restart coordinate in RAM.
-- Stadium 2 width is $02C0; $02C1 is one unit beyond its opposite touchline.
local modified=false
local handle=event.onmemoryexecute(function()
 if modified or mainmemory.read_u16_le(0xE52A)~=4 or mainmemory.read_u16_le(0x042C)~=0xFFFF then return end
 local ok,x=pcall(emu.getregister,'X')
 if not ok or type(x)~='number' or x<0 or x>0x1000 then return end
 mainmemory.write_u16_le(0x042C,0x02C1)
 mainmemory.write_u16_le(0x002C+x,0x02C1)
 modified=true;log:write(string.format('SYNTHETIC modified x=%04X frame=%d\n',x,emu.framecount()));log:flush()
end,0x86D200,'synthetic-opposite-throw')
assert(handle,'Missing hook')

for frame=1,2250 do
 local input={}
 if frame>=180 and frame<=1200 and frame%120<6 then input={Start=true} end
 if frame>=1320 and frame<1326 then input={Right=true} end
 if frame>=1440 and frame<1446 then input={A=true} end
 if frame>=1680 and frame<1686 then input={Right=true} end
 if frame>=1800 and frame<1806 then input={Down=true} end
 if frame>=1920 and frame<1926 then input={A=true} end
 if frame>=2160 and frame<2166 then input={A=true} end
 if frame>=2400 and frame<2406 then input={A=true} end
 if frame>=2640 and frame<2646 then input={A=true} end
 joypad.set(input,1);emu.frameadvance()
 if frame==2200 then local ok=savestate.save(root..'throw-ready.State',true);log:write('STATE '..tostring(ok)..'\n');log:flush() end
 if frame%60==0 and frame>=1680 then
  pcall(client.screenshot,root..frame..'.png')
  log:write(string.format('%d %04X %04X %04X scenario=%04X ball=%04X,%04X\n',frame,mainmemory.read_u16_le(0x32),mainmemory.read_u16_le(0x70),mainmemory.read_u16_le(0xC0),mainmemory.read_u16_le(0xE52A),mainmemory.read_u16_le(0x408),mainmemory.read_u16_le(0x40C))); log:flush()
 end
end
joypad.set({},1);log:write('DONE '..tostring(modified)..'\n');log:close()
