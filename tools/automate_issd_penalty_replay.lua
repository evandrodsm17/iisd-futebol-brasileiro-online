-- Isolated penalty replay from a locally captured BizHawk state.
-- Directions are held only on the requested controller; A pulses both.
local state=assert(os.getenv('ISSD_PENALTY_REPLAY_STATE'))
local output=assert(os.getenv('ISSD_PENALTY_REPLAY_OUTPUT'))
local direction=assert(os.getenv('ISSD_PENALTY_REPLAY_DIRECTION'))
local controller=assert(os.getenv('ISSD_PENALTY_REPLAY_CONTROLLER'))
local steps=tonumber(os.getenv('ISSD_PENALTY_REPLAY_STEPS') or '1800')
local directions={neutral={},Left={Left=true},Right={Right=true},Up={Up=true},Down={Down=true},
 UpLeft={Up=true,Left=true},UpRight={Up=true,Right=true},DownLeft={Down=true,Left=true},DownRight={Down=true,Right=true}}
assert(directions[direction] and (controller=='p1' or controller=='p2') and steps and steps%1==0 and steps>=1 and steps<=5000,'Invalid replay configuration')
local out=assert(io.open(output,'w'))
assert(savestate.load(state,true),'Unable to load penalty scene')
local function u(a) return mainmemory.read_u16_le(a) end
out:write(string.format('{"type":"session_start","direction":"%s","controller":"%s","start_frame":%d,"steps":%d,"action_pulses":"both"}\n',direction,controller,emu.framecount(),steps));out:flush()
for step=1,steps do
 local p1,p2={},{}
 for name,pressed in pairs(directions[direction]) do
  if controller=='p1' then p1[name]=pressed else p2[name]=pressed end
 end
 local action=emu.framecount()%120<6
 if action then p1.A=true;p2.A=true end
 joypad.set(p1,1);joypad.set(p2,2)
 emu.frameadvance()
 out:write(string.format('{"type":"sample","step":%d,"frame":%d,"mode1":%d,"mode2":%d,"phase":%d,"held_p1":%d,"held_p2":%d,"input_word":%d,"side":%d,"round":%d,"action":%s}\n',step,emu.framecount(),u(0x32),u(0x70),u(0xc0),u(0x20),u(0x22),u(0x140c),u(0x1440),u(0x1704),tostring(action)))
 if step%60==0 then out:flush() end
end
joypad.set({},1);joypad.set({},2)
out:write(string.format('{"type":"session_end","steps":%d,"end_frame":%d}\n',steps,emu.framecount()))
out:close()
