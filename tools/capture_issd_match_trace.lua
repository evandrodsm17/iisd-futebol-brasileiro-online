-- Read-only live-match trace for ISS Deluxe in BizHawk.
--
-- Load only after reaching a real match.  It does not send controller input
-- or export ROM data/savestates.  The JSONL output contains sampled runtime
-- coordinates needed to calibrate the browser port: ball, camera, current
-- carrier and active actor records.
--
-- This is deliberately a passive capture: it never calls joypad.set.  Start
-- it only while a player is visibly moving sideways in a real match.  It then
-- lets the emulation run for two seconds and records the game's expanded OAM
-- geometry once every other frame.

local output_path = "C:/Users/evandro.mota/Documents/REA-FUTEBOL/docs/issd-natural-play-trace.jsonl"
local cgram_path = "C:/Users/evandro.mota/Documents/REA-FUTEBOL/docs/issd-natural-play-cgram.hex"
local capture_frames = 18000
local sample_every = 2
local screenshot_every = 300

local function u16(address)
  return mainmemory.read_u16_le(address)
end

local function s16(address)
  local value = u16(address)
  return value >= 0x8000 and value - 0x10000 or value
end

local sizes = {{8,16},{8,32},{8,64},{16,32},{16,64},{32,64},{16,32},{16,32}}

local function actor_is_capturable(address)
  local descriptor, pose, actor_type = u16(address + 0x14), u16(address), mainmemory.read_u8(address + 0x30)
  if actor_type == 0 or descriptor < 0x8000 or pose == 0 or pose >= 0xA000 then return false end
  local count = mainmemory.read_u8(pose)
  return count > 0 and count <= 64 and pose + count * 2 <= 0xA000
end

local function write_actor(file, address, obsel)
  -- $0500..$1A00, stride $100: verified actor allocation range.  A zero
  -- type at +$30 means the slot is inactive and stays out of the log.
  if not actor_is_capturable(address) then return false end
  local descriptor, pose = u16(address + 0x14), u16(address)
  local count = mainmemory.read_u8(pose)
  local object_props = mainmemory.read_u8(address + 3)
  local inherited = mainmemory.read_u8(address + 5)
  if inherited & 0x80 == 0 then inherited = mainmemory.read_u8(0x007C) end
  object_props = object_props | ((inherited & 0x30) | (mainmemory.read_u8(address + 4) & 0xF0))
  file:write(string.format(
    '{"address":%d,"team_record":%d,"field_slot":%d,"state":%d,"animation_handler":%d,"animation_script":%d,"animation_timer":%d,"animation_duration":%d,"animation_cursor":%d,"type":%d,"kit_variant":%d,"uniform_selector":%d,"object_flags":%d,"x":%d,"y":%d,"vx":%d,"vy":%d,"descriptor":%d,"pose":%d,"direction":%d,"parts":[',
    address, u16(address + 0x9A), u16(address + 0x68), u16(address + 0x32),
    u16(address + 0x92), u16(address + 0x1C), u16(address + 0x16), u16(address + 0x18), u16(address + 0x1A),
    mainmemory.read_u8(address + 0x30), mainmemory.read_u8(address + 0x56), mainmemory.read_u8(address + 0x57), mainmemory.read_u8(address + 4),
    s16(address + 0x2A), s16(address + 0x2C), s16(address + 0x46), s16(address + 0x48),
    descriptor, pose, u16(address + 0x2E)))
  for index = 0, count - 1 do
    if index > 0 then file:write(',') end
    local entry = pose + index * 2
    local attr = mainmemory.read_u8(0x6001 + entry)
    local large = mainmemory.read_u8(entry + 1) & 0x80 ~= 0
    local size = sizes[(obsel >> 5) + 1][large and 2 or 1]
    local final_attr = (attr & 0xC1) ~ object_props
    if attr & 0x20 ~= 0 then
      if final_attr & 0x08 ~= 0 then final_attr = final_attr | 0x02
      else final_attr = (final_attr & 0xFB) | 0x08 end
    end
    local dx = s16(0x2000 + entry)
    if object_props & 0x40 ~= 0 then dx = -dx end
    file:write(string.format(
      '{"x":%d,"y":%d,"tile":%d,"size":%d,"attr":%d}',
      dx - (large and 8 or 4), s16(0x4000 + entry) - (large and 8 or 4),
      mainmemory.read_u8(0x6000 + entry), size, final_attr))
  end
  file:write(']}')
  return true
end

local trace = assert(io.open(output_path, "w"))
local frame = 0
local closed = false

local function capture_frame()
  if closed then return end
  frame = frame + 1
  if frame % sample_every == 0 then
    local obsel = mainmemory.read_u8(0x1EA6)
    trace:write(string.format(
      '{"frame":%d,"obsel":%d,"phase":%d,"stadium":{"layout":%d,"length":%d,"width":%d},"ball":{"x":%d,"y":%d,"z":%d,"vx":%d,"vy":%d,"vz":%d},"carrier":%d,"selected_p1":%d,"camera":{"x":%d,"y":%d},"actors":[',
      frame, obsel, u16(0x00C0), u16(0x0086), u16(0x12A2), u16(0x12A4),
      s16(0x0408), s16(0x040C), s16(0x0410), s16(0x0424), s16(0x0428), s16(0x0436),
      u16(0x1B90), u16(0x1ACC), s16(0x13A0), s16(0x13B0)))
    local first = true
    for actor = 0x0500, 0x1A00, 0x100 do
      if actor_is_capturable(actor) then
        if not first then trace:write(',') end
        write_actor(trace, actor, obsel)
        first = false
      end
    end
    trace:write(']}\n')
    trace:flush()
  end
  if frame % screenshot_every == 0 then
    client.screenshot("C:/Users/evandro.mota/Documents/REA-FUTEBOL/docs/issd-natural-play-" .. frame .. ".png")
  end
  if frame >= capture_frames then
    trace:close()
    local cgram = assert(io.open(cgram_path, "w"))
    for index = 0, 0x1FF do
      cgram:write(string.format("%02X", mainmemory.read_u8(0x2C00 + index)))
      if index % 32 == 31 then cgram:write("\n") end
    end
    cgram:close()
    closed = true
    console.writeline("ISSD natural-play trace written: " .. output_path)
  end
end

-- Register a per-frame callback and return to BizHawk.  The player can now
-- keep moving normally; no emu.frameadvance loop monopolizes input.
event.onframeend(capture_frame, "issd-motion-coverage")
console.writeline("ISSD natural-play capture armed for " .. capture_frames .. " frames")
