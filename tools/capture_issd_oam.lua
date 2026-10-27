-- Captures the SNES OAM mirror used by ISS Deluxe after booting a local ROM.
-- Run with BizHawk's --lua flag.  It writes only the runtime OAM bytes needed
-- for visual reconstruction; neither the ROM nor a save state is exported.

local output_path = "C:/Users/evandro.mota/Documents/REA-FUTEBOL/docs/issd-runtime-oam.hex"
local planes_path = "C:/Users/evandro.mota/Documents/REA-FUTEBOL/docs/issd-runtime-oam-planes.hex"
local vram_path = "C:/Users/evandro.mota/Documents/REA-FUTEBOL/docs/issd-runtime-vram.bin"
local cgram_path = "C:/Users/evandro.mota/Documents/REA-FUTEBOL/docs/issd-runtime-cgram.hex"
local players_path = "C:/Users/evandro.mota/Documents/REA-FUTEBOL/docs/issd-runtime-player-compositions.json"
local domains_path = "C:/Users/evandro.mota/Documents/REA-FUTEBOL/docs/issd-memory-domains.txt"
local route_path = "C:/Users/evandro.mota/Documents/REA-FUTEBOL/docs/issd-menu-route.log"
-- This script is also loaded into a manually navigated live match.  One frame
-- is sufficient there and avoids changing the player's current game state.
local capture_frame = 1

local domains = assert(io.open(domains_path, "w"))
for _, name in ipairs(memory.getmemorydomainlist()) do domains:write(name .. "\n") end
domains:close()

local route = {}
local function hold(first, last, button)
  for frame = first, last do route[frame] = { [button] = true } end
end
-- BizHawk's SNES binding uses the fully-qualified controller names.
local route_log = assert(io.open(route_path, "w"))
for frame = 1, capture_frame do
  local buttons = route[frame] or {}
  joypad.set(buttons, 1)
  if route[frame] then route_log:write("frame " .. frame .. " input\n") end
  if frame % 300 == 0 then
    local screenshot = "C:/Users/evandro.mota/Documents/REA-FUTEBOL/docs/issd-route-" .. frame .. ".png"
    local ok, result = pcall(client.screenshot, screenshot)
    route_log:write("frame " .. frame .. " screenshot=" .. tostring(ok) .. " " .. tostring(result) .. "\n")
  end
  emu.frameadvance()
end
route_log:close()

local file = assert(io.open(output_path, "w"))
for i = 0, 0x21F do
  file:write(string.format("%02X", mainmemory.read_u8(0x01E0 + i)))
  if i % 32 == 31 then file:write("\n") end
end
file:close()
local planes = assert(io.open(planes_path, "w"))
for _, base in ipairs({0x0000, 0x2000, 0x4000, 0x6000}) do
  for i = 0, 0xFF do planes:write(string.format("%02X", mainmemory.read_u8(base + i))) end
  planes:write("\n")
end
planes:close()

-- OAM selects tiles and palettes; capture both render inputs from the same
-- frame.  These are transient emulator observations, never ROM extraction.
local cgram = assert(io.open(cgram_path, "w"))
for i = 0, 0x1FF do
  cgram:write(string.format("%02X", mainmemory.read_u8(0x2C00 + i)))
  if i % 32 == 31 then cgram:write("\n") end
end
cgram:close()

local vram = assert(io.open(vram_path, "wb"))
for i = 0, 0xFFFF do
  vram:write(string.char(memory.read_u8(i, "VRAM")))
end
vram:close()

-- Export the same-frame player geometry after the game has expanded its
-- descriptor into WRAM.  These parts are the missing evidence needed for a
-- faithful browser sprite: the running descriptor's pose is dynamic, so it
-- cannot be reconstructed from the static ROM alone.
local function u16(address)
  return mainmemory.read_u16_le(address)
end
local function s16(address)
  local value = u16(address)
  return value >= 0x8000 and value - 0x10000 or value
end
local function hex(value, width)
  return string.format("0x%0" .. width .. "X", value)
end
local sizes = {{8,16},{8,32},{8,64},{16,32},{16,64},{32,64},{16,32},{16,32}}
local obsel = mainmemory.read_u8(0x1EA6)
local players = assert(io.open(players_path, "w"))
players:write('{"evidence":"runtime-oam-capture","obsel":' .. obsel .. ',"actors":[')
local first_actor = true
for object = 0x0500, 0x1A00, 0x0100 do
  local descriptor, pose = u16(object + 0x14), u16(object)
  if mainmemory.read_u8(object + 0x30) ~= 0 and descriptor >= 0x8000 and pose ~= 0 and pose < 0xA000 then
    local count = mainmemory.read_u8(pose)
    if count > 0 and count <= 64 and pose + count * 2 <= 0xA000 then
      if not first_actor then players:write(',') end
      first_actor = false
      local object_props = mainmemory.read_u8(object + 3)
      local inherited = mainmemory.read_u8(object + 5)
      if inherited & 0x80 == 0 then inherited = mainmemory.read_u8(0x007C) end
      object_props = object_props | ((inherited & 0x30) | (mainmemory.read_u8(object + 4) & 0xF0))
      players:write('{"object":"' .. hex(object,4) .. '","descriptor":' .. descriptor .. ',"pose":' .. pose .. ',"direction":' .. u16(object + 0x2E) .. ',"type":' .. mainmemory.read_u8(object + 0x30) .. ',"kit_variant":' .. mainmemory.read_u8(object + 0x56) .. ',"uniform_selector":' .. mainmemory.read_u8(object + 0x57) .. ',"object_flags":' .. mainmemory.read_u8(object + 4) .. ',"parts":[')
      for index = 0, count - 1 do
        if index > 0 then players:write(',') end
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
        players:write('{"x":' .. (dx - (large and 8 or 4)) .. ',"y":' .. (s16(0x4000 + entry) - (large and 8 or 4)) .. ',"tile":' .. mainmemory.read_u8(0x6000 + entry) .. ',"size":' .. size .. ',"attr":' .. final_attr .. ',"palette":' .. ((final_attr >> 1) & 7) .. ',"priority":' .. ((final_attr >> 4) & 3) .. ',"h_flip":' .. tostring(final_attr & 0x40 ~= 0) .. ',"v_flip":' .. tostring(final_attr & 0x80 ~= 0) .. '}')
      end
      players:write(']}')
    end
  end
end
players:write(']}\n')
players:close()
console.writeline("ISSD OAM capture written: " .. output_path)
