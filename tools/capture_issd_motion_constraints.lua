-- Passive frame-end evidence. No input injection or memory writes.
local directory = "C:/Users/evandro.mota/Documents/REA-FUTEBOL/docs/"
local base = directory .. "issd-motion-constraints-" .. os.date("%Y%m%d-%H%M%S")
local path = base .. ".jsonl"
local suffix = 0
while true do
  local existing = io.open(path, "r")
  if not existing then break end
  existing:close()
  suffix = suffix + 1
  path = base .. "-" .. suffix .. ".jsonl"
end
local output = assert(io.open(path, "w"))
output:write('{"type":"session_start","schema_version":1,"warmup_frames":1800,"capture_frames":18000}\n')
output:flush()
local count, closed = 0, false
local function u16(address) return mainmemory.read_u16_le(address) end
local function words(base_address, offsets)
  local values = {}
  for _, offset in ipairs(offsets) do
    values[#values + 1] = string.format('"%04X":%d', offset, u16(base_address + offset))
  end
  return "{" .. table.concat(values, ",") .. "}"
end
local function finish()
  if closed then return end
  closed = true
  output:flush()
  output:close()
  console.writeline("ISSD motion constraints saved: " .. path)
end
event.onexit(finish, "issd-motion-constraints-close")
local function capture_frame()
  if closed then return end
  count = count + 1
  if count == 1800 then console.writeline("ISSD: capture begins now; play normally for 5 minutes") end
  if count <= 1800 then return end
  local actors = {}
  for address = 0x0500, 0x1A00, 0x0100 do
    actors[#actors + 1] = string.format('{"address":%d,"words":%s}', address,
      words(address, {0x06,0x08,0x0A,0x0C,0x22,0x24,0x26,0x28,0x2A,0x2C,0x2E,0x30,0x32,0x60,0x68,0x6C,0x88}))
  end
  output:write(string.format('{"frame":%d,"globals":%s,"actors":[%s]}\n',
    emu.framecount(), words(0, {0x10,0x20,0x28,0x86,0x98,0x9A,0xC0,0xD0,0xE8,0xF0,0x408,0x40C,0x11E8,0x12A2,0x12A4,0x12E0,0x12E2,0x12E4,0x12E6,0x12E8,0x12EA,0x12F6,0x12FA}), table.concat(actors, ",")))
  if count % 60 == 0 then output:flush() end
  if count % 1800 == 0 then console.writeline("ISSD: captured " .. math.floor((count - 1800) / 60) .. " seconds at 60fps") end
  if count >= 19800 then finish() end
end
console.writeline("ISSD: 30s preparation + 5min passive capture at 60fps; output: " .. path)
local ok, problem = xpcall(function()
  while not closed do
    emu.frameadvance()
    capture_frame()
  end
end, debug.traceback)
if not ok then
  console.writeline("ISSD CAPTURE ERROR: " .. tostring(problem))
  finish()
end
