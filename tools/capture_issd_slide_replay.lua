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
local draw_out=assert(io.open(directory..'/slide-draw.jsonl','w'))
local draw_handle=event.onmemoryexecute(function()
 local frame=emu.framecount()
 if frame<first_frame-1 or frame>first_frame+40 then return end
 local ok,y=pcall(emu.getregister,'Y');local sok,stack=pcall(emu.getregister,'S')
 if not ok or not sok or type(y)~='number' or type(stack)~='number' then return end
 local object=y>=0x1d40 and y<=0x1ffe and tostring(u16(y)) or 'null'
 draw_out:write(string.format('{"frame":%d,"list_y":%d,"object":%s,"stack":%d}\n',frame,y,object,stack))
 draw_out:flush()
end,0x8095e3,'issd-slide-draw-list')
assert(draw_handle,'Unable to register draw-list capture')
local handle=event.onframeend(function()
 if emu.framecount()<first_frame then return end
 local actor=u16(0x1acc)
 if actor<0x500 or actor>0x1a00 or actor%0x100~=0 then return end
 local script,descriptor=u16(actor+0x1c),u16(actor+0x14)
 if script~=0xdb25 and script~=0xdb5b then return end
 local key=string.format('%04X-%04X',script,descriptor)
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
