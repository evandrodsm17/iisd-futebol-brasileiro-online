-- Isolated, user-input-only goalkeeper action trial; no emulated memory writes.
local state=assert(os.getenv('ISSD_KEEPER_TRIAL_STATE'),'Missing state')
local output=assert(os.getenv('ISSD_KEEPER_TRIAL_OUTPUT'),'Missing output')
local button=os.getenv('ISSD_KEEPER_TRIAL_BUTTON') or 'NEUTRAL'
assert(button=='NEUTRAL' or button=='A' or button=='B' or button=='X' or button=='Y','Invalid button')
local direction=os.getenv('ISSD_KEEPER_TRIAL_DIRECTION')
local directions={Up={Up=true},Down={Down=true},Left={Left=true},Right={Right=true},
 UpLeft={Up=true,Left=true},UpRight={Up=true,Right=true},DownLeft={Down=true,Left=true},DownRight={Down=true,Right=true}}
assert(not direction or (button~='NEUTRAL' and directions[direction]),'Invalid action direction')
local pre_direction=os.getenv('ISSD_KEEPER_PRE_DIRECTION')
assert(not pre_direction or directions[pre_direction], 'Invalid pre-action direction')
local pre_direction2=os.getenv('ISSD_KEEPER_PRE_DIRECTION2')
local pre_switch=tonumber(os.getenv('ISSD_KEEPER_PRE_SWITCH') or '40')
assert(not pre_direction2 or (pre_direction and directions[pre_direction2] and pre_switch and pre_switch%1==0 and pre_switch>=2), 'Invalid second pre-action direction')
local start=tonumber(os.getenv('ISSD_KEEPER_TRIAL_START') or '3')
local duration=tonumber(os.getenv('ISSD_KEEPER_TRIAL_DURATION') or '6')
assert(not pre_direction2 or pre_switch<start,'Second direction must start before action')
assert(start and start%1==0 and start>=1 and start<=120 and duration and duration%1==0 and duration>=1 and duration<=30,'Invalid window')
assert(savestate.load(state,true),'Unable to load state')
local out=assert(io.open(output,'w'))
local function u16(a) return mainmemory.read_u16_le(a) end
if pre_direction2 then out:write(string.format('{"type":"pre_direction2","direction":"%s","start":%d,"end":%d}\n',pre_direction2,pre_switch,start)) end
if pre_direction then out:write(string.format('{"type":"pre_direction","direction":"%s","start":2,"end":%d}\n',pre_direction,pre_direction2 and pre_switch or start)) end
if direction then out:write(string.format('{"type":"action_direction","direction":"%s"}\n',direction)) end
out:write(string.format('{"type":"session_start","schema":"issd-keeper-input-trial/v1","button":"%s","start":%d,"duration":%d,"state_frame":%d}\n',button,start,duration,emu.framecount()))
for step=1,180 do
 local press=button~='NEUTRAL' and step>=start and step<start+duration
 local input=press and {[button]=true} or {}
 local active_pre=pre_direction2 and step>=pre_switch and pre_direction2 or pre_direction
 if active_pre and step>=2 and step<start then for k,v in pairs(directions[active_pre]) do input[k]=v end end
 if press and direction then for k,v in pairs(directions[direction]) do input[k]=v end end
 joypad.set(input,1);joypad.set({},2);emu.frameadvance()
 local actor=0x500
 out:write(string.format('{"step":%d,"frame":%d,"input":"%s","selected":%d,"held_p1":%d,"actor_type":%d,"state":%d,"script":%d,"descriptor":%d,"pose":%d,"direction":%d,"x":%d,"y":%d,"carrier":%d,"link_a6":%d,"ball_x":%d,"ball_y":%d,"ball_z":%d,"ball_vx":%d,"ball_vy":%d,"ball_vz":%d}\n',
 step,emu.framecount(),press and (button..(direction and ('+'..direction) or '')) or ((active_pre and step>=2 and step<start) and active_pre or 'neutral'),u16(0x1acc),u16(0x20),mainmemory.read_u8(actor+0x30),u16(actor+0x32),u16(actor+0x1c),u16(actor+0x14),u16(actor),u16(actor+0x2e),u16(actor+8),u16(actor+12),u16(0x1b90),u16(0xa6),u16(0x408),u16(0x40c),u16(0x410),u16(0x424),u16(0x428),u16(0x436)))
end
joypad.set({},1);joypad.set({},2);out:write('{"type":"session_end","steps":180}\n');out:close()
