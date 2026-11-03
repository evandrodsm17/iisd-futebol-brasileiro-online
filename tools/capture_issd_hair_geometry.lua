-- Read-only snapshot from an isolated, existing match state. Never writes ROM.
local output=assert(os.getenv('ISSD_HAIR_GEOMETRY_OUTPUT'),'Missing output path')
local state=assert(os.getenv('ISSD_HAIR_GEOMETRY_STATE'),'Missing isolated replay state')
assert(savestate.load(state,true),'Failed to load replay state')
local file=assert(io.open(output,'w'))
local function u16(a) return mainmemory.read_u16_le(a) end
for _,range in ipairs({{0x4E68,52},{0x4ED0,15},{0x4EEE,15},{0x4F0C,40},{0x4F5C,30},{0x4F98,15}}) do
  for i=0,range[2]-1 do
    local pointer=range[1]+2*i
    file:write(string.format('{"pointer":%d,"x_word":%d,"y_word":%d,"tile":%d,"attr":%d}\n',
      pointer,u16(0x2000+pointer),u16(0x4000+pointer),mainmemory.read_u8(0x6000+pointer),mainmemory.read_u8(0x6001+pointer)))
  end
end
file:close()
print('Read-only geometry snapshot complete: '..output)
