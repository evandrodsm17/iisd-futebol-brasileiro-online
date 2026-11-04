-- Read-only execution trace of the original slide actor and ball-link writes.
local directory=assert(os.getenv('ISSD_AUTO_OUTPUT_DIR'),'Missing output directory')
assert(os.getenv('ISSD_AUTO_REPLAY_STATE'),'Isolated replay required')
local output=assert(io.open(directory..'/slide-contact-route.jsonl','w'))
local actor=assert(tonumber(os.getenv('ISSD_SLIDE_TRACE_ACTOR') or '3328'))
local first=assert(tonumber(os.getenv('ISSD_SLIDE_TRACE_START_FRAME') or '4274'))
local last=assert(tonumber(os.getenv('ISSD_SLIDE_TRACE_END_FRAME') or '4305'))
assert(actor>=0x500 and actor<=0x1a00 and actor%0x100==0,'Invalid actor')
assert(first>=0 and last>=first,'Invalid trace window')
local function u16(a)return mainmemory.read_u16_le(a)end
local function reg(n)local ok,v=pcall(emu.getregister,n);return ok and type(v)=='number' and v or -1 end
local sites={
 [0x84a736]='jump_entry',[0x84a744]='jump_setup',[0x84a77b]='jump_update',[0x84a7a4]='jump_landing',[0x84a346]='reaction_dispatch',
 [0x84a08d]='slide_handler',[0x84e8b0]='proximity_entry',
 [0x84e8e4]='proximity_return',[0x84e8e5]='proximity_clear',[0x84e8e7]='proximity_set',
 [0x98fe8d]='player_overlap_entry',[0x98fedf]='player_overlap_return',
 [0x80eed3]='opponent_condition_entry',
 [0x85f11a]='ball_gate_entry',[0x85f125]='contact_alternative',[0x85f12a]='contact_result',
 [0x85f137]='opponent_response',[0x85f178]='link_path',[0x85f18e]='prepare_link',
 [0x85f192]='store_link',[0x85f195]='after_link',[0x85f199]='alternate_path',
 [0x85f8b9]='reset_link_entry',[0x85f8d9]='clear_link',[0x85f8dc]='after_clear_link'
}
for address,label in pairs(sites) do
 assert(event.onmemoryexecute(function()
  local frame=emu.framecount();if frame<first or frame>last then return end
  local dp=reg('D');local target=u16(0xa6);if target==0 then target=u16(0xa4) end;if dp~=actor and address~=0x85f8b9 and address~=0x85f8d9 and address~=0x85f8dc then return end
  output:write(string.format('{"frame":%d,"site":"%s","address":%d,"dp":%d,"a":%d,"x":%d,"y":%d,"p":%d,"selected":%d,"actor":%d,"state":%d,"script":%d,"flags":%d,"timer":%d,"link_a6":%d,"ball_xyz":[%d,%d,%d],"ball_velocity":[%d,%d,%d],"actor_xy":[%d,%d],"offset_xy":[%d,%d],"target":%d,"target_xy":[%d,%d],"target_flags":%d,"actor_z":%d,"actor_vz":%d,"actor_collision":%d,"actor_source":%d,"actor_reaction":%d}\n',
   frame,label,address,dp,reg('A'),reg('X'),reg('Y'),reg('P'),u16(0x1acc),actor,u16(actor+0x32),u16(actor+0x1c),u16(actor+0x6e),u16(actor+0x70),u16(0xa6),u16(0x408),u16(0x40c),u16(0x410),u16(0x424),u16(0x428),u16(0x436),u16(actor+8),u16(actor+12),u16(actor+0x38),u16(actor+0x3a),target,u16(target+8),u16(target+12),u16(target+0x6c),u16(actor+0x10),u16(actor+0x34),u16(actor+0x6c),u16(actor+0x76),u16(actor+0x78)))
  output:flush()
 end,address,'slide-contact-'..label),'Could not register '..label)
end
dofile(assert(os.getenv('ISSD_AUTO_GATE_SCRIPT'),'Missing gate observer'))
output:close()
