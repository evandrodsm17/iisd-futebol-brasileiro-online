-- Read-only hooks in an isolated replay; no game memory is changed.
local directory=assert(os.getenv('ISSD_AUTO_OUTPUT_DIR'),'Missing output directory')
assert(os.getenv('ISSD_AUTO_REPLAY_STATE'),'An isolated replay is required')
local out=assert(io.open(directory..'/slide-reaction-choice.jsonl','w'))
local function u16(a)return mainmemory.read_u16_le(a)end
local function reg(n)local ok,v=pcall(emu.getregister,n);return ok and type(v)=='number' and v or -1 end
local first=tonumber(os.getenv('ISSD_REACTION_START_FRAME') or '4210')
local last=tonumber(os.getenv('ISSD_REACTION_END_FRAME') or '4235')
local attacker=tonumber(os.getenv('ISSD_REACTION_ATTACKER') or '3328')
local target=tonumber(os.getenv('ISSD_REACTION_TARGET') or '6400')
local sites={[0x80eed3]='choice_entry',[0x80e8dc]='record_return',[0x80ef7a]='store_reaction',[0x84a346]='dispatch'}
for address,site in pairs(sites)do
 assert(event.onmemoryexecute(function()
  local frame=emu.framecount();if frame<first or frame>last then return end
  local d,x,a,y,p=reg('D'),reg('X'),reg('A'),reg('Y'),reg('P')
  if site=='choice_entry' and (d~=attacker or x~=target) then return end
  if site=='record_return' and d~=target then return end
  if site=='store_reaction' and (d~=attacker or x~=target) then return end
  if site=='dispatch' and d~=target then return end
  local record=x>=0 and x<=0xfff9
  out:write(string.format('{"frame":%d,"site":"%s","d":%d,"x":%d,"a":%d,"y":%d,"p":%d,"attacker30":%d,"attacker60":%d,"target30":%d,"target60":%d,"target68":%d,"target6c":%d,"target6e":%d,"target76":%d,"target78":%d,"global78":%d,"global11f9":%d,"globalc0":%d,"ball_owner":%d,"record_word":%d,"record_next_word":%d,"record_sixth_word":%d}\n',
   frame,site,d,x,a,y,p,u16(attacker+0x30),u16(attacker+0x60),u16(target+0x30),u16(target+0x60),u16(target+0x68),u16(target+0x6c),u16(target+0x6e),u16(target+0x76),u16(target+0x78),u16(0x78),u16(0x11f9),u16(0xc0),u16(0xa6),record and u16(x) or -1,record and u16(x+1) or -1,record and u16(x+6) or -1))
  out:flush()
 end,address,'issd-reaction-'..site),'Failed to register '..site)
end
dofile(assert(os.getenv('ISSD_AUTO_PROBE_SCRIPT'),'Missing replay driver'))
out:close()
