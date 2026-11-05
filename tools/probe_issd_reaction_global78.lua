-- Read-only observation of writes to global $0078 during an isolated replay.
local directory=assert(os.getenv('ISSD_AUTO_OUTPUT_DIR'),'Missing output directory')
assert(os.getenv('ISSD_AUTO_REPLAY_STATE'),'An isolated replay is required')
local out=assert(io.open(directory..'/reaction-global78.jsonl','w'))
local first=tonumber(os.getenv('ISSD_REACTION_START_FRAME') or '4210')
local last=tonumber(os.getenv('ISSD_REACTION_END_FRAME') or '4221')
local function u16(a)return mainmemory.read_u16_le(a)end
local function reg(n)local ok,v=pcall(emu.getregister,n);return ok and type(v)=='number' and v or -1 end
for _,address in ipairs({0x0078,0x7e0078})do
 assert(event.onmemorywrite(function()
  local frame=emu.framecount();if frame<first or frame>last then return end
  out:write(string.format('{"frame":%d,"site":"write","watch":%d,"pb":%d,"pc":%d,"d":%d,"a":%d,"x":%d,"y":%d,"p":%d,"value":%d,"addend":%d,"random_a":%d,"random_b":%d}\n',frame,address,reg('PB'),reg('PC'),reg('D'),reg('A'),reg('X'),reg('Y'),reg('P'),u16(0x78),u16(0x3a),u16(0x1fea),u16(0x1fec)))
  out:flush()
 end,address,string.format('issd-global78-%06X',address),'System Bus'),'Could not register global write')
end
assert(event.onmemoryexecute(function()
 local frame=emu.framecount();if frame<first or frame>last or reg('D')~=0xd00 or reg('X')~=0x1900 then return end
 out:write(string.format('{"frame":%d,"site":"reaction","value":%d,"addend":%d,"random_a":%d,"random_b":%d}\n',frame,u16(0x78),u16(0x3a),u16(0x1fea),u16(0x1fec)));out:flush()
end,0x80eed3,'issd-global78-reaction'),'Could not register reaction')
dofile(assert(os.getenv('ISSD_AUTO_PROBE_SCRIPT'),'Missing replay driver'))
out:close()
