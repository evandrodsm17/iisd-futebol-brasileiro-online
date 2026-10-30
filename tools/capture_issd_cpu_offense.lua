-- Read-only AI offensive-play trace for SNES ISS Deluxe (BizHawk, USA).
-- Use Open Game / CPU vs CPU, keep a single difficulty for this run.
-- Change scenario for every run, and output_path to a writable directory.
-- No joypad.set, savestate, write_u*, memory mutation or auto-advance.
-- "ball" coordinates/velocity and "carrier" are raw WRAM candidates.
-- Side flags ($0DA4/$0EA4), difficulty ($0DCC/$0ECC), RNG ($1FEA/$1FEC)
-- are captured to test static CPU routing, NOT to infer decisions from one frame.
local output_path = "issd-cpu-offense-trace.jsonl"
local scenario = "CPUvsCPU_level-unknown"
local capture_frames = 7200  -- two minutes at 60 emulated frames/s

local u8 = mainmemory.read_u8
local u16 = mainmemory.read_u16_le
local function s16(address)
  local n = u16(address)
  return n >= 0x8000 and n - 0x10000 or n
end

local out = assert(io.open(output_path, "w"))
local frame, count, closed = 0, 0, false
local function write_actor(address)
  -- 22 actor pages, player slots of both sides; active check is provisional.
  local type = u8(address + 0x30)
  if type == 0 then return false end
  out:write(string.format(
    '{"address":%d,"side":%d,"type":%d,"state":%d,"script":%d,"descriptor":%d,' ..
    '"direction":%d,"timer":%d,"duration":%d,"cursor":%d,' ..
    '"x":%d,"y":%d,"vx":%d,"vy":%d,"record":%d}',
    address, address < 0x1000 and 0 or 1, type,
    u16(address + 0x32), u16(address + 0x1C),
    u16(address + 0x14), u16(address + 0x2E),
    u16(address + 0x16), u16(address + 0x18),
    u16(address + 0x1A), s16(address + 0x2A),
    s16(address + 0x2C), s16(address + 0x46),
    s16(address + 0x48), u16(address + 0x9A)))
  return true
end

local function on_frame()
  if closed then return end
  frame = frame + 1
  -- Actor and ball sampled from the same frame, including short-lived kicks.
  out:write(string.format(
    '{"schema":"issd-cpu-offense-trace/v1","scenario":"%s","frame":%d,' ..
    '"phase":%d,"game_level":%d,"selected_p1":%d,"carrier_candidate":%d,' ..
    '"side_flags_a4":[%d,%d],"team_CC":[%d,%d],"prng_words":[%d,%d],' ..
    '"ball":{"x":%d,"y":%d,"z":%d,"vx":%d,"vy":%d,"vz":%d},' ..
    '"stadium":{"layout":%d,"length":%d,"width":%d},' ..
    '"actors":[',
    scenario, frame, u16(0x00C0), u16(0x1E54),
    u16(0x1ACC), u16(0x1B90),
    u16(0x0DA4), u16(0x0EA4), u16(0x0DCC), u16(0x0ECC), u16(0x1FEA), u16(0x1FEC),
    s16(0x0408), s16(0x040C), s16(0x0410),
    s16(0x0424), s16(0x0428), s16(0x0436),
    u16(0x0086), u16(0x12A2), u16(0x12A4)))
  local first = true
  for address = 0x0500, 0x1A00, 0x100 do
    if u8(address + 0x30) ~= 0 then
      if not first then out:write(",") end
      write_actor(address)
      first = false
    end
  end
  out:write("]}\n")
  count = count + 1
  if count % 120 == 0 then out:flush() end
  if frame >= capture_frames then
    out:flush()
    out:close()
    closed = true
    console.writeline(string.format(
      "ISSD offense trace captured %d frames: %s", count, output_path))
  end
end
event.onframeend(on_frame, "issd-cpu-offense-readonly")
console.writeline("Passive CPU offense capture armed for " .. capture_frames .. " frames")
