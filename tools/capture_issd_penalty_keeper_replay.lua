-- Capture locally replayed goalkeeper graphics after a synthetic two-player setup.
local root=assert(os.getenv('ISSD_PENALTY_GRAPHICS_DIR'))
local direction=assert(os.getenv('ISSD_PENALTY_REPLAY_DIRECTION'))
assert((direction=='Left' or direction=='Right') and os.getenv('ISSD_PENALTY_REPLAY_CONTROLLER')=='p2' and os.getenv('ISSD_PENALTY_REPLAY_PLAYERS_OVERRIDE')=='4' and os.getenv('ISSD_PENALTY_REPLAY_P2_ACTION_START')=='955' and os.getenv('ISSD_PENALTY_REPLAY_P2_ACTION_SECOND')=='1455','Unexpected synthetic replay')
local out=assert(io.open(root..'/graphics.jsonl','w'))
local expected={28,30,14,16,10}
local trigger,target,index=nil,nil,0
local function u(a) return mainmemory.read_u16_le(a) end
local function write_blob(path,size,domain)
 local f=assert(io.open(path,'wb'))
 for i=0,size-1 do f:write(string.char(memory.read_u8(i,domain))) end
 f:close()
end
out:write(string.format('{"type":"capture_start","direction":"%s","synthetic_players":true}\n',direction));out:flush()
assert(event.onmemoryexecute(function()
 local dp,a=emu.getregister('D'),emu.getregister('A')%256
 if u(0x1440)~=0 or u(0x1704)~=1 then return end
 if not target and a==expected[1] and u(dp+0x14)~=a then target=dp;trigger=emu.framecount() end
 if target and dp==target and index<#expected and a==expected[index+1] and u(dp+0x14)~=a then
  index=index+1
  out:write(string.format('{"type":"selector","frame":%d,"index":%d,"value":%d,"actor":%d,"state":%d,"linked_object":%d}\n',emu.framecount(),index,a,dp,u(dp+0x38),u(dp+0x36)));out:flush()
 end
end,0x8c9539,'keeper-replay-selector'))
assert(event.onmemoryexecute(function()
 if not trigger then return end
 local frame=emu.framecount();if frame<trigger or frame>trigger+40 then return end
 local y=emu.getregister('Y');if y<0x1d40 or y>0x1ffe then return end
 local object=u(y);if object>0xffc8 then return end
 out:write(string.format('{"type":"draw_entry","frame":%d,"list_y":%d,"object":%d,"stack":%d,"linked_object":%d,"object_field_00":%d,"object_field_02":%d,"object_field_14":%d,"object_state":%d,"object_x":%d,"object_y":%d,"object_height":%d}\n',frame,y,object,emu.getregister('S'),u(object+0x36),u(object),u(object+2),u(object+0x14),u(object+0x38),u(object+8),u(object+0xc),u(object+0x10)));out:flush()
end,0x8095e3,'keeper-replay-draw'))
assert(event.onframeend(function()
 if not trigger then return end
 local frame=emu.framecount();local delta=frame-trigger
 if delta<1 or delta>40 then return end
 local stem=string.format('full-%02d',delta)
 local vram=pcall(write_blob,root..'/'..stem..'-vram.bin',65536,'VRAM')
 local oam=pcall(write_blob,root..'/'..stem..'-oam.bin',544,'OAM')
 local cgram=pcall(write_blob,root..'/'..stem..'-cgram.bin',512,'CGRAM')
 local screenshot=pcall(client.screenshot,root..'/'..stem..'.png')
 out:write(string.format('{"type":"full_graphics","frame":%d,"delta":%d,"actor":%d,"obsel":%d,"vram":%s,"oam":%s,"cgram":%s,"screenshot":%s,"stem":"%s"}\n',frame,delta,target,mainmemory.read_u8(0x1ea6),tostring(vram),tostring(oam),tostring(cgram),tostring(screenshot),stem));out:flush()
end,'keeper-replay-frame'))
local ok,problem=xpcall(function() dofile(assert(os.getenv('ISSD_PENALTY_MODE_PROBE'))) end,debug.traceback)
if not ok then
 local message=tostring(problem):match('^[^\r\n]*'):gsub('\\','\\\\'):gsub('"','\\"')
 out:write('{"type":"error","detail":"'..message..'"}\n')
end
out:write(string.format('{"type":"capture_end","sequence_count":%d}\n',index));out:close()
