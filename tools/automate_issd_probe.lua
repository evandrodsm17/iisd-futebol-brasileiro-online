-- Isolated experimental navigation. Sends P1 inputs; never writes ROM or RAM.
-- A menu pulse is a probe, not evidence that a match has started.
local directory = os.getenv('ISSD_AUTO_OUTPUT_DIR') or 'C:/Users/evandro.mota/Documents/REA-FUTEBOL/analysis'
local stem = directory .. '/issd-auto-probe-' .. os.date('%Y%m%d-%H%M%S')
local base = stem
local suffix = 0
while true do
  local existing = io.open(base .. '.jsonl', 'r')
  if not existing then break end
  existing:close()
  suffix = suffix + 1
  base = stem .. '-' .. suffix
end
local output_path = base .. '.jsonl'
local out = assert(io.open(output_path, 'w'))
local function u16(a) return mainmemory.read_u16_le(a) end
local function button(frame)
  -- Conservative spaced pulses; remaining frames are neutral.
  if frame>=180 and frame<=1200 and frame%120<6 then
    return {Start=true}, 'Start'
  end
  if frame>1200 and frame<=3450 and frame%120<6 then
    return {A=true}, 'A'
  end
  if frame>=3510 and frame<3540 then return {B=true}, 'B' end
  if frame>=3600 and frame<3720 then return {Right=true}, 'Right' end
  if frame>=3780 and frame<3900 then return {Left=true}, 'Left' end
  if frame>=3960 and frame<4080 then return {Up=true}, 'Up' end
  if frame>=4140 and frame<4260 then return {Down=true}, 'Down' end
  return {}, 'neutral'
end
out:write('{"type":"session_start","schema":"issd-auto-probe/v2","menu_route":"experimental","target_frames":4800}\n')
out:flush()
for step=1,4800 do
  local input,label=button(step)
  joypad.set(input,1)
  emu.frameadvance()
  if step%600==0 then
    local ok, message=pcall(client.screenshot,base..'-'..step..'.png')
    print('screenshot '..step..': '..tostring(ok)..' '..tostring(message))
  end
  if step%2==0 then
    local selected=u16(0x1ACC)
    local valid=selected>=0x0500 and selected<=0x1A00 and selected%0x100==0
    local state,script,descriptor,direction,x,y=0,0,0,0,0,0
    if valid then
      state=u16(selected+0x32);script=u16(selected+0x1C)
      descriptor=u16(selected+0x14);direction=u16(selected+0x2E)
      x=u16(selected+0x08);y=u16(selected+0x0C)
    end
    local controls={}
    for address=0x1AA0,0x1B60,0x30 do
      controls[#controls+1]=string.format('{"address":%d,"actor":%d,"flags":%d,"held":%d}',
        address,u16(address+0x2C),u16(address+0x2E),u16(address+0x12))
    end
    local actors={}
    for address=0x0500,0x1A00,0x100 do
      actors[#actors+1]=string.format('{"address":%d,"type":%d,"state":%d,"direction":%d,"x":%d,"x_fraction":%d,"y":%d,"y_fraction":%d,"team":%d}',
        address,mainmemory.read_u8(address+0x30),u16(address+0x32),u16(address+0x2E),
        u16(address+0x08),u16(address+0x06),u16(address+0x0C),u16(address+0x0A),u16(address+0x9A))
    end
    out:write(string.format('{"step":%d,"frame":%d,"input":"%s","joypad1":%d,"held_p1":%d,"pressed_p1":%d,"player_setting":%d,"mode1":%d,"mode2":%d,"phase":%d,"selected_p1":%d,"actor_slot_valid":%s,"actor":{"state":%d,"script":%d,"descriptor":%d,"direction":%d,"x":%d,"y":%d},"ball":{"x":%d,"y":%d,"z":%d},"link_a4":%d,"link_a6":%d,"controls":[%s],"actors":[%s]}\n',
      step,emu.framecount(),label,u16(0x10),u16(0x20),u16(0x28),u16(0x11E6),u16(0x32),u16(0x70),u16(0xC0),selected,tostring(valid),
      state,script,descriptor,direction,x,y,u16(0x408),u16(0x40C),u16(0x410),u16(0xA4),u16(0xA6),table.concat(controls,','),table.concat(actors,',')))
    if step%120==0 then out:flush() end
  end
end
joypad.set({},1)
out:write('{"type":"session_end","steps":4800}\n')
out:close()
print('ISSD auto probe complete: '..output_path)
