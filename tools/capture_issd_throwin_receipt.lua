-- Record native ball links and contact checks during an isolated replay.
local out=assert(io.open(assert(os.getenv('ISSD_THROW_OUTPUT'))..'/receive-hooks.jsonl','w'))
local driver=assert(os.getenv('ISSD_THROW_DRIVER'),'Missing replay driver')
local function u16(a)return mainmemory.read_u16_le(a)end
local function reg(name)local ok,v=pcall(emu.getregister,name);return ok and type(v)=='number' and v or -1 end
local function write(kind,label)
 local frame=emu.framecount()
 if frame<2290 or frame>2350 then return end
 local d=reg('D');local valid=d>=0x500 and d<=0x1a00 and d%0x100==0
 out:write(string.format('{"kind":"%s","label":"%s","frame":%d,"pc":%d,"pb":%d,"d":%d,"a":%d,"x":%d,"y":%d,"carry":%d,"link_a6":%d,"ball_type":%d,"ball_x":%d,"ball_y":%d,"ball_z":%d,"actor_x":%d,"actor_y":%d,"actor_z":%d,"actor_team":%d,"actor_field68":%d}\n',kind,label,frame,reg('PC'),reg('PB'),d,reg('A'),reg('X'),reg('Y'),reg('Flag C'),u16(0xa6),u16(0x430),u16(0x408),u16(0x40c),u16(0x410),valid and u16(d+8) or 0,valid and u16(d+12) or 0,valid and u16(d+16) or 0,valid and u16(d+0x9a) or 0,valid and u16(d+0x68) or 0))
end
for _,e in ipairs({{0x84E8B0,'84E8B0'},{0x84E8BD,'84E8BD'},{0x84E8E4,'84E8E4'},{0x84E8E7,'84E8E7'},{0x84E8E9,'84E8E9'},{0x84E902,'84E902'},{0x84E91E,'84E91E'},{0x8486E2,'8486E2'},{0x84BCDA,'84BCDA'},{0x84C24A,'84C24A'},{0x85F11A,'85F11A'}}) do
 local address,label=e[1],e[2]
 assert(event.onmemoryexecute(function()write('exec',label)end,address,'throw-receive-'..label))
end
for _,e in ipairs({{0x00A6,'a6-low'},{0x7E00A6,'a6-wram-low'},{0x0430,'type-low'},{0x7E0430,'type-wram-low'}}) do
 local address,label=e[1],e[2]
 assert(event.onmemorywrite(function()write('write',label)end,address,'throw-receive-'..label,'System Bus'))
end
dofile(driver);out:write('{"kind":"done"}\n');out:close()
