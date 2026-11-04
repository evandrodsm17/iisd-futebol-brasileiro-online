-- Capture same-frame OAM/VRAM/CGRAM for selected P1's slide/get-up poses.
-- Raw assets remain local; this wrapper never changes emulated memory.
local directory=assert(os.getenv('ISSD_AUTO_OUTPUT_DIR'),'Missing output directory')
assert(os.getenv('ISSD_AUTO_REPLAY_STATE'),'An isolated replay is required')
local out=assert(io.open(directory..'/slide-poses.jsonl','w'))
local function u16(a) return mainmemory.read_u16_le(a) end
local function write_blob(path,size,read)
 local f=assert(io.open(path,'wb'))
 for i=0,size-1 do f:write(string.char(read(i))) end
 f:close()
end
local seen={}
local first_frame=tonumber(os.getenv('ISSD_SLIDE_CAPTURE_AFTER_FRAME') or '0')
assert(first_frame and first_frame>=0,'Invalid capture frame')
local tracked_actor_text=os.getenv('ISSD_SLIDE_CAPTURE_ACTOR')
local tracked_actor=tracked_actor_text and tonumber(tracked_actor_text) or nil
assert(not tracked_actor_text or (tracked_actor and tracked_actor>=0x500 and tracked_actor<=0x1a00 and tracked_actor%0x100==0),'Invalid tracked actor')
local capture_every_frame=os.getenv('ISSD_SLIDE_CAPTURE_EVERY_FRAME')=='1'
local draw_out=assert(io.open(directory..'/slide-draw.jsonl','w'))
local aux_handle=event.onmemoryexecute(function()
 local frame=emu.framecount()
 if frame<first_frame-1 or frame>first_frame+40 then return end
 local okd,dp=pcall(emu.getregister,'D');local oky,y=pcall(emu.getregister,'Y')
 if not okd or not oky or type(dp)~='number' or type(y)~='number' or dp<0 or dp>0xffd0 or y<0 or y>0xffd0 then return end
 draw_out:write(string.format('{"type":"aux_execution","frame":%d,"context":%d,"parent_y":%d,"context_parent":%d,"context_slot":%d,"hair_offset":%d,"context_desc":%d,"parent_desc":%d,"parent_script":%d,"parent_type":%d,"parent_kit_variant":%d,"parent_uniform_selector":%d,"parent_flags":%d,"context_flags":%d}\n',
  frame,dp,y,u16(dp+0x1c),u16(dp+0x1a),u16(dp+0x16),u16(dp+0x14),u16(y+0x14),u16(y+0x1c),mainmemory.read_u8(y+0x30),mainmemory.read_u8(y+0x56),mainmemory.read_u8(y+0x57),mainmemory.read_u8(y+4),u16(dp+4)))
 draw_out:flush()
end,0x98fb86,'issd-slide-hair-aux')
assert(aux_handle,'Unable to register auxiliary capture')
local draw_handle=event.onmemoryexecute(function()
 local frame=emu.framecount()
 if frame<first_frame-1 or frame>first_frame+40 then return end
 local ok,y=pcall(emu.getregister,'Y');local sok,stack=pcall(emu.getregister,'S')
 if not ok or not sok or type(y)~='number' or type(stack)~='number' then return end
 local object=y>=0x1d40 and y<=0x1ffe and tostring(u16(y)) or 'null'
 draw_out:write(string.format('{"frame":%d,"list_y":%d,"object":%s,"stack":%d}\n',frame,y,object,stack))
 local actor=tracked_actor or u16(0x1acc)
 if object==tostring(actor) and actor>=0x500 and actor<=0x1a00 and actor%0x100==0 then
  local pose=u16(actor);local rom_layout=pose>=0x8000
  local function rombyte(addr) return memory.read_u8(0x880000+addr,'System Bus') end
  local count=rom_layout and rombyte(pose) or mainmemory.read_u8(pose)
  assert(count>0 and count<=64 and (rom_layout or pose+count*2<0xa000),'Unsupported geometry')
  local parts={}
  for i=0,count-1 do
   if rom_layout then
    local entry=pose+1+i*4;local dy=rombyte(entry);local dx=rombyte(entry+1);local attr=rombyte(entry+3)
    parts[#parts+1]=string.format('{"dx":%d,"dy":%d,"tile":%d,"attr":%d,"large":%s}',dx<128 and dx or dx+0xff00,dy<128 and dy or dy+0xff00,rombyte(entry+2),attr,tostring(attr%32>=16))
   else
    local entry=pose+i*2
    parts[#parts+1]=string.format('{"dx":%d,"dy":%d,"tile":%d,"attr":%d,"large":%s}',u16(0x2000+entry),u16(0x4000+entry),mainmemory.read_u8(0x6000+entry),mainmemory.read_u8(0x6001+entry),tostring(mainmemory.read_u8(entry+1)>=128))
   end
  end
  draw_out:write(string.format('{"type":"body_geometry","frame":%d,"object":%d,"pose":%d,"descriptor":%d,"script":%d,"source":"%s","draw_x":%d,"draw_y":%d,"draw_z":%d,"tile_base":%d,"object_prop":%d,"object_inherited":%d,"object_flags":%d,"global_prop":%d,"actor_type":%d,"kit_variant":%d,"uniform_selector":%d,"parts":[%s]}\n',frame,actor,pose,u16(actor+0x14),u16(actor+0x1c),rom_layout and 'rom88' or 'wram',u16(actor+8),u16(actor+12),u16(actor+16),u16(actor+2),mainmemory.read_u8(actor+3),mainmemory.read_u8(actor+5),mainmemory.read_u8(actor+4),mainmemory.read_u8(0x7c),mainmemory.read_u8(actor+0x30),mainmemory.read_u8(actor+0x56),mainmemory.read_u8(actor+0x57),table.concat(parts,',')))
 end
 draw_out:flush()
end,0x8095e3,'issd-slide-draw-list')
assert(draw_handle,'Unable to register draw-list capture')
local handle=event.onframeend(function()
 if emu.framecount()<first_frame then return end
 local actor=tracked_actor or u16(0x1acc)
 if actor<0x500 or actor>0x1a00 or actor%0x100~=0 then return end
 local script,descriptor=u16(actor+0x1c),u16(actor+0x14)
 if capture_every_frame then
  if emu.framecount()>first_frame+32 then return end
 elseif script~=0xdb25 and script~=0xdb5b then return end
 local key=string.format('%04X-%04X',script,descriptor)
 if capture_every_frame then key=key..string.format('-%d',emu.framecount()) end
 if seen[key] then return end
 seen[key]=true
 local stem='slide-'..key
 write_blob(directory..'/'..stem..'-mirror.bin',544,function(i)return mainmemory.read_u8(0x1e0+i)end)
 write_blob(directory..'/'..stem..'-vram.bin',65536,function(i)return memory.read_u8(i,'VRAM')end)
 write_blob(directory..'/'..stem..'-cgram.bin',512,function(i)return mainmemory.read_u8(0x2c00+i)end)
 local ppu=pcall(function() write_blob(directory..'/'..stem..'-ppu.bin',544,function(i)return memory.read_u8(i,'OAM')end) end)
 local ppu_cgram=pcall(function() write_blob(directory..'/'..stem..'-ppu-cgram.bin',512,function(i)return memory.read_u8(i,'CGRAM')end) end)
 local screenshot=pcall(client.screenshot,directory..'/'..stem..'-screen.png')
 out:write(string.format('{"frame":%d,"actor":%d,"state":%d,"script":%d,"descriptor":%d,"direction":%d,"pose":%d,"timer":%d,"duration":%d,"cursor":%d,"object_field_02":%d,"obsel":%d,"ppu_available":%s,"ppu_cgram_available":%s,"screenshot":%s,"stem":"%s"}\n',
  emu.framecount(),actor,u16(actor+0x32),script,descriptor,u16(actor+0x2e),u16(actor),u16(actor+0x16),u16(actor+0x18),u16(actor+0x1a),u16(actor+2),mainmemory.read_u8(0x1ea6),tostring(ppu),tostring(ppu_cgram),tostring(screenshot),stem))
 out:flush()
end,'issd-slide-replay-capture')
assert(handle,'Unable to register frame-end capture')
dofile(assert(os.getenv('ISSD_AUTO_PROBE_SCRIPT'),'Missing replay driver'))
out:close()
draw_out:close()
