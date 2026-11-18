-- Isolated graphics capture around one observed penalty goalkeeper selector sequence.
-- The emulator's ROM and raw capture artifacts remain local.
local root=assert(os.getenv('ISSD_PENALTY_GRAPHICS_DIR'),'Missing graphics output directory')
assert(os.getenv('ISSD_AUTO_FAST_COMPETITION')=='1' and os.getenv('ISSD_AUTO_MENU_MODE')=='world_series' and not os.getenv('ISSD_FORCE_PENALTY_SELECTOR'),'Requires isolated unforced World Series probe')
local out=assert(io.open(root..'/graphics.jsonl','w'))
local profile=os.getenv('ISSD_PENALTY_CAPTURE_PROFILE') or 'baseline'
assert(profile=='baseline' or profile=='left' or profile=='right','Invalid capture profile')
assert(profile=='baseline' or os.getenv('ISSD_AUTO_PENALTY_DIRECTION')==({left='Left',right='Right'})[profile],'Direction does not match capture profile')
local expected=profile=='left' and {6,8,10} or (profile=='right' and {6,26,12} or {28,30,14,16,10})
local initial_state=profile=='baseline' and 0x9196 or 0x9366
local target,index,windows=nil,0,{}
local full=os.getenv('ISSD_PENALTY_FULL_GRAPHICS')=='1'
local function u(a) return mainmemory.read_u16_le(a) end
local function write_blob(path,size,domain)
 local file=assert(io.open(path,'wb'))
 for i=0,size-1 do file:write(string.char(memory.read_u8(i,domain))) end
 file:close()
end
out:write('{"type":"capture_start"}\n');out:flush()
assert(event.onmemoryexecute(function()
 local dp,a=emu.getregister('D'),emu.getregister('A')%256
 if not target and a==expected[1] and u(dp+0x38)==initial_state and u(dp+0x14)~=a then target=dp end
 if target and dp==target and index<#expected and a==expected[index+1] and u(dp+0x14)~=a then
  index=index+1
  local frame=emu.framecount()
  windows[#windows+1]={trigger=frame,selector=a,actor=dp,state=u(dp+0x38),index=index}
  out:write(string.format('{"type":"selector","frame":%d,"index":%d,"value":%d,"actor":%d,"state":%d}\n',frame,index,a,dp,u(dp+0x38)));out:flush()
 end
end,0x8c9539,'penalty-graphics-selector'))
assert(event.onmemoryexecute(function()
 if not target then return end
 local frame=emu.framecount()
 if frame<windows[1].trigger or frame>windows[1].trigger+40 then return end
 local y=emu.getregister('Y')
 if y<0x1d40 or y>0x1ffe then return end
 local object=u(y)
 if object>0xffc8 then return end
 out:write(string.format('{"type":"draw_entry","frame":%d,"list_y":%d,"object":%d,"stack":%d,"linked_object":%d,"object_field_00":%d,"object_field_02":%d,"object_field_14":%d,"object_state":%d}\n',frame,y,object,emu.getregister('S'),u(object+0x36),u(object),u(object+2),u(object+0x14),u(object+0x38)));out:flush()
end,0x8095e3,'penalty-graphics-draw'))
assert(event.onframeend(function()
 local frame=emu.framecount()
 if full and target then
  local delta=frame-windows[1].trigger
  if delta>=1 and delta<=40 then
   local stem=string.format('full-%02d',delta)
   local vram=pcall(write_blob,root..'/'..stem..'-vram.bin',65536,'VRAM')
   local oam=pcall(write_blob,root..'/'..stem..'-oam.bin',544,'OAM')
   local cgram=pcall(write_blob,root..'/'..stem..'-cgram.bin',512,'CGRAM')
   local screenshot=pcall(client.screenshot,root..'/'..stem..'.png')
   out:write(string.format('{"type":"full_graphics","frame":%d,"delta":%d,"actor":%d,"obsel":%d,"vram":%s,"oam":%s,"cgram":%s,"screenshot":%s,"stem":"%s"}\n',frame,delta,target,mainmemory.read_u8(0x1ea6),tostring(vram),tostring(oam),tostring(cgram),tostring(screenshot),stem));out:flush()
  end
 end
 for _,window in ipairs(windows) do
  local delta=frame-window.trigger
  if delta>=0 and delta<=2 then
   local stem=string.format('selector-%02d-delta-%d',window.index,delta)
   local vram=pcall(write_blob,root..'/'..stem..'-vram.bin',65536,'VRAM')
   local oam=pcall(write_blob,root..'/'..stem..'-oam.bin',544,'OAM')
   local cgram=pcall(write_blob,root..'/'..stem..'-cgram.bin',512,'CGRAM')
   local screenshot=pcall(client.screenshot,root..'/'..stem..'.png')
   out:write(string.format('{"type":"graphics","frame":%d,"delta":%d,"trigger":%d,"selector":%d,"index":%d,"actor":%d,"state":%d,"obsel":%d,"vram":%s,"oam":%s,"cgram":%s,"screenshot":%s,"stem":"%s"}\n',frame,delta,window.trigger,window.selector,window.index,window.actor,window.state,mainmemory.read_u8(0x1ea6),tostring(vram),tostring(oam),tostring(cgram),tostring(screenshot),stem));out:flush()
  end
 end
end,'penalty-graphics-frame'))
local ok,problem=xpcall(function() dofile(assert(os.getenv('ISSD_PENALTY_MODE_PROBE'))) end,debug.traceback)
if not ok then
 local message=tostring(problem):match('^[^\r\n]*'):gsub('\\','\\\\'):gsub('"','\\"')
 out:write('{"type":"error","detail":"'..message..'"}\n')
end
out:write(string.format('{"type":"capture_end","sequence_count":%d}\n',index));out:close()
