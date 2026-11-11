-- Capture ball-release execution during an isolated, read-only scenario replay.
local directory=assert(os.getenv('ISSD_THROW_OUTPUT'),'Missing output directory')
local driver=assert(os.getenv('ISSD_THROW_DRIVER'),'Missing replay driver')
local out=assert(io.open(directory..'/release-hooks.jsonl','w'))
local function u16(a)return mainmemory.read_u16_le(a)end
local function reg(name)local ok,v=pcall(emu.getregister,name);return ok and type(v)=='number' and v or -1 end
for _,entry in ipairs({{0x85EF51,'85EF51'},{0x85EFB4,'85EFB4'},{0x85F8B9,'85F8B9'},{0x8394A4,'8394A4'},{0x839E32,'839E32'},{0x839E92,'839E92'},{0x839EC3,'839EC3'},{0x83953F,'83953F'}}) do
 local address,name=entry[1],entry[2]
 local handle=event.onmemoryexecute(function()
  local frame=emu.framecount()
  if frame<2255 or frame>2295 then return end
  local d=reg('D')
  out:write(string.format('{"frame":%d,"address":"%s","d":%d,"a":%d,"x":%d,"y":%d,"ball_type":%d,"link_a6":%d,"phase":%d,"ball_vx":%d,"ball_vy":%d,"ball_vz":%d,"vx_fraction":%d,"vy_fraction":%d,"vz_fraction":%d,"scratch00":%d,"scratch02":%d,"scratch04":%d,"scratch06":%d,"global_ac":%d,"global_ae":%d}\n',frame,name,d,reg('A'),reg('X'),reg('Y'),u16(0x430),u16(0xa6),u16(0xc0),u16(0x424),u16(0x428),u16(0x436),u16(0x422),u16(0x426),u16(0x434),u16(0),u16(2),u16(4),u16(6),u16(0xac),u16(0xae)))
  out:flush()
 end,address,'issd-throw-release-'..name)
 assert(handle,'Unable to register release hook '..name)
end
dofile(driver)
out:write('{"type":"done"}\n');out:close()
