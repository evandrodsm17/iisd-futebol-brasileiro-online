-- Captures the SNES OAM mirror used by ISS Deluxe after booting a local ROM.
-- Run with BizHawk's --lua flag.  It writes only the runtime OAM bytes needed
-- for visual reconstruction; neither the ROM nor a save state is exported.

local output_path = "C:/Users/evandro.mota/Documents/REA-FUTEBOL/docs/issd-runtime-oam.hex"
local planes_path = "C:/Users/evandro.mota/Documents/REA-FUTEBOL/docs/issd-runtime-oam-planes.hex"
local domains_path = "C:/Users/evandro.mota/Documents/REA-FUTEBOL/docs/issd-memory-domains.txt"
local capture_frame = 3600

local domains = assert(io.open(domains_path, "w"))
for _, name in ipairs(memory.getmemorydomainlist()) do domains:write(name .. "\n") end
domains:close()

for frame = 1, capture_frame do
  -- Default menu progression: start the title/menu, then accept the default
  -- exhibition configuration.  The capture is still useful if a menu pauses.
  if frame % 180 == 0 or frame % 180 == 1 then
    joypad.set({ Start = true }, 1)
  else
    joypad.set({}, 1)
  end
  emu.frameadvance()
end

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
console.writeline("ISSD OAM capture written: " .. output_path)
