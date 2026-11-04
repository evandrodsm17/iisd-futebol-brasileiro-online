-- Read-only opponent and ball trace around the paired Right/A replay.
local directory=assert(os.getenv('ISSD_AUTO_OUTPUT_DIR'),'Missing output directory')
assert(os.getenv('ISSD_AUTO_REPLAY_STATE'),'An isolated replay is required')
local out=assert(io.open(directory..'/defense-opponent.jsonl','w'))
local final_frame=tonumber(os.getenv('ISSD_OPPONENT_END_FRAME') or '4380')
assert(final_frame and final_frame>=4380 and final_frame<=5000,'Invalid observation end frame')
local function u16(a)return mainmemory.read_u16_le(a)end
local function reg(n)local ok,v=pcall(emu.getregister,n);return ok and type(v)=='number' and v or -1 end
local function actor(a)
 return string.format('{"address":%d,"state":%d,"script":%d,"descriptor":%d,"x":%d,"y":%d,"z":%d,"direction":%d,"f6e":%d,"f70":%d,"f76":%d,"f78":%d}',
  a,u16(a+0x32),u16(a+0x1c),u16(a+0x14),u16(a+8),u16(a+12),u16(a+16),u16(a+0x2e),u16(a+0x6e),u16(a+0x70),u16(a+0x76),u16(a+0x78))
end
local function record(kind,site)
 local frame=emu.framecount();if frame<4274 or frame>final_frame then return end
 out:write(string.format('{"type":"%s","site":"%s","frame":%d,"d":%d,"xreg":%d,"a":%d,"p":%d,"link_a6":%d,"phase":%d,"phase_c2":%d,"restart_c4":%d,"restart_c6":%d,"restart_ca":%d,"restart_ce":%d,"selected_11e8":%d,"clock_16d0":%d,"a4":%d,"foul_setting":%d,"referee":%d,"global_78":%d,"global_11fa":%d,"foul_00ba":%d,"event_19d2":%d,"event_12f6":%d,"card_12de":%d,"ball_04de":%d,"player":%s,"opponent":%s,"ball":{"x":%d,"y":%d,"z":%d,"type":%d}}\n',
  kind,site,frame,reg('D'),reg('X'),reg('A'),reg('P'),u16(0xa6),u16(0xc0),u16(0xc2),u16(0xc4),u16(0xc6),u16(0xca),u16(0xce),u16(0x11e8),u16(0x16d0),u16(0xa4),u16(0x1e50),u16(0x1e58),u16(0x78),u16(0x11fa),u16(0xba),u16(0x19d2),u16(0x12f6),u16(0x12de),u16(0x4de),actor(0xf00),actor(0x1900),u16(0x408),u16(0x40c),u16(0x410),u16(0x430)))
 out:flush()
end
for address,label in pairs({[0x85f137]='opponent_entry',[0x85f175]='before_write_78',[0x85f178]='after_write_78',[0x85f195]='after_link'}) do
 assert(event.onmemoryexecute(function() if reg('D')==0xf00 then record('execution',label) end end,address,'issd-opponent-'..label),'Hook failed')
end
for address,label in pairs({[0x84a346]='response_dispatch',[0x84a36d]='response_case_2',
 [0x84a52b]='response_init_0328',[0x84a55e]='response_handler_0328',
 [0x84a381]='after_foul_gate',
 [0x84a570]='response_init_0330',[0x84a589]='response_handler_0330',
 [0x84a58e]='response_0330_expired',[0x84a5a3]='response_handler_0360',
 [0x84a6d7]='response_handler_0350',[0x84a6e0]='response_0350_animation_done',
 [0x84a6e9]='response_leave_0350',[0x849faf]='recovery_init',
 [0x849fd7]='recovery_handler',[0x84878a]='return_no_ball',[0x848dd1]='return_with_ball'}) do
 assert(event.onmemoryexecute(function() if reg('D')==0x1900 then record('execution',label) end end,address,'issd-opponent-'..label),'Response hook failed')
end
assert(event.onmemoryexecute(function() if reg('D')==0x1900 then record('execution','foul_gate_entry') end end,0x80f005,'issd-opponent-foul-gate'),'Foul hook failed')
for address,label in pairs({[0x80f045]='foul_return_clear',[0x80f047]='foul_branch_47',[0x80f04f]='foul_branch_4f',[0x80f06a]='foul_branch_6a',[0x80f076]='foul_branch_76',
 [0x80f09e]='foul_branch_9e',[0x80f0c4]='foul_branch_c4',[0x80f125]='foul_branch_125'}) do
 assert(event.onmemoryexecute(function() if reg('D')==0x1900 then record('execution',label) end end,address,'issd-opponent-'..label),'Foul branch hook failed')
end
for address,label in pairs({[0xa4db90]='restart_initialize',[0xa4dd11]='restart_case_3',
 [0xa4dd45]='restart_prepare',[0xa4dd6a]='restart_select_actor',
 [0xa4dd79]='restart_actor_selected',[0xa4ddb7]='restart_set_phase_4',
 [0xa4dcc8]='restart_place_ball'}) do
 assert(event.onmemoryexecute(function() record('restart',label) end,address,'issd-restart-'..label),'Restart hook failed')
end
assert(event.onframeend(function()record('frame_end','')end,'issd-opponent-frame'),'Frame hook failed')
dofile(assert(os.getenv('ISSD_AUTO_GATE_SCRIPT'),'Missing gate observer'))
out:close()
