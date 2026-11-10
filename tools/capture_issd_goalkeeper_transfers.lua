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
local save_frame_text=os.getenv('ISSD_KEEPER_SAVE_FRAME')
local save_frame=save_frame_text and tonumber(save_frame_text) or nil
assert(not save_frame_text or (boot_replay and save_frame and save_frame%1==0 and save_frame>0), 'Save-frame probe requires an isolated boot replay and positive frame')
local graphics=os.getenv('ISSD_KEEPER_CAPTURE_GRAPHICS')=='1'
local graphics_start_text=os.getenv('ISSD_KEEPER_GRAPHICS_START')
local graphics_end_text=os.getenv('ISSD_KEEPER_GRAPHICS_END')
local graphics_start=graphics_start_text and tonumber(graphics_start_text) or nil
local graphics_end=graphics_end_text and tonumber(graphics_end_text) or nil
assert((not graphics_start_text and not graphics_end_text) or (graphics and graphics_start and graphics_end and graphics_start%1==0 and graphics_end%1==0 and graphics_start>=0 and graphics_end>graphics_start and graphics_end-graphics_start<=180), 'Invalid bounded graphics capture window')
local function window(frame) return graphics_start and frame>=graphics_start and frame<graphics_end end
local drawout=graphics and assert(io.open(directory..'/keeper-draw.jsonl','w')) or nil
local function blob(path,size,read)
 local f=assert(io.open(path,'wb'))
 for i=0,size-1 do f:write(string.char(read(i))) end
 f:close()
end
local family=os.getenv('ISSD_KEEPER_GRAPHICS_FAMILY') or 'catch'
assert(family=='catch' or family=='release' or family=='dive', 'Invalid goalkeeper graphics family')
local families={
 catch={[0xe7c7]=true,[0xe7e3]=true,[0xe80a]=true},
 release={[0xe625]=true,[0xe644]=true,[0xe830]=true,[0xe4a7]=true},
 -- Scripts observed with dive-labelled graphics in the natural-play trace.
 dive={[0xe924]=true,[0xe94b]=true,[0xe96f]=true,[0xe996]=true,[0xe9a6]=true,[0xe9cd]=true,[0xe9f1]=true,[0xea18]=true},
}
local target=families[family]
local draw_handle
if graphics then
 draw_handle=event.onmemoryexecute(function()
  local oky,y=pcall(emu.getregister,'Y');local oks,stack=pcall(emu.getregister,'S')
  if not oky or not oks or type(y)~='number' or type(stack)~='number' then return end
  local interesting=not not window(emu.framecount())
  for actor=0x500,0x1a00,0x100 do if valid(actor) and target[u16(actor+0x1c)] then interesting=true end end
  if not interesting then return end
  local object=y>=0x1d40 and y<=0x1ffe and tostring(u16(y)) or 'null'
  drawout:write(string.format('{"frame":%d,"object":%s,"stack":%d}\n',emu.framecount(),object,stack))
 end,0x8095e3,'issd-keeper-draw')
 assert(draw_handle,'Unable to register keeper draw hook')
end
local release_trace=os.getenv('ISSD_KEEPER_TRACE_RELEASE')=='1'
local release_count=0
if release_trace then
 for _,entry in ipairs({{0x84ec89,'84EC89'},{0x84ec94,'84EC94'},{0x84ecae,'84ECAE'},{0x84eccb,'84ECCB'},{0x84ecef,'84ECEF'},{0x84ed0a,'84ED0A'},{0x85ee38,'85EE38'},{0x85ee00,'85EE00'},{0x85f8b9,'85F8B9'}}) do
  local address,name=entry[1],entry[2]
  local hook=event.onmemoryexecute(function()
   local ok,d=pcall(emu.getregister,'D')
   if not ok or not valid(d) then return end
   release_count=release_count+1
   out:write(string.format('{"type":"release_hook","frame":%d,"address":"%s","actor":%d,"state":%d,"script":%d,"descriptor":%d,"direction":%d,"timer70":%d,"field80":%d,"field82":%d,"link_a6":%d,"ball_x":%d,"ball_y":%d,"ball_z":%d,"ball_vx":%d,"ball_vy":%d,"ball_vz":%d,"ball_type":%d}\n',
    emu.framecount(),name,d,u16(d+0x32),u16(d+0x1c),u16(d+0x14),u16(d+0x2e),u16(d+0x70),u16(d+0x80),u16(d+0x82),u16(0xa6),u16(0x408),u16(0x40c),u16(0x410),u16(0x424),u16(0x428),u16(0x436),u16(0x430)))
  end,address,'issd-keeper-release-'..name)
  assert(hook,'Unable to register release hook')
 end
 for _,entry in ipairs({{0x8394a4,'8394A4'},{0x839e32,'839E32'},{0x839e92,'839E92'},{0x839ec3,'839EC3'},{0x83953f,'83953F'}}) do
  local address,name=entry[1],entry[2]
  local hook=event.onmemoryexecute(function()
   local okd,d=pcall(emu.getregister,'D');local oka,a=pcall(emu.getregister,'A')
   local okx,x=pcall(emu.getregister,'X');local oky,y=pcall(emu.getregister,'Y')
   if not okd or not oka or not okx or not oky or type(d)~='number' or type(a)~='number' or type(x)~='number' or type(y)~='number' then return end
   out:write(string.format('{"type":"ball_vector_hook","frame":%d,"address":"%s","d":%d,"a":%d,"x":%d,"y":%d,"ball_type":%d,"angle":%d,"parameter":%d,"table_value":%d,"link_a6":%d,"ball_vx":%d,"ball_vy":%d,"ball_vz":%d,"vx_fraction":%d,"vy_fraction":%d,"scratch00":%d,"scratch02":%d,"scratch04":%d,"scratch06":%d,"global_ac":%d,"global_ae":%d}\n',
    emu.framecount(),name,d,a,x,y,u16(0x430),u16(0x452),u16(0x456),u16(0x464),u16(0xa6),u16(0x424),u16(0x428),u16(0x436),u16(0x422),u16(0x426),u16(0),u16(2),u16(4),u16(6),u16(0xac),u16(0xae)))
  end,address,'issd-keeper-ball-vector-'..name)
  assert(hook,'Unable to register ball vector hook')
 end
end
local integration_trace=os.getenv('ISSD_KEEPER_TRACE_INTEGRATION')=='1'
if integration_trace then
 for _,entry in ipairs({{0x8389fb,'8389FB'},{0x838a1d,'838A1D'}}) do
  local address,name=entry[1],entry[2]
  local hook=event.onmemoryexecute(function()
   local ok,x=pcall(emu.getregister,'X')
   if not ok or x~=0x400 then return end
   out:write(string.format('{"type":"ball_integration","frame":%d,"address":"%s","xreg":%d,"ball_type":%d,"x_frac":%d,"x":%d,"y_frac":%d,"y":%d,"z_frac":%d,"z":%d,"vx_frac":%d,"vx":%d,"vy_frac":%d,"vy":%d,"vz_frac":%d,"vz":%d,"link_a6":%d}\n',
    emu.framecount(),name,x,u16(0x430),u16(0x406),u16(0x408),u16(0x40a),u16(0x40c),u16(0x40e),u16(0x410),u16(0x422),u16(0x424),u16(0x426),u16(0x428),u16(0x434),u16(0x436),u16(0xa6)))
  end,address,'issd-keeper-integration-'..name)
  assert(hook,'Unable to register ball integration hook')
 end
end
if os.getenv('ISSD_KEEPER_TRACE_POSITION_WRITES')=='1' then
 for _,address in ipairs({0x0406,0x0407,0x0408,0x0409,0x040a,0x040b,0x040c,0x040d,0x7e0406,0x7e0407,0x7e0408,0x7e0409,0x7e040a,0x7e040b,0x7e040c,0x7e040d}) do
  local hook=event.onmemorywrite(function()
   local okpc,pc=pcall(emu.getregister,'PC');local okpb,pb=pcall(emu.getregister,'PB')
   if not okpc or not okpb or type(pc)~='number' or type(pb)~='number' then return end
   out:write(string.format('{"type":"position_write","frame":%d,"watch":%d,"pc":%d,"pb":%d,"xfrac":%d,"x":%d,"yfrac":%d,"y":%d,"ball_type":%d}\n',emu.framecount(),address,pc,pb,u16(0x406),u16(0x408),u16(0x40a),u16(0x40c),u16(0x430)))
  end,address,string.format('issd-keeper-pos-%06X',address),'System Bus')
  assert(hook,'Unable to register position-write hook')
 end
end
if os.getenv('ISSD_KEEPER_TRACE_TRANSLATION')=='1' then
 for _,entry in ipairs({{0x83cfcb,'83CFCB'},{0x83cfe5,'83CFE5'}}) do
  local address,name=entry[1],entry[2]
  local hook=event.onmemoryexecute(function()
   out:write(string.format('{"type":"world_translation","frame":%d,"address":"%s","dx":%d,"dy":%d,"ball_x":%d,"ball_y":%d,"actor_x":%d,"actor_y":%d,"ball_type":%d}\n',emu.framecount(),name,u16(0xa0),u16(0xa2),u16(0x408),u16(0x40c),u16(0x508),u16(0x50c),u16(0x430)))
  end,address,'issd-keeper-translation-'..name)
  assert(hook,'Unable to register translation hook')
 end
end
if os.getenv('ISSD_KEEPER_TRACE_VERTICAL')=='1' then
 for _,entry in ipairs({{0x83941f,'83941F'},{0x83942e,'83942E'},{0x83943d,'83943D'},{0x839453,'839453'},{0x83946d,'83946D'},{0x83882a,'83882A'},{0x838863,'838863'},{0x838865,'838865'}}) do
  local address,name=entry[1],entry[2]
  local hook=event.onmemoryexecute(function()
   local oka,a=pcall(emu.getregister,'A');local okx,x=pcall(emu.getregister,'X')
   if not oka or not okx or type(a)~='number' or type(x)~='number' then return end
   out:write(string.format('{"type":"ball_vertical","a":%d,"xreg":%d,"frame":%d,"address":"%s","ball_type":%d,"z_frac":%d,"z":%d,"vz_frac":%d,"vz":%d,"gravity":%d,"link_a6":%d}\n',a,x,emu.framecount(),name,u16(0x430),u16(0x40e),u16(0x410),u16(0x434),u16(0x436),u16(0x458),u16(0xa6)))
  end,address,'issd-keeper-vertical-'..name)
  assert(hook,'Unable to register vertical hook')
 end
end
if os.getenv('ISSD_KEEPER_TRACE_BOUNCE')=='1' then
 for _,entry in ipairs({{0x83882a,'83882A'},{0x838941,'838941'},{0x83895d,'83895D'},{0x838962,'838962'},{0x838866,'838866'},{0x838883,'838883'},{0x83898d,'83898D'},{0x8389af,'8389AF'},{0x8389c4,'8389C4'},{0x8389ce,'8389CE'},{0x8388bb,'8388BB'}}) do
  local address,name=entry[1],entry[2]
  local hook=event.onmemoryexecute(function()
   local oka,a=pcall(emu.getregister,'A');local okx,x=pcall(emu.getregister,'X')
   if not oka or not okx or type(a)~='number' or type(x)~='number' or x~=0x400 then return end
   out:write(string.format('{"type":"bounce_hook","frame":%d,"address":"%s","a":%d,"ball_type":%d,"z":%d,"z_frac":%d,"vz":%d,"vz_frac":%d,"vx":%d,"vx_frac":%d,"vy":%d,"vy_frac":%d,"gravity":%d,"flags":%d,"parameter":%d,"weather":%d}\n',emu.framecount(),name,a,u16(0x430),u16(0x410),u16(0x40e),u16(0x436),u16(0x434),u16(0x424),u16(0x422),u16(0x428),u16(0x426),u16(0x458),u16(0x46e),u16(0x456),u16(0x1e4c)))
  end,address,'issd-keeper-bounce-'..name)
  assert(hook,'Unable to register bounce hook')
 end
end
if os.getenv('ISSD_KEEPER_TRACE_RECEIVE')=='1' then
 for _,entry in ipairs({{0x848cb1,'848CB1'},{0x848cdf,'848CDF'},{0x848d08,'848D08'},{0x848d25,'848D25'},{0x848d48,'848D48'},{0x85f05b,'85F05B'}}) do
  local address,name=entry[1],entry[2]
  local hook=event.onmemoryexecute(function()
   local ok,d=pcall(emu.getregister,'D')
   if not ok or type(d)~='number' or d<0x500 or d>0x1a00 or d%0x100~=0 or mainmemory.read_u8(d+0x30)<=1 then return end
   out:write(string.format('{"type":"receive_hook","frame":%d,"address":"%s","actor":%d,"actor_type":%d,"state":%d,"script":%d,"descriptor":%d,"direction":%d,"field68":%d,"field84":%d,"field86":%d,"ball_type":%d,"ball_z":%d,"link_a6":%d}\n',emu.framecount(),name,d,mainmemory.read_u8(d+0x30),u16(d+0x32),u16(d+0x1c),u16(d+0x14),u16(d+0x2e),u16(d+0x68),u16(d+0x84),u16(d+0x86),u16(0x430),u16(0x410),u16(0xa6)))
  end,address,'issd-receive-'..name)
  assert(hook,'Unable to register receive hook')
 end
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
local trace_team=os.getenv('ISSD_KEEPER_TRACE_TEAM')=='1'
local frame_handle=event.onframeend(function()
 if trace_team then
  local keeper_team=u16(0x59a)
  for actor=0x500,0x1a00,0x100 do
   if mainmemory.read_u8(actor+0x30)>1 and u16(actor+0x9a)==keeper_team then
    out:write(string.format('{"type":"team_sample","frame":%d,"actor":%d,"actor_type":%d,"team":%d,"state":%d,"script":%d,"direction":%d,"x":%d,"x_frac":%d,"y":%d,"y_frac":%d,"ball_x":%d,"ball_x_frac":%d,"ball_y":%d,"ball_y_frac":%d,"ball_z":%d,"ball_type":%d,"link_a6":%d,"selected":%d}\n',
      emu.framecount(),actor,mainmemory.read_u8(actor+0x30),u16(actor+0x9a),u16(actor+0x32),u16(actor+0x1c),u16(actor+0x2e),u16(actor+8),u16(actor+6),u16(actor+12),u16(actor+10),u16(0x408),u16(0x406),u16(0x40c),u16(0x40a),u16(0x410),u16(0x430),u16(0xa6),u16(0x1acc)))
   end
  end
 end
 if save_frame and emu.framecount()==save_frame then
  local filename=directory..'/keeper-start.State'
  local ok=savestate.save(filename,true)
  out:write(string.format('{"type":"state_saved","frame":%d,"success":%s}\n',emu.framecount(),tostring(not not ok)))
  assert(ok,'Unable to save goalkeeper replay state')
 end
 for actor=0x500,0x1a00,0x100 do
  if valid(actor) then
   sample_count=sample_count+1
   if graphics and ((graphics_start and window(emu.framecount())) or (not graphics_start and target[u16(actor+0x1c)])) then
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
out:write(string.format('{"type":"session_end","transfers":%d,"keeper_frames":%d,"release_hooks":%d}\n',transfer_count,sample_count,release_count))
out:close()
if drawout then drawout:close() end
