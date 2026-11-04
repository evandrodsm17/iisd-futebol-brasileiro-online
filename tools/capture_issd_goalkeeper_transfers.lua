-- Read-only goalkeeper transfer observer around the ordinary isolated replay.
-- The descriptor at entry is X; $00 is the actor's current pose. Capture the
-- guards before execution, then sample actors at frame end. A frame-end sample
-- is not a claim about the PPU image or the outcome of a particular call.
local directory=assert(os.getenv('ISSD_AUTO_OUTPUT_DIR'),'Missing output directory')
local boot_replay=os.getenv('ISSD_KEEPER_BOOT_REPLAY')=='1'
assert(os.getenv('ISSD_AUTO_REPLAY_STATE') or (boot_replay and os.getenv('ISSD_AUTO_SCENARIO')=='opponent_link'), 'An isolated state replay or explicit opponent_link boot replay is required')
local out=assert(io.open(directory..'/keeper-transfers.jsonl','w'))
local function u16(a) return mainmemory.read_u16_le(a) end
local actor_text=os.getenv('ISSD_KEEPER_TRACE_ACTOR')
local selected=actor_text and tonumber(actor_text) or nil
assert(not actor_text or (selected and selected>=0x500 and selected<=0x1a00 and selected%0x100==0),'Invalid goalkeeper actor')
local function valid(actor)
 return actor and actor>=0x500 and actor<=0x1a00 and actor%0x100==0 and
   (not selected or selected==actor) and mainmemory.read_u8(actor+0x30)==1
end
local graphics=os.getenv('ISSD_KEEPER_CAPTURE_GRAPHICS')=='1'
local drawout=graphics and assert(io.open(directory..'/keeper-draw.jsonl','w')) or nil
local function blob(path,size,read)
 local f=assert(io.open(path,'wb'))
 for i=0,size-1 do f:write(string.char(read(i))) end
 f:close()
end
local target={[0xe7c7]=true,[0xe7e3]=true,[0xe80a]=true}
local draw_handle
if graphics then
 draw_handle=event.onmemoryexecute(function()
  local oky,y=pcall(emu.getregister,'Y');local oks,stack=pcall(emu.getregister,'S')
  if not oky or not oks or type(y)~='number' or type(stack)~='number' then return end
  local interesting=false
  for actor=0x500,0x1a00,0x100 do if valid(actor) and target[u16(actor+0x1c)] then interesting=true end end
  if not interesting then return end
  local object=y>=0x1d40 and y<=0x1ffe and tostring(u16(y)) or 'null'
  drawout:write(string.format('{"frame":%d,"object":%s,"stack":%d}\n',emu.framecount(),object,stack))
 end,0x8095e3,'issd-keeper-draw')
 assert(draw_handle,'Unable to register keeper draw hook')
end
local transfer_count=0
local transfer=event.onmemoryexecute(function()
 local okd,d=pcall(emu.getregister,'D');local okx,x=pcall(emu.getregister,'X')
 if not okd or not okx or not valid(d) or type(x)~='number' then return end
 local guard_actor=u16(d+0x1e);local guard_global=u16(0x14e4)
 local used=u16(0x11e0);local limit=u16(0x11e2)
 transfer_count=transfer_count+1
 out:write(string.format('{"type":"transfer_entry","frame":%d,"actor":%d,"requested_descriptor":%d,"previous_descriptor":%d,"previous_pose":%d,"guard_actor":%d,"guard_global":%d,"dma_used":%d,"dma_limit":%d,"guards_allow":%s,"script":%d,"state":%d}\n',
  emu.framecount(),d,x,u16(d+0x14),u16(d),guard_actor,guard_global,used,limit,
  tostring(guard_actor==0 and guard_global==0 and used<limit),u16(d+0x1c),u16(d+0x32)))
end,0x84e6c7,'issd-keeper-transfer-entry')
assert(transfer,'Unable to register transfer hook')
local sample_count=0
local frame_handle=event.onframeend(function()
 for actor=0x500,0x1a00,0x100 do
  if valid(actor) then
   sample_count=sample_count+1
   if graphics and target[u16(actor+0x1c)] then
    local stem=string.format('keeper-%04X-%d',actor,emu.framecount())
    blob(directory..'/'..stem..'-mirror.bin',544,function(i)return mainmemory.read_u8(0x1e0+i)end)
    blob(directory..'/'..stem..'-vram.bin',65536,function(i)return memory.read_u8(i,'VRAM')end)
    local ppu=pcall(function() blob(directory..'/'..stem..'-ppu.bin',544,function(i)return memory.read_u8(i,'OAM')end) end)
    local cgram=pcall(function() blob(directory..'/'..stem..'-cgram.bin',512,function(i)return memory.read_u8(i,'CGRAM')end) end)
    local screenshot=pcall(client.screenshot,directory..'/'..stem..'-screen.png')
    out:write(string.format('{"type":"graphics","frame":%d,"actor":%d,"stem":"%s","ppu":%s,"cgram":%s,"screenshot":%s,"obsel":%d}\n',emu.framecount(),actor,stem,tostring(ppu),tostring(cgram),tostring(screenshot),mainmemory.read_u8(0x1ea6)))
   end
   out:write(string.format('{"type":"keeper_frame","frame":%d,"actor":%d,"state":%d,"script":%d,"descriptor":%d,"pose":%d,"direction":%d,"ball_x":%d,"ball_y":%d,"ball_z":%d,"ball_vx":%d,"ball_vy":%d,"ball_vz":%d,"carrier":%d,"held_p1":%d,"held_p2":%d}\n',
    emu.framecount(),actor,u16(actor+0x32),u16(actor+0x1c),u16(actor+0x14),u16(actor),u16(actor+0x2e),
    u16(0x408),u16(0x40c),u16(0x410),u16(0x424),u16(0x428),u16(0x436),u16(0x1b90),u16(0x20),u16(0x22)))
  end
 end
end,'issd-keeper-frame')
assert(frame_handle,'Unable to register keeper frame hook')
out:write('{"type":"session_start","schema":"issd-keeper-transfers/v1","timing":"transfer entry before execution; frame samples at frame end","memory_modified":false}\n')
dofile(assert(os.getenv('ISSD_AUTO_PROBE_SCRIPT'),'Missing replay driver'))
out:write(string.format('{"type":"session_end","transfers":%d,"keeper_frames":%d}\n',transfer_count,sample_count))
out:close()
if drawout then drawout:close() end
