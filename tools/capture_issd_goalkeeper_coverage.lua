-- Isolated replay: send inputs to both controllers and record goalkeeper OAM
-- geometry. This script does not write to the ROM or operate the user's UI.
local state=assert(os.getenv('ISSD_KEEPER_STATE'),'Missing replay state')
local output=assert(os.getenv('ISSD_KEEPER_OUTPUT'),'Missing output')
assert(savestate.load(state,true),'Unable to load isolated replay')
local out=assert(io.open(output,'w'))
local function u16(a)return mainmemory.read_u16_le(a) end
local function s16(a)local n=u16(a);return n>=0x8000 and n-0x10000 or n end
local sizes={{8,16},{8,32},{8,64},{16,32},{16,64},{32,64},{16,32},{16,32}}
-- Descriptor-to-pose pointers read from the USA ROM at $82:CAB1/B6/BB.
local wanted={[0xcab1]=0x4aa4,[0xcab6]=0x4ab4,[0xcabb]=0x4ac0}
local seen={};local count=0;local hooks=0;local running=0;local directions={}
local synthetic=os.getenv('ISSD_KEEPER_FORCE_DIRECTION')=='1'
local displaced=os.getenv('ISSD_KEEPER_DISPLACE')=='1'
if displaced then
 for _,actor in ipairs({0x0500,0x1000}) do
  assert(mainmemory.read_u8(actor+0x30)==1,'Unexpected goalkeeper slot')
  mainmemory.write_u16_le(actor+8,(u16(actor+8)+50)%0x10000)
  mainmemory.write_u16_le(actor+12,(u16(actor+12)+20)%0x10000)
 end
end
if synthetic then
 local handle=event.onmemoryexecute(function()
  local actor=emu.getregister('D')
  if actor>=0x0500 and actor<=0x1a00 and actor%0x100==0 and mainmemory.read_u8(actor+0x30)==1 and u16(actor+0x1c)==0xe34a then
   hooks=hooks+1
   mainmemory.write_u16_le(actor+0x2e,4)
   mainmemory.write_u8(actor+4,mainmemory.read_u8(actor+4)|0x40)
  end
 end,0x84e68f,'issd-keeper-forced-direction')
 assert(handle,'Unable to register isolated direction hook')
end
for step=1,3600 do
 local phase=math.floor((step-1)/180)%8
 local moves={{Right=true},{Down=true},{Left=true},{Up=true},{Right=true,Down=true},{Left=true,Down=true},{Left=true,Up=true},{Right=true,Up=true}}
 local p1=moves[phase+1];local p2=moves[((phase+4)%8)+1]
 joypad.set(p1,1);joypad.set(p2,2);emu.frameadvance()
 for actor=0x0500,0x1a00,0x100 do
  local desc=u16(actor+0x14);local pose=u16(actor)
  if mainmemory.read_u8(actor+0x30)==1 and u16(actor+0x1c)==0xe34a then local d=u16(actor+0x2e);directions[d]=(directions[d] or 0)+1;running=running+1 end
  if mainmemory.read_u8(actor+0x30)==1 and u16(actor+0x1c)==0xe34a and u16(actor+0x2e)==4 and wanted[desc]==pose and not seen[desc] and pose>0 and pose<0xa000 then
   local n=mainmemory.read_u8(pose);local obsel=mainmemory.read_u8(0x1ea6)
   if n>0 and n<=32 and pose+n*2<0xa000 then
    local inherited=mainmemory.read_u8(actor+5);if inherited&0x80==0 then inherited=mainmemory.read_u8(0x7c) end
    local flags=mainmemory.read_u8(actor+4);local props=mainmemory.read_u8(actor+3)|((inherited&0x30)|(flags&0xf0));local parts={}
    for i=0,n-1 do
     local entry=pose+i*2;local raw=mainmemory.read_u8(0x6001+entry);local large=mainmemory.read_u8(entry+1)&0x80~=0
     local attr=(raw&0xc1)~props;if raw&0x20~=0 then if attr&8~=0 then attr=attr|2 else attr=(attr&0xfb)|8 end end
     local dx=s16(0x2000+entry);if props&0x40~=0 then dx=-dx end
     local tile=mainmemory.read_u8(0x6000+entry)
     parts[#parts+1]=string.format('{"x":%d,"y":%d,"geometry_tile":%d,"tile":%d,"size":%d,"attr":%d}',dx-(large and 8 or 4),s16(0x4000+entry)-(large and 8 or 4),tile,(tile+u16(actor+2))&255,sizes[(obsel>>5)+1][large and 2 or 1],attr)
    end
    out:write(string.format('{"frame":%d,"synthetic_direction":%s,"synthetic_position":%s,"actors":[{"address":%d,"animation_script":%d,"type":1,"direction":4,"descriptor":%d,"pose":%d,"object_flags":%d,"parts":[%s]}]}\n',emu.framecount(),tostring(synthetic),tostring(displaced),actor,0xe34a,desc,pose,flags,table.concat(parts,',')))
    out:flush();seen[desc]=true;count=count+1
   end
  end
 end
 if step%300==0 then local f=assert(io.open(output..'.status','w'));local counts={};for k,v in pairs(directions) do counts[#counts+1]=string.format('"%d":%d',k,v) end;f:write(string.format('{"step":%d,"hooks":%d,"running":%d,"captured":%d,"directions":{%s}}',step,hooks,running,count,table.concat(counts,',')));f:close() end
 if count==3 then break end
end
joypad.set({},1);joypad.set({},2);out:close()
