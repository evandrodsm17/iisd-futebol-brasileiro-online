-- ISSD / BizHawk: read-only memory-domain probe and available-domain snapshots.
-- Start during a match via Tools > Lua Console > Open Script.
-- The first snapshot happens immediately. Press P1 Select+L+R to capture again.
-- Outputs contain NO ROM dump: only the allowed PPU memory domains if exposed.
local output = 'issd_capture'
os.execute('mkdir "' .. output .. '" 2>nul')
local function domains()
  local names = memory.getmemorydomainlist()
  print('Memory domains:')
  for i, name in ipairs(names) do
    local ok, size = pcall(memory.getmemorydomainsize, name)
    print(string.format('  %s  size=%s', name, ok and tostring(size) or '?'))
  end
  return names
end
local list = domains()
local function find(name)
  for _, v in ipairs(list) do if string.lower(v) == string.lower(name) then return v end end
  return nil
end
local function snapshot(domain, size, filename)
  local name = find(domain)
  if not name then print(domain .. ' not exposed by current core.'); return end
  local ok, length = pcall(memory.getmemorydomainsize, name)
  if not ok or length < size then print(domain .. ' has insufficient size.'); return end
  local f, err = io.open(filename, 'wb')
  if not f then print('Cannot open ' .. filename .. ': ' .. tostring(err)); return end
  local bytes = {}
  for i = 0, size-1 do
    bytes[#bytes+1] = string.char(memory.read_u8(i, name))
    if #bytes == 1024 then f:write(table.concat(bytes)); bytes = {} end
  end
  if #bytes > 0 then f:write(table.concat(bytes)) end
  f:close()
  print('Saved ' .. filename)
end
local counter = 0
local function capture()
  counter = counter + 1
  local prefix = string.format('%s/frame_%04d', output, counter)
  snapshot('VRAM', 65536, prefix .. '_vram.bin')
  snapshot('OAM', 544, prefix .. '_oam.bin')
  snapshot('CGRAM', 512, prefix .. '_cgram.bin')
  print('Capture ' .. counter .. ' @ emulator frame ' .. emu.framecount())
end
capture()
local previously = false
while true do
  local buttons = joypad.get(1)
  local active = buttons.Select and buttons.L and buttons.R
  if active and not previously then capture() end
  previously = active
  emu.frameadvance()
end
