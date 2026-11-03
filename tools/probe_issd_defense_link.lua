-- Passive instruction probes around the link update in the defensive path.
local directory=assert(os.getenv('ISSD_AUTO_OUTPUT_DIR'),'Missing output directory')
assert(os.getenv('ISSD_AUTO_REPLAY_STATE'),'An isolated replay is required')
local out=assert(io.open(directory..'/defense-link.jsonl','w'))
local function u16(a) return mainmemory.read_u16_le(a) end
local function reg(name) local ok,value=pcall(emu.getregister,name); return ok and type(value)=='number' and value or -1 end
local locations={
 [0x85f11a]='contact_entry', [0x85f125]='contact_alternative',
 [0x85f12a]='contact_result', [0x85f137]='opponent_response',
 [0x85f178]='link_path', [0x85f18e]='prepare_link',
 [0x85f192]='store_link', [0x85f195]='after_link', [0x85f199]='alternate_path',
 [0x85f8d6]='reset_link_context', [0x85f8d9]='clear_link', [0x85f8dc]='after_clear_link'
}
for address,label in pairs(locations) do
 assert(event.onmemoryexecute(function()
  local actor=reg('D')
  if actor~=u16(0x1acc) or actor<0x0500 or actor>0x1a00 or actor%0x100~=0 then return end
  out:write(string.format('{"frame":%d,"site":"%s","actor":%d,"a":%d,"x":%d,"y":%d,"p":%d,"link_a6":%d,"link_a4":%d,"state":%d,"script":%d,"f6e":%d,"ball_xyz":[%d,%d,%d]}\n',
   emu.framecount(),label,actor,reg('A'),reg('X'),reg('Y'),reg('P'),u16(0xa6),u16(0xa4),u16(actor+0x32),u16(actor+0x1c),u16(actor+0x6e),u16(0x408),u16(0x40c),u16(0x410)))
  out:flush()
 end,address,'issd-defense-link-'..label),'Hook registration failed: '..label)
end
dofile(assert(os.getenv('ISSD_AUTO_GATE_SCRIPT'),'Missing gate probe'))
out:close()
