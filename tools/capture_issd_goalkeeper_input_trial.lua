-- Isolated, user-input-only goalkeeper action trial; no emulated memory writes.
local state=assert(os.getenv('ISSD_KEEPER_TRIAL_STATE'),'Missing state')
local output=assert(os.getenv('ISSD_KEEPER_TRIAL_OUTPUT'),'Missing output')
local button=os.getenv('ISSD_KEEPER_TRIAL_BUTTON') or 'NEUTRAL'
assert(button=='NEUTRAL' or button=='A' or button=='B' or button=='X' or button=='Y','Invalid button')
local start=tonumber(os.getenv('ISSD_KEEPER_TRIAL_START') or '3')
local duration=tonumber(os.getenv('ISSD_KEEPER_TRIAL_DURATION') or '6')
assert(start and start%1==0 and start>=1 and start<=120 and duration and duration%1==0 and duration>=1 and duration<=30,'Invalid window')
assert(savestate.load(state,true),'Unable to load state')
local out=assert(io.open(output,'w'))
local function u16(a) return mainmemory.read_u16_le(a) end
out:write(string.format('{"type":"session_start","schema":"issd-keeper-input-trial/v1","button":"%s","start":%d,"duration":%d,"state_frame":%d}\n',button,start,duration,emu.framecount()))
for step=1,180 do
 local press=button~='NEUTRAL' and step>=start and step<start+duration
 joypad.set(press and {[button]=true} or {},1);joypad.set({},2);emu.frameadvance()
 local actor=0x500
 out:write(string.format('{"step":%d,"frame":%d,"input":"%s","selected":%d,"held_p1":%d,"actor_type":%d,"state":%d,"script":%d,"descriptor":%d,"pose":%d,"direction":%d,"x":%d,"y":%d,"carrier":%d,"link_a6":%d,"ball_x":%d,"ball_y":%d,"ball_z":%d,"ball_vx":%d,"ball_vy":%d,"ball_vz":%d}\n',
 step,emu.framecount(),press and button or 'neutral',u16(0x1acc),u16(0x20),mainmemory.read_u8(actor+0x30),u16(actor+0x32),u16(actor+0x1c),u16(actor+0x14),u16(actor),u16(actor+0x2e),u16(actor+8),u16(actor+12),u16(0x1b90),u16(0xa6),u16(0x408),u16(0x40c),u16(0x410),u16(0x424),u16(0x428),u16(0x436)))
end
joypad.set({},1);joypad.set({},2);out:write('{"type":"session_end","steps":180}\n');out:close()
