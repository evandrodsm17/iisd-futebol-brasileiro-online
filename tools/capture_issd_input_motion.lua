-- Passive ISS Deluxe input-to-motion capture for BizHawk.
--
-- Start this in a real match. It never calls joypad.set and never writes RAM
-- or ROM. After a ten-second warm-up it records P1's raw/held pad words and
-- the selected P1 actor for sixty seconds.

local output_path = "C:/Users/evandro.mota/Documents/REA-FUTEBOL/docs/issd-input-motion-trace.jsonl"
local warmup_frames = 600
local capture_frames = 3600

local function u16(address) return mainmemory.read_u16_le(address) end
local function s16(address)
  local value = u16(address)
  return value >= 0x8000 and value - 0x10000 or value
end

local function actor_is_valid(address)
  return address >= 0x0500 and address <= 0x1A00 and address % 0x100 == 0
      and mainmemory.read_u8(address + 0x30) ~= 0
end

local output = assert(io.open(output_path, "w"))
local frame, samples, closed = 0, 0, false

local function capture_frame()
  if closed then return end
  frame = frame + 1
  if frame <= warmup_frames then return end
  local selected = u16(0x1ACC)
  if actor_is_valid(selected) then
    output:write(string.format(
      '{"frame":%d,"joypad1":%d,"held_p1":%d,"pressed_p1":%d,"selected_p1":%d,"phase":%d,"actor":{"state":%d,"script":%d,"descriptor":%d,"direction":%d,"x":%d,"y":%d,"vx":%d,"vy":%d,"timer":%d,"duration":%d,"cursor":%d}}\n',
      frame, u16(0x0010), u16(0x0020), u16(0x0028), selected, u16(0x00C0),
      u16(selected + 0x32), u16(selected + 0x1C), u16(selected + 0x14),
      u16(selected + 0x2E), s16(selected + 0x2A), s16(selected + 0x2C),
      s16(selected + 0x46), s16(selected + 0x48), u16(selected + 0x16),
      u16(selected + 0x18), u16(selected + 0x1A)))
    samples = samples + 1
  end
  if frame >= warmup_frames + capture_frames then
    output:close()
    closed = true
    console.writeline(string.format(
      "ISSD input/motion trace written (%d valid samples): %s", samples, output_path))
  end
end

event.onframeend(capture_frame, "issd-input-motion-capture")
console.writeline("ISSD input/motion capture: 10s warm-up, then 60s read-only trace")
