-- Isolated synthetic shootout: record the object state on both sides of 8C:A500.
local output=assert(os.getenv('ISSD_PENALTY_RESPONSE_OUTPUT'))
local automation=assert(os.getenv('ISSD_INIT_AUTOMATION'))
assert(os.getenv('ISSD_AUTO_FAST_COMPETITION')=='1' and os.getenv('ISSD_AUTO_MENU_MODE')=='world_series' and os.getenv('ISSD_AUTO_PENALTY_DIRECTION')=='Right' and os.getenv('ISSD_AUTO_PENALTY_CONTROLLER')=='p1','Unexpected capture configuration')
local out=assert(io.open(output,'w'))
local pending=nil
local function u(a)return mainmemory.read_u16_le(a)end
local function u24(a)return u(a)+mainmemory.read_u8(a+2)*65536 end
local function reg(n)local ok,v=pcall(emu.getregister,n);return ok and type(v)=='number' and v or -1 end
out:write('{"site":"session_start"}\n');out:flush();client.speedmode(800)
assert(event.onmemoryexecute(function()
 local d=reg('D');assert(not pending and d>=0 and d<=0xffc8,'Unexpected contact context')
 local peer=u(d+0x36);assert(peer<=0xffc8,'Unexpected linked object')
 local target=u(peer+0x1a);local source=u(0x1702)
 assert(target<=0xffc8 and source<=0xffc8,'Unexpected motion pointers')
 pending={frame=emu.framecount(),target=target,peer=peer,source=source}
 out:write(string.format('{"site":"before","frame":%d,"side":%d,"round":%d,"contact":%d,"peer":%d,"target":%d,"source":%d,"peer_y":%d,"target_y":%d,"target_vx":%d,"target_vy":%d,"target_vz":%d,"source_vx":%d,"source_vz":%d,"flags":%d}\n',pending.frame,u(0x1440),u(0x1704),d,peer,target,source,u(peer+0xc),u24(target+0xb),u24(target+0x28),u24(target+0x32),u24(target+0x2b),u24(source+0x28),u24(source+0x2b),u(0x14aa)));out:flush()
end,0x8ca500,'penalty-response-before'))
assert(event.onmemoryexecute(function()
 assert(pending and pending.frame==emu.framecount() and reg('X')==pending.target,'Contact response mismatch')
 local target=pending.target
 out:write(string.format('{"site":"after","frame":%d,"side":%d,"round":%d,"target":%d,"target_y":%d,"target_vx":%d,"target_vy":%d,"target_vz":%d,"flags":%d}\n',pending.frame,u(0x1440),u(0x1704),target,u24(target+0xb),u24(target+0x28),u24(target+0x32),u24(target+0x2b),u(0x14aa)));out:flush();pending=nil
end,0x8ca56b,'penalty-response-after'))
local ok,problem=xpcall(function()dofile(automation)end,debug.traceback)
if not ok then local message=tostring(problem):match('^[^\r\n]*'):gsub('\\','\\\\'):gsub('"','\\"');out:write('{"site":"error","detail":"'..message..'"}\n') end
if pending then out:write('{"site":"error","detail":"unfinished response"}\n') end
out:write('{"site":"session_end"}\n');out:close();client.exit()
