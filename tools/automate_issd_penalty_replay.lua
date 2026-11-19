-- Isolated penalty replay from a locally captured BizHawk state.
-- Directions are held only on the requested controller; A pulses both.
local state=assert(os.getenv('ISSD_PENALTY_REPLAY_STATE'))
local output=assert(os.getenv('ISSD_PENALTY_REPLAY_OUTPUT'))
local direction=assert(os.getenv('ISSD_PENALTY_REPLAY_DIRECTION'))
local controller=assert(os.getenv('ISSD_PENALTY_REPLAY_CONTROLLER'))
local steps=tonumber(os.getenv('ISSD_PENALTY_REPLAY_STEPS') or '1800')
local screenshot_dir=os.getenv('ISSD_PENALTY_REPLAY_SCREENSHOT_DIR')
local action_start_text=os.getenv('ISSD_PENALTY_REPLAY_P2_ACTION_START')
local action_start=action_start_text and tonumber(action_start_text) or nil
assert(not action_start_text or (action_start and action_start%1==0 and action_start>=1 and action_start<=steps-8),'Invalid P2 action window')
local action_second_text=os.getenv('ISSD_PENALTY_REPLAY_P2_ACTION_SECOND')
local action_second=action_second_text and tonumber(action_second_text) or nil
assert(not action_second_text or (action_start and action_second and action_second%1==0 and action_second>action_start+8 and action_second<=steps-8),'Invalid second P2 action window')
local players_override=os.getenv('ISSD_PENALTY_REPLAY_PLAYERS_OVERRIDE')
assert(not players_override or players_override=='4','Only the explicitly labeled two-player override is supported')
local directions={neutral={},Left={Left=true},Right={Right=true},Up={Up=true},Down={Down=true},
 UpLeft={Up=true,Left=true},UpRight={Up=true,Right=true},DownLeft={Down=true,Left=true},DownRight={Down=true,Right=true}}
assert(directions[direction] and (controller=='p1' or controller=='p2') and steps and steps%1==0 and steps>=1 and steps<=5000,'Invalid replay configuration')
local out=assert(io.open(output,'w'))
assert(savestate.load(state,true),'Unable to load penalty scene')
local function u(a) return mainmemory.read_u16_le(a) end
local previous_players=u(0x11e6)
if players_override then mainmemory.write_u16_le(0x11e6,4) end
out:write(string.format('{"type":"session_start","direction":"%s","controller":"%s","start_frame":%d,"steps":%d,"action_pulses":"%s","players_before":%d,"players_after":%d,"synthetic_players":%s}\n',direction,controller,emu.framecount(),steps,action_start and 'p1-periodic-p2-window' or 'both',previous_players,u(0x11e6),tostring(players_override~=nil)));out:flush()
if action_start then out:write(string.format('{"type":"synthetic_p2_action","start_step":%d,"duration":8}\n',action_start));out:flush() end
if action_second then out:write(string.format('{"type":"synthetic_p2_action","start_step":%d,"duration":8}\n',action_second));out:flush() end
for step=1,steps do
 local p1,p2={},{}
 for name,pressed in pairs(directions[direction]) do
  if controller=='p1' then p1[name]=pressed else p2[name]=pressed end
 end
 local action=emu.framecount()%120<6
 if action then p1.A=true end
 if action_start then
  if (step>=action_start and step<action_start+8) or (action_second and step>=action_second and step<action_second+8) then p2.A=true end
 elseif action then p2.A=true end
 joypad.set(p1,1);joypad.set(p2,2)
 emu.frameadvance()
 if screenshot_dir and (step==330 or step==960 or step==1020 or step==1200) then pcall(client.screenshot,screenshot_dir..'/step-'..step..'.png') end
 out:write(string.format('{"type":"sample","step":%d,"frame":%d,"mode1":%d,"mode2":%d,"phase":%d,"held_p1":%d,"held_p2":%d,"input_word":%d,"side":%d,"round":%d,"action":%s,"action_p2":%s}\n',step,emu.framecount(),u(0x32),u(0x70),u(0xc0),u(0x20),u(0x22),u(0x140c),u(0x1440),u(0x1704),tostring(action),tostring(p2.A==true)))
 if step%60==0 then out:flush() end
end
joypad.set({},1);joypad.set({},2)
out:write(string.format('{"type":"session_end","steps":%d,"end_frame":%d}\n',steps,emu.framecount()))
out:close()
