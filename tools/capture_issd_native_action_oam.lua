-- Passive native-OAM capture for ISS Deluxe in BizHawk.
-- Captures the real OAM buffer, not guessed WRAM work-plane geometry.
-- Run DURING a real match. It does not modify buttons, RAM or ROM.
-- IMPORTANT: edit root to the absolute docs/ directory on your PC.
local root = "C:/Users/evandro.mota/Documents/REA-FUTEBOL/docs/"
local output_path = root .. "issd-native-action-oam.jsonl"
local capture_frames = 18000
local max_snapshots = 160
local max_repeats_per_actor_pose = 2
local repeat_gap_frames = 3

-- Focus on actual action families, not thousands of idle poses.
-- $D100 is associated with LowKick graphics, but *not yet* confirmed as pass.
local target_scripts = {
  [0xD007] = true, -- strong kick
  [0xD100] = true, -- alternate kick/LowKick
  [0xDB25] = true, -- slide
  [0xDB5B] = true, -- get up
}

local function u16(address) return mainmemory.read_u16_le(address) end
local function s16(address)
  local value = u16(address)
  return value >= 0x8000 and value - 0x10000 or value
end

local function write_blob(path, size, reader)
  local out = assert(io.open(path, "wb"))
  for i = 0, size - 1 do out:write(string.char(reader(i))) end
  out:close()
end

local function write_vram(path)
  write_blob(path, 65536, function(i) return memory.read_u8(i, "VRAM") end)
end

local function write_oam_mirror(path)
  -- ISS Deluxe's OAM mirror in $7E:01E0..03FF (544 bytes):
  -- low 512 bytes are DMA reversed; high 32 bytes are forward-ordered.
  -- Preserve all 544 RAW bytes, do not infer individual player parts.
  write_blob(path, 544, function(i) return mainmemory.read_u8(0x01E0 + i) end)
end

local function write_cgram(path)
  -- The same $7E:2C00 CGRAM mirror used in existing successful captures.
  local out = assert(io.open(path, "w"))
  for i = 0, 511 do
    out:write(string.format("%02X", mainmemory.read_u8(0x2C00 + i)))
    if i % 32 == 31 then out:write("\n") end
  end
  out:close()
end

local function oam_ppu_available()
  -- Some BizHawk SNES cores expose a hardware OAM memory domain.
  -- Capture it when present, but never assume it exists.
  local ok, value = pcall(function() return memory.read_u8(0, "OAM") end)
  return ok and type(value) == "number"
end

local function write_oam_ppu(path)
  -- Hardware OAM low 512 bytes are already forward-ordered, unlike mirror.
  write_blob(path, 544, function(i) return memory.read_u8(i, "OAM") end)
end

local function actor_active(address)
  return mainmemory.read_u8(address + 0x30) ~= 0
    and u16(address + 0x14) >= 0x8000
end

local output = assert(io.open(output_path, "w"))
local seen, frame, captured, closed = {}, 0, 0, false
local has_ppu = oam_ppu_available()

local function snapshot(address, script, direction, descriptor)
  captured = captured + 1
  local basename = string.format(
    "issd-native-oam-%04X-%d-%04X-%04X-%03d",
    script, direction, descriptor, address, captured
  )
  local oam_name = basename .. "-mirror.bin"
  local ppu_name = basename .. "-ppu.bin"
  local vram_name = basename .. "-vram.bin"
  local cgram_name = basename .. "-cgram.hex"
  local screenshot_name = basename .. "-screen.png"

  -- Take all sources in the SAME frame-end callback.
  write_oam_mirror(root .. oam_name)
  local ppu_ok = has_ppu and pcall(write_oam_ppu, root .. ppu_name)
  write_vram(root .. vram_name)
  write_cgram(root .. cgram_name)
  local shot_ok = pcall(function() client.screenshot(root .. screenshot_name) end)

  local x_origin = s16(address + 0x08)
  local y_origin = s16(address + 0x0C)
  local y_offset = s16(address + 0x10)
  output:write(string.format(
    '{"schema":"issd-native-action-oam/v1","frame":%d,"obsel":%d,"oam_mirror":"%s","oam_mirror_encoding":"low-512-reversed-high-32-forward","oam_ppu":%s,"vram":"%s","cgram":"%s","screenshot":%s,"actor":',
    frame, mainmemory.read_u8(0x1EA6), oam_name,
    ppu_ok and ('"' .. ppu_name .. '"') or "null", vram_name, cgram_name,
    shot_ok and ('"' .. screenshot_name .. '"') or "null"
  ))
  output:write(string.format(
    '{"address":%d,"animation_script":%d,"direction":%d,"descriptor":%d,"pose":%d,"animation_timer":%d,"animation_duration":%d,"animation_cursor":%d,"object_field_02":%d,"origin_x_raw":%d,"origin_y_raw":%d,"origin_y_offset_raw":%d,"object_flags":%d,"type":%d}',
    address, script, direction, descriptor, u16(address), u16(address + 0x16),
    u16(address + 0x18), u16(address + 0x1A),
    u16(address + 0x02), x_origin, y_origin, y_offset,
    mainmemory.read_u8(address + 0x04), mainmemory.read_u8(address + 0x30)
  ))
  output:write(',"limitations":"Raw OAM contains every visible object. Actor-to-OAM-slot assignment and exact action timing are NOT inferred."}\n')
  output:flush()
end

local function capture_frame()
  if closed then return end
  frame = frame + 1
  for address = 0x0500, 0x1A00, 0x100 do
    if captured >= max_snapshots then break end
    if actor_active(address) then
      local script = u16(address + 0x1C)
      if target_scripts[script] then
        local direction, descriptor = u16(address + 0x2E), u16(address + 0x14)
        local key = string.format("%04X-%d-%04X-%04X", script, direction, descriptor, address)
        local old = seen[key]
        if not old or (old.count < max_repeats_per_actor_pose and frame - old.last >= repeat_gap_frames) then
          snapshot(address, script, direction, descriptor)
          seen[key] = {count = (old and old.count or 0) + 1, last = frame}
        end
      end
    end
  end
  if frame >= capture_frames or captured >= max_snapshots then
    output:close()
    closed = true
    console.writeline("ISSD native action OAM written: " .. output_path)
    console.writeline("Snapshots saved: " .. captured)
  end
end

event.onframeend(capture_frame, "issd-native-action-oam-capture")
console.writeline("ISSD native action OAM capture running (passive). OAM domain: " .. (has_ppu and "available" or "mirror only"))
