-- Passive SNES ISS Deluxe menu/lineup capture for BizHawk (USA retail).
-- Launch in a match. Request management, visit Formation/Squad, swap players,
-- cancel or resume. No joypad.set, savestate writes, RAM or ROM modifications.
-- Output is raw evidence, NOT a decoded substitution event log.
--
-- Set output_path to a writable location before running if necessary.
local output_path = "issd-team-management-trace.jsonl"
local capture_frames = 18000
local heartbeat_frames = 120

local u8 = mainmemory.read_u8
local u16 = mainmemory.read_u16_le
local function hexbytes(address, count)
  local a = {}
  for offset = 0, count - 1 do
    a[#a + 1] = string.format("%02X", u8(address + offset))
  end
  return table.concat(a)
end
local function snapshot(frame)
  return {
    frame = frame,
    phase = u16(0x00C0),
    lineup_first = hexbytes(0x3F90, 20),
    lineup_second = hexbytes(0x3FA4, 20),
    original_snapshot_first = hexbytes(0xD864, 20),
    original_snapshot_second = hexbytes(0xD878, 20),
    selector_first = u16(0x1E6C),
    selector_second = u16(0x1E6E),
    -- These bytes are raw offsets; do not label them a visible formation
    -- without matching the screenshot and selected team record.
    team_record_a6_first = u8(0x0D00 + 0xA6),
    team_record_a6_second = u8(0x0E00 + 0xA6),
    selected_actor_candidate = u16(0x1ACC),
    -- Known P1 sampling addresses from capture_issd_input_motion.lua.
    p1_raw_0010 = u16(0x0010),
    p1_held_0020 = u16(0x0020),
    p1_pressed_0028 = u16(0x0028),
    -- Adjacent words are captured as unclassified candidates for P2.
    candidate_0012 = u16(0x0012),
    candidate_0022 = u16(0x0022),
    candidate_002A = u16(0x002A),
  }
end
local function structural_key(s)
  return table.concat({
    tostring(s.phase), s.lineup_first, s.lineup_second,
    s.original_snapshot_first, s.original_snapshot_second,
    tostring(s.selector_first), tostring(s.selector_second),
    tostring(s.team_record_a6_first), tostring(s.team_record_a6_second),
    tostring(s.selected_actor_candidate)
  }, ":")
end
local function input_key(s)
  return table.concat({
    tostring(s.p1_raw_0010), tostring(s.p1_held_0020),
    tostring(s.p1_pressed_0028), tostring(s.candidate_0012),
    tostring(s.candidate_0022), tostring(s.candidate_002A)
  }, ":")
end
local file = assert(io.open(output_path, "w"))
local frame, written, closed = 0, 0, false
local last_structural, last_input = nil, nil
local function record(s, reason)
  -- Fields are bounded to hexadecimal text and integer words.
  file:write(string.format(
    '{"frame":%d,"reason":"%s","phase":%d,"lineup_first":"%s","lineup_second":"%s",' ..
    '"original_snapshot_first":"%s","original_snapshot_second":"%s",' ..
    '"selector_first":%d,"selector_second":%d,' ..
    '"team_record_a6_first":%d,"team_record_a6_second":%d,' ..
    '"selected_actor_candidate":%d,"p1_raw_0010":%d,"p1_held_0020":%d,' ..
    '"p1_pressed_0028":%d,"candidate_0012":%d,"candidate_0022":%d,"candidate_002A":%d}\n',
    s.frame, reason, s.phase, s.lineup_first, s.lineup_second,
    s.original_snapshot_first, s.original_snapshot_second,
    s.selector_first, s.selector_second,
    s.team_record_a6_first, s.team_record_a6_second,
    s.selected_actor_candidate, s.p1_raw_0010, s.p1_held_0020,
    s.p1_pressed_0028, s.candidate_0012, s.candidate_0022,
    s.candidate_002A))
  written = written + 1
  if written % 20 == 0 then file:flush() end
end
local function capture_frame()
  if closed then return end
  frame = frame + 1
  local s = snapshot(frame)
  local structural = structural_key(s)
  local inputs = input_key(s)
  local reason = nil
  if frame == 1 then reason = "initial"
  elseif structural ~= last_structural then reason = "structure-changed"
  elseif inputs ~= last_input then reason = "input-changed"
  elseif frame % heartbeat_frames == 0 then reason = "heartbeat"
  end
  if reason then record(s, reason) end
  last_structural, last_input = structural, inputs
  if frame >= capture_frames then
    file:flush()
    file:close()
    closed = true
    console.writeline(string.format(
      "ISSD team management: %d snapshots / %d emulator frames -> %s",
      written, frame, output_path))
  end
end
event.onframeend(capture_frame, "issd-team-management-evidence")
console.writeline("ISSD passive team-management capture armed: navigate the ORIGINAL Squad menu.")
