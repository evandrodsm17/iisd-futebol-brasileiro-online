-- Replays a user-supplied scenario save in an isolated BizHawk instance.
-- The ROM and savestate are read only; outputs go to the caller's directory.
local state=assert(os.getenv('ISSD_THROW_STATE'),'ISSD_THROW_STATE ausente')
local output=assert(os.getenv('ISSD_THROW_OUTPUT'),'ISSD_THROW_OUTPUT ausente'):gsub('\\','/')
local button=os.getenv('ISSD_THROW_BUTTON') or 'NEUTRAL'
assert(button=='NEUTRAL' or button=='A' or button=='B' or button=='X' or button=='Y','Bot?o inv?lido')
local direction=os.getenv('ISSD_THROW_DIRECTION') or 'NEUTRAL'
assert(direction=='NEUTRAL' or direction=='Up' or direction=='Down' or direction=='Left' or direction=='Right','Invalid direction')
local graphics=os.getenv('ISSD_THROW_GRAPHICS')=='1'
local direction_start=tonumber(os.getenv('ISSD_THROW_DIRECTION_START') or '60')
assert(direction_start and direction_start>=0 and direction_start<66,'Invalid direction start')
local out=assert(io.open(output..'/trace.jsonl','w'))
local gout=graphics and assert(io.open(output..'/graphics.jsonl','w')) or nil
assert(savestate.load(state,true),'N?o foi poss?vel carregar estado')
local function u16(address)return mainmemory.read_u16_le(address)end
local thrower=u16(0xA6)
assert(thrower>=0x0500 and thrower<=0x1A00 and thrower%0x100==0,'Invalid thrower')
local function write_blob(path,size,read)
 local file=assert(io.open(path,'wb'))
 for i=0,size-1 do file:write(string.char(read(i))) end
 file:close()
end
local function capture_graphics(step)
 if not gout or step<55 or step>85 then return end
 local name=string.format('throw-%03d',step)
 local prefix=output..'/'..name
 write_blob(prefix..'-mirror.bin',544,function(i)return mainmemory.read_u8(0x1E0+i)end)
 write_blob(prefix..'-vram.bin',65536,function(i)return memory.read_u8(i,'VRAM')end)
 local ppu=pcall(function()write_blob(prefix..'-ppu.bin',544,function(i)return memory.read_u8(i,'OAM')end)end)
 local cgppu=pcall(function()write_blob(prefix..'-ppu-cgram.bin',512,function(i)return memory.read_u8(i,'CGRAM')end)end)
 local cg=assert(io.open(prefix..'-cgram.hex','w'))
 for i=0,511 do cg:write(string.format('%02X',mainmemory.read_u8(0x2C00+i))) end
 cg:close()
 local shot=pcall(client.screenshot,prefix..'-screen.png')
 gout:write(string.format('{"schema":"issd-native-action-oam/v1","frame":%d,"step":%d,"obsel":%d,"oam_mirror":"%s-mirror.bin","oam_mirror_encoding":"low-512-reversed-high-32-forward","oam_ppu":%s,"vram":"%s-vram.bin","cgram":"%s-cgram.hex","cgram_ppu":%s,"screenshot":%s,"actor":{"address":%d,"animation_script":%d,"direction":%d,"descriptor":%d,"pose":%d,"animation_timer":%d,"animation_duration":%d,"animation_cursor":%d,"object_field_02":%d,"origin_x_raw":%d,"origin_y_raw":%d,"origin_y_offset_raw":%d,"object_flags":%d,"type":%d}}\n',emu.framecount(),step,mainmemory.read_u8(0x1EA6),name,ppu and ('"'..name..'-ppu.bin"') or 'null',name,name,cgppu and ('"'..name..'-ppu-cgram.bin"') or 'null',shot and ('"'..name..'-screen.png"') or 'null',thrower,u16(thrower+0x1C),u16(thrower+0x2E),u16(thrower+0x14),u16(thrower),u16(thrower+0x16),u16(thrower+0x18),u16(thrower+0x1A),u16(thrower+0x02),u16(thrower+0x08),u16(thrower+0x0C),u16(thrower+0x10),mainmemory.read_u8(thrower+0x04),mainmemory.read_u8(thrower+0x30)))
 gout:flush()
end
for step=0,149 do
 local input={}
 if step>=60 and step<66 then
  if button~='NEUTRAL' then input[button]=true end
 end
 if step>=direction_start and step<66 and direction~='NEUTRAL' then input[direction]=true end
 joypad.set(input,1);emu.frameadvance()
 capture_graphics(step)
 local actors={}
 for address=0x0500,0x1A00,0x100 do
  actors[#actors+1]=string.format('{"address":%d,"type":%d,"state":%d,"script":%d,"descriptor":%d,"direction":%d,"x":%d,"y":%d}',address,mainmemory.read_u8(address+0x30),u16(address+0x32),u16(address+0x1C),u16(address+0x14),u16(address+0x2E),u16(address+0x08),u16(address+0x0C))
 end
 out:write(string.format('{"step":%d,"frame":%d,"button":"%s","held_p1":%d,"a4":%d,"a6":%d,"controlled":%d,"phase":%d,"ball":{"x":%d,"y":%d,"z":%d,"vx":%d,"vy":%d,"vz":%d,"type":%d},"actors":[%s]}\n',step,emu.framecount(),button,u16(0x20),u16(0xA4),u16(0xA6),u16(0x1AFC),u16(0xC0),u16(0x408),u16(0x40C),u16(0x410),u16(0x424),u16(0x428),u16(0x436),u16(0x430),table.concat(actors,',')))
 if step>=50 and step<=110 and step%2==0 then pcall(client.screenshot,output..string.format('/frame-%03d.png',step)) end
 if step%30==0 then out:flush() end
end
if gout then gout:close() end
joypad.set({},1);out:write('{"type":"done"}\n');out:close()
