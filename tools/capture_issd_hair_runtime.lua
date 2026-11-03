-- Read-only auxiliary hair-context trace from an isolated replay state.
local root=assert(os.getenv('ISSD_HAIR_RUNTIME_DIR'),'Missing output directory')
local state=assert(os.getenv('ISSD_HAIR_GEOMETRY_STATE'),'Missing isolated replay state')
assert(savestate.load(state,true),'Unable to load replay state')
local out=assert(io.open(root..'/hair-runtime.jsonl','w'))
local function u16(a) return mainmemory.read_u16_le(a) end
local function reg(n)local ok,v=pcall(emu.getregister,n);return ok and type(v)=='number' and v or -1 end
if os.getenv('ISSD_HAIR_SYNTHETIC_POSITION')=='1' then
 local parent=0x1700;local anchor=u16(0x1acc)
 assert(anchor>=0x0500 and anchor<=0x1a00 and anchor%0x100==0,'Invalid controlled actor')
 local oldx,oldy=u16(parent+8),u16(parent+12)
 local dx=tonumber(os.getenv('ISSD_HAIR_POSITION_DX') or '40')
 local dy=tonumber(os.getenv('ISSD_HAIR_POSITION_DY') or '0')
 assert(dx and dx%1==0 and dx>=-256 and dx<=256 and dy and dy%1==0 and dy>=-256 and dy<=256,'Invalid synthetic position offset')
 local newx=(u16(anchor+8)+dx)%0x10000;local newy=(u16(anchor+12)+dy)%0x10000
 mainmemory.write_u16_le(parent+8,newx);mainmemory.write_u16_le(parent+12,newy)
 mainmemory.write_u16_le(parent+6,u16(anchor+6));mainmemory.write_u16_le(parent+10,u16(anchor+10))
 out:write(string.format('{"type":"synthetic_position","actor":%d,"anchor":%d,"old_x":%d,"old_y":%d,"new_x":%d,"new_y":%d}\n',parent,anchor,oldx,oldy,newx,newy))
end
local step=0
local ok,handle=pcall(event.onmemoryexecute,function()
 local dp,y=reg('D'),reg('Y')
 if dp<0 or dp>0xffd0 or y<0 or y>0xffd0 then return end
 out:write(string.format('{"type":"aux_execution","step":%d,"frame":%d,"context":%d,"parent_y":%d,"context_parent":%d,"context_slot":%d,"hair_offset":%d,"context_desc":%d,"parent_desc":%d,"parent_script":%d,"parent_type":%d,"context_flags":%d}\n',
  step,emu.framecount(),dp,y,u16(dp+0x1c),u16(dp+0x1a),u16(dp+0x16),u16(dp+0x14),u16(y+0x14),u16(y+0x1c),mainmemory.read_u8(y+0x30),u16(dp+4)))
end,0x98FB86,'issd-hair-aux')
local h=tostring(handle)
out:write(string.format('{"type":"hook","success":%s}\n',tostring(ok and handle~=nil and h~='00000000-0000-0000-0000-000000000000')))
local dok,draw=pcall(event.onmemoryexecute,function()
 if step<7 or step>25 then return end
 local y=reg('Y');local object=(y>=0x1d40 and y<=0x1ffe) and u16(y) or -1
 out:write(string.format('{"type":"draw_entry","step":%d,"frame":%d,"list_y":%d,"object":%d,"stack":%d}\n',
  step,emu.framecount(),y,object,reg('S')))
end,0x8095E3,'issd-hair-draw')
local dh=tostring(draw)
out:write(string.format('{"type":"draw_hook_registration","success":%s}\n',tostring(dok and draw~=nil and dh~='00000000-0000-0000-0000-000000000000')))
local function dump(path,count,reader)
 local f=assert(io.open(path,'wb'))
 for n=0,count-1 do f:write(string.char(reader(n))) end
 f:close()
end
for i=1,120 do
 step=i;joypad.set({},1);joypad.set({},2);emu.frameadvance()
 if i>=7 and i<=26 then
  local stem=string.format('%s/frame-%03d',root,i)
  dump(stem..'-mirror.bin',544,function(n)return mainmemory.read_u8(0x1e0+n) end)
  dump(stem..'-oam.bin',544,function(n)return memory.read_u8(n,'OAM') end)
  dump(stem..'-vram.bin',65536,function(n)return memory.read_u8(n,'VRAM') end)
  dump(stem..'-cgram.bin',512,function(n)return memory.read_u8(n,'CGRAM') end)
  local okshot=pcall(client.screenshot,stem..'.png')
  out:write(string.format('{"type":"graphics","step":%d,"frame":%d,"obsel":%d,"context":3024,"parent":%d,"context_desc":%d,"parent_desc":%d,"screenshot":%s}\n',
   i,emu.framecount(),mainmemory.read_u8(0x1ea6),u16(0x0bd0+0x1c),u16(0x0bd0+0x14),u16(0x1700+0x14),tostring(okshot)))
 end
 for _,c in ipairs({0x0aa0,0x0ad0,0x0ba0,0x0bd0,0x0ca0,0x0cd0}) do
  local parent=u16(c+0x1c);local slot=u16(c+0x1a);local desc=u16(c+0x14)
  if parent~=0 and desc>=0x8000 and slot<0x200 then
   local address=(0xc000+slot*32)%0x10000;local bytes={}
   for n=0,31 do bytes[#bytes+1]=string.format('%02x',memory.read_u8((address+n)%0x10000,'VRAM')) end
   out:write(string.format('{"type":"vram","step":%d,"frame":%d,"context":%d,"parent":%d,"slot":%d,"hair_offset":%d,"descriptor":%d,"vram_offset":%d,"bytes":"%s"}\n',
    i,emu.framecount(),c,parent,slot,u16(c+0x16),desc,address,table.concat(bytes)))
  end
 end
 if i==1 or i==60 or i==120 then
  for _,c in ipairs({0x0aa0,0x0ad0,0x0ba0,0x0bd0,0x0ca0,0x0cd0}) do
   local parent=u16(c+0x1c)
   out:write(string.format('{"type":"context","step":%d,"context":%d,"parent":%d,"slot":%d,"hair_offset":%d,"descriptor":%d}\n',
    i,c,parent,u16(c+0x1a),u16(c+0x16),u16(c+0x14)))
  end
  if i==60 then
   local file=assert(io.open(root..'/oam-step60.bin','wb'))
   for n=0,543 do file:write(string.char(memory.read_u8(n,'OAM'))) end
   file:close()
  end
 end
end
joypad.set({},1);joypad.set({},2)
out:write('{"type":"session_end","steps":120}\n');out:close()
