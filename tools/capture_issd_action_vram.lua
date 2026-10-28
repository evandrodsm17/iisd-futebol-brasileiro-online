-- Passive ISS Deluxe action capture for BizHawk.
--
-- Run only in a real match. It never sends controller input and never writes
-- to ROM/RAM. For each new observed action descriptor it saves the OAM-derived
-- player parts plus VRAM and CGRAM from that same emulated frame.

local root = "C:/Users/evandro.mota/Documents/REA-FUTEBOL/docs/"
local output_path = root .. "issd-action-vram-trace.jsonl"
local capture_frames = 18000
local target_scripts = { [0xD007] = true, [0xD100] = true, [0xD6DB] = true, [0xDB25] = true, [0xDB5B] = true }
local sizes = {{8,16},{8,32},{8,64},{16,32},{16,64},{32,64},{16,32},{16,32}}

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

local function write_vram(path)
  local file = assert(io.open(path, "wb"))
  for index = 0, 0xFFFF do file:write(string.char(memory.read_u8(index, "VRAM"))) end
  file:close()
end

local function write_cgram(path)
  local file = assert(io.open(path, "w"))
  for index = 0, 0x1FF do
    file:write(string.format("%02X", mainmemory.read_u8(0x2C00 + index)))
    if index % 32 == 31 then file:write("\n") end
  end
  file:close()
end

local function write_actor(file, address, obsel)
  local descriptor, pose = u16(address + 0x14), u16(address)
  local count = mainmemory.read_u8(pose)
  local object_props, inherited = mainmemory.read_u8(address + 3), mainmemory.read_u8(address + 5)
  if inherited & 0x80 == 0 then inherited = mainmemory.read_u8(0x007C) end
  object_props = object_props | ((inherited & 0x30) | (mainmemory.read_u8(address + 4) & 0xF0))
  file:write(string.format('{"address":%d,"animation_handler":%d,"animation_script":%d,"animation_timer":%d,"animation_duration":%d,"animation_cursor":%d,"type":%d,"kit_variant":%d,"uniform_selector":%d,"object_flags":%d,"descriptor":%d,"pose":%d,"direction":%d,"parts":[',
    address, u16(address + 0x92), u16(address + 0x1C), u16(address + 0x16), u16(address + 0x18), u16(address + 0x1A), mainmemory.read_u8(address + 0x30), mainmemory.read_u8(address + 0x56), mainmemory.read_u8(address + 0x57), mainmemory.read_u8(address + 4), descriptor, pose, u16(address + 0x2E)))
  for index = 0, count - 1 do
    if index > 0 then file:write(",") end
    local entry = pose + index * 2
    local attr = mainmemory.read_u8(0x6001 + entry)
    local large = mainmemory.read_u8(entry + 1) & 0x80 ~= 0
    local final_attr = (attr & 0xC1) ~ object_props
    if attr & 0x20 ~= 0 then
      if final_attr & 0x08 ~= 0 then final_attr = final_attr | 0x02 else final_attr = (final_attr & 0xFB) | 0x08 end
    end
    local dx = s16(0x2000 + entry)
    if object_props & 0x40 ~= 0 then dx = -dx end
    file:write(string.format('{"x":%d,"y":%d,"tile":%d,"size":%d,"attr":%d}',
      dx - (large and 8 or 4), s16(0x4000 + entry) - (large and 8 or 4),
      mainmemory.read_u8(0x6000 + entry), sizes[(obsel >> 5) + 1][large and 2 or 1], final_attr))
  end
  file:write("]}")
end

local output = assert(io.open(output_path, "w"))
local seen, frame, closed = {}, 0, false
local function capture_frame()
  if closed then return end
  frame = frame + 1
  local obsel = mainmemory.read_u8(0x1EA6)
  for address = 0x0500, 0x1A00, 0x100 do
    if actor_is_capturable(address) then
      local script, direction, descriptor = u16(address + 0x1C), u16(address + 0x2E), u16(address + 0x14)
      if target_scripts[script] then
        local key = string.format("%04X-%d-%04X", script, direction, descriptor)
        if not seen[key] then
          seen[key] = true
          local prefix = root .. "issd-action-vram-" .. key
          write_vram(prefix .. ".bin")
          write_cgram(prefix .. "-cgram.hex")
          output:write(string.format('{"frame":%d,"obsel":%d,"vram":"%s.bin","cgram":"%s-cgram.hex","actor":', frame, obsel, prefix, prefix))
          write_actor(output, address, obsel)
          output:write("}\n")
          output:flush()
        end
      end
    end
  end
  if frame >= capture_frames then
    output:close()
    closed = true
    console.writeline("ISSD action VRAM trace written: " .. output_path)
  end
end

event.onframeend(capture_frame, "issd-action-vram-capture")
console.writeline("ISSD action VRAM capture armed for " .. capture_frames .. " frames")
