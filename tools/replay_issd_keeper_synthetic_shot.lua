-- Reproduce one search case in isolated emulator memory. No ROM/state writes.
local state=assert(os.getenv('ISSD_KEEPER_STATE'),'Missing state')
assert(savestate.load(state,true),'Unable to load isolated replay')
local function u16(a)return mainmemory.read_u16_le(a)end
local function w(a,n)mainmemory.write_u16_le(a,n%0x10000)end
local actor=tonumber(os.getenv('ISSD_KEEPER_ACTOR') or '1280')
local sign=tonumber(os.getenv('ISSD_KEEPER_SHOT_SIDE') or (actor==0x1000 and '-1' or '1'))
assert(sign==1 or sign==-1,'Invalid shot side')
assert(mainmemory.read_u8(actor+0x30)==1,'Unexpected goalkeeper slot')
local forced_direction_text=os.getenv('ISSD_KEEPER_FORCE_DIVE_DIRECTION')
if forced_direction_text then
 local forced_direction=tonumber(forced_direction_text)
 assert(forced_direction and forced_direction%1==0 and forced_direction>=0 and forced_direction<=7,'Invalid forced dive direction')
 local scripts={[0xe924]=true,[0xe94b]=true,[0xe996]=true,[0xe9a6]=true,[0xe9cd]=true,[0xea18]=true}
 local handle=event.onmemoryexecute(function()
  local d=emu.getregister('D')
  if d==actor and scripts[u16(actor+0x1c)] then
   w(actor+0x2e,forced_direction)
   mainmemory.write_u8(actor+4,mainmemory.read_u8(actor+4)|0x40)
  end
 end,0x84e68f,'issd-keeper-synthetic-dive-direction')
 assert(handle,'Unable to register synthetic direction hook')
end
if os.getenv('ISSD_KEEPER_MOVE_TO_PLAYER')=='1' then
 w(actor+6,u16(0x1906));w(actor+8,u16(0x1908));w(actor+10,u16(0x190a));w(actor+12,u16(0x190c))
end
-- Optional synthetic camera setup: hold a harmless ball near the keeper
-- before the test, allowing the ordinary game camera to follow it.
if os.getenv('ISSD_KEEPER_CAMERA_SETUP')=='1' then
 for step=1,120 do
  w(0xa4,0);w(0xa6,0);w(0x406,0);w(0x408,u16(actor+8)+100);w(0x40a,0);w(0x40c,u16(actor+12));w(0x40e,0);w(0x410,0)
  w(0x422,0);w(0x424,0);w(0x426,0);w(0x428,0);w(0x434,0);w(0x436,0);w(0x430,3)
  joypad.set({},1);joypad.set({},2);emu.frameadvance()
 end
end
local kx,ky=u16(actor+8),u16(actor+12)
local dy=tonumber(os.getenv('ISSD_KEEPER_SHOT_DY') or '-32')
w(0xa4,0);w(0xa6,0)
w(0x406,0);w(0x408,kx+24*sign);w(0x40a,0);w(0x40c,ky+dy);w(0x40e,0);w(0x410,-8)
w(0x422,0);w(0x424,-5*sign);w(0x426,0);w(0x428,0);w(0x434,0);w(0x436,0);w(0x430,3)
for step=1,80 do joypad.set({},1);joypad.set({},2);emu.frameadvance() end
joypad.set({},1);joypad.set({},2)
