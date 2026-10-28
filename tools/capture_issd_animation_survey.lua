-- Passive ISS Deluxe animation survey for BizHawk.
--
-- Run in a real match. It never calls joypad.set and never writes RAM or ROM.
-- After a 10-second warm-up it records one metadata row for each unique
-- script/direction/descriptor seen on any capturable field actor over 10 min.

local output_path = "C:/Users/evandro.mota/Documents/REA-FUTEBOL/docs/issd-animation-survey.jsonl"
local warmup_frames = 600
local capture_frames = 36000

local function u16(address) return mainmemory.read_u16_le(address) end
local function s16(address)
  local value = u16(address)
  return value >= 0x8000 and value - 0x10000 or value
end

local function actor_is_capturable(address)
  local descriptor, pose, kind = u16(address + 0x14), u16(address), mainmemory.read_u8(address + 0x30)
  if kind == 0 or descriptor < 0x8000 or pose == 0 or pose >= 0xA000 then return false end
  local count = mainmemory.read_u8(pose)
  return count > 0 and count <= 64 and pose + count * 2 <= 0xA000
end

local output = assert(io.open(output_path, "w"))
local seen, frame, samples, closed = {}, 0, 0, false

local function capture_frame()
  if closed then return end
  frame = frame + 1
  if frame > warmup_frames then
    for address = 0x0500, 0x1A00, 0x100 do
      if actor_is_capturable(address) then
        local script, direction, descriptor = u16(address + 0x1C), u16(address + 0x2E), u16(address + 0x14)
        local key = string.format("%04X-%d-%04X", script, direction, descriptor)
        if not seen[key] then
          seen[key] = true
          output:write(string.format(
            '{"frame":%d,"phase":%d,"selected_p1":%d,"held_p1":%d,"pressed_p1":%d,"actor":{"address":%d,"state":%d,"script":%d,"descriptor":%d,"pose":%d,"direction":%d,"x":%d,"y":%d,"timer":%d,"duration":%d,"cursor":%d,"type":%d,"kit_variant":%d,"uniform_selector":%d}}\n',
            frame, u16(0x00C0), u16(0x1ACC), u16(0x0020), u16(0x0028),
            address, u16(address + 0x32), script, descriptor, u16(address), direction,
            s16(address + 0x2A), s16(address + 0x2C), u16(address + 0x16),
            u16(address + 0x18), u16(address + 0x1A), mainmemory.read_u8(address + 0x30),
            mainmemory.read_u8(address + 0x56), mainmemory.read_u8(address + 0x57)))
          output:flush()
          samples = samples + 1
        end
      end
    end
  end
  if frame >= warmup_frames + capture_frames then
    output:close()
    closed = true
    console.writeline(string.format("ISSD animation survey written (%d unique poses): %s", samples, output_path))
  end
end

event.onframeend(capture_frame, "issd-animation-survey")
console.writeline("ISSD animation survey: 10s warm-up, then 10 min read-only metadata capture")
