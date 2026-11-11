-- Replays a user-supplied scenario save in an isolated BizHawk instance.
-- The ROM and savestate are read only; outputs go to the caller's directory.
local state=assert(os.getenv('ISSD_THROW_STATE'),'ISSD_THROW_STATE ausente')
local output=assert(os.getenv('ISSD_THROW_OUTPUT'),'ISSD_THROW_OUTPUT ausente'):gsub('\\','/')
local button=os.getenv('ISSD_THROW_BUTTON') or 'NEUTRAL'
assert(button=='NEUTRAL' or button=='A' or button=='B' or button=='X' or button=='Y','Bot?o inv?lido')
local out=assert(io.open(output..'/trace.jsonl','w'))
assert(savestate.load(state,true),'N?o foi poss?vel carregar estado')
local function u16(address)return mainmemory.read_u16_le(address)end
for step=0,149 do
 local input={}
 if step>=60 and step<66 and button~='NEUTRAL' then input[button]=true end
 joypad.set(input,1);emu.frameadvance()
 local actors={}
 for address=0x0500,0x1A00,0x100 do
  actors[#actors+1]=string.format('{"address":%d,"type":%d,"state":%d,"script":%d,"descriptor":%d,"direction":%d,"x":%d,"y":%d}',address,mainmemory.read_u8(address+0x30),u16(address+0x32),u16(address+0x1C),u16(address+0x14),u16(address+0x2E),u16(address+0x08),u16(address+0x0C))
 end
 out:write(string.format('{"step":%d,"frame":%d,"button":"%s","a4":%d,"a6":%d,"controlled":%d,"phase":%d,"ball":{"x":%d,"y":%d,"z":%d,"vx":%d,"vy":%d,"vz":%d,"type":%d},"actors":[%s]}\n',step,emu.framecount(),button,u16(0xA4),u16(0xA6),u16(0x1AFC),u16(0xC0),u16(0x408),u16(0x40C),u16(0x410),u16(0x424),u16(0x428),u16(0x436),u16(0x430),table.concat(actors,',')))
 if step>=50 and step<=110 and step%2==0 then pcall(client.screenshot,output..string.format('/frame-%03d.png',step)) end
 if step%30==0 then out:flush() end
end
joypad.set({},1);out:write('{"type":"done"}\n');out:close()
