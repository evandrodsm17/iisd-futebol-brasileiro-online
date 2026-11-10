-- Isolated search only: load the same saved state for every test and inject a
-- synthetic free ball near the goalkeeper. Never writes to the ROM or disk state.
local state=assert(os.getenv('ISSD_KEEPER_STATE'),'Missing state')
local output=assert(os.getenv('ISSD_KEEPER_OUTPUT'),'Missing output')
local out=assert(io.open(output,'w'))
local function u16(a)return mainmemory.read_u16_le(a)end
local function w(a,n) mainmemory.write_u16_le(a,n%0x10000) end
local wanted={[0xe924]=true,[0xe94b]=true,[0xe996]=true,[0xe9cd]=true,[0xea18]=true}
local found=0
for _,dx in ipairs({24,48,80,120}) do
 for _,dy in ipairs({-32,0,32}) do
  for _,height in ipairs({-8,-32,-64}) do
   assert(savestate.load(state,true),'Unable to load isolated replay')
   local actor=tonumber(os.getenv('ISSD_KEEPER_ACTOR') or '1280')
   local sign=actor==0x1000 and -1 or 1
   assert(mainmemory.read_u8(actor+0x30)==1,'Unexpected goalkeeper slot')
   if os.getenv('ISSD_KEEPER_MOVE_TO_PLAYER')=='1' then
    w(actor+6,u16(0x1906));w(actor+8,u16(0x1908));w(actor+10,u16(0x190a));w(actor+12,u16(0x190c))
   end
   local kx,ky=u16(actor+8),u16(actor+12)
   w(0xa4,0);w(0xa6,0)
   w(0x406,0);w(0x408,kx+dx*sign);w(0x40a,0);w(0x40c,ky+dy);w(0x40e,0);w(0x410,height)
   w(0x422,0);w(0x424,-5*sign);w(0x426,0);w(0x428,0);w(0x434,0);w(0x436,0);w(0x430,3)
   local scripts={};local first=nil
   for step=1,100 do
    joypad.set({},1);joypad.set({},2);emu.frameadvance()
    local script=u16(actor+0x1c)
    if wanted[script] then
     scripts[script]=true;first=first or step
    end
   end
   local ids={};for script in pairs(scripts) do ids[#ids+1]=tostring(script) end;table.sort(ids)
   if first then found=found+1 end
   out:write(string.format('{"dx":%d,"dy":%d,"height":%d,"first":%s,"scripts":[%s]}\n',dx,dy,height,first and tostring(first) or 'null',table.concat(ids,',')))
   out:flush()
  end
 end
end
joypad.set({},1);joypad.set({},2);out:close()
print('Synthetic keeper shots triggering dive scripts: '..found)
