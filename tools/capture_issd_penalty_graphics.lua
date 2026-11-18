-- Isolated graphics capture around one observed penalty goalkeeper selector sequence.
-- The emulator's ROM and raw capture artifacts remain local.
local root=assert(os.getenv('ISSD_PENALTY_GRAPHICS_DIR'),'Missing graphics output directory')
assert(os.getenv('ISSD_AUTO_FAST_COMPETITION')=='1' and os.getenv('ISSD_AUTO_MENU_MODE')=='world_series' and not os.getenv('ISSD_FORCE_PENALTY_SELECTOR'),'Requires isolated unforced World Series probe')
local out=assert(io.open(root..'/graphics.jsonl','w'))
local expected={28,30,14,16,10}
local target,index,windows=nil,0,{}
local function u(a) return mainmemory.read_u16_le(a) end
local function write_blob(path,size,domain)
 local file=assert(io.open(path,'wb'))
 for i=0,size-1 do file:write(string.char(memory.read_u8(i,domain))) end
 file:close()
end
out:write('{"type":"capture_start"}\n');out:flush()
assert(event.onmemoryexecute(function()
 local dp,a=emu.getregister('D'),emu.getregister('A')%256
 if not target and a==expected[1] and u(dp+0x38)==0x9196 and u(dp+0x14)~=a then target=dp end
 if target and dp==target and index<#expected and a==expected[index+1] and u(dp+0x14)~=a then
  index=index+1
  local frame=emu.framecount()
  windows[#windows+1]={trigger=frame,selector=a,actor=dp,state=u(dp+0x38),index=index}
  out:write(string.format('{"type":"selector","frame":%d,"index":%d,"value":%d,"actor":%d,"state":%d}\n',frame,index,a,dp,u(dp+0x38)));out:flush()
 end
end,0x8c9539,'penalty-graphics-selector'))
assert(event.onframeend(function()
 local frame=emu.framecount()
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
