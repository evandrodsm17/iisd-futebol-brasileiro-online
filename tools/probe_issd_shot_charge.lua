-- Observe native action charge and release paths in a saved two-player replay.
local root=assert(os.getenv('ISSD_CHARGE_OUTPUT'));local out=assert(io.open(root..'/charge-hooks.jsonl','w'))
local function u(a)return mainmemory.read_u16_le(a)end
local function reg(n)local ok,v=pcall(emu.getregister,n);return ok and type(v)=='number' and v or -1 end
local hooks={{0x80da3c,'80DA3C'},{0x80da65,'80DA65'},{0x80da68,'80DA68'},{0x85f685,'85F685'},{0x85f694,'85F694'},{0x85f6ba,'85F6BA'},{0x85f70c,'85F70C'},{0x85f72a,'85F72A'},{0x85f75f,'85F75F'},{0x85f871,'85F871'},{0x85f89b,'85F89B'},{0x85f8d6,'85F8D6'}}
for _,h in ipairs(hooks) do local addr,name=h[1],h[2]
 assert(event.onmemoryexecute(function()
  local d=reg('D');if d~=0x1900 then return end
  out:write(string.format('{"frame":%d,"site":"%s","d":%d,"a":%d,"x":%d,"y":%d,"flags6e":%d,"flags60":%d,"charge":%d,"mask":%d,"actorDir":%d,"script":%d,"heldP2":%d,"carrier":%d,"ballType":%d,"ballVZ":%d}\n',emu.framecount(),name,d,reg('A'),reg('X'),reg('Y'),u(d+0x6e),u(d+0x60),u(d+0x82),u(d+0x80),u(d+0x2e),u(d+0x1c),u(0x22),u(0xa6),u(0x430),u(0x436)));out:flush()
 end,addr,'native-charge-'..name))
end
out:write('{"type":"session_start","actor":6400}\n');out:flush()
dofile(assert(os.getenv('ISSD_AUTO_PROBE_SCRIPT')))
out:write('{"type":"session_end"}\n');out:close();client.exit()
