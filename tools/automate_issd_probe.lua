-- Isolated experimental navigation. Does not modify ROM; optional replay loads a savestate.
-- A menu pulse is a probe, not evidence that a match has started.
local directory = os.getenv('ISSD_AUTO_OUTPUT_DIR') or 'C:/Users/evandro.mota/Documents/REA-FUTEBOL/analysis'
local stem = directory .. '/issd-auto-probe-' .. os.date('%Y%m%d-%H%M%S')
local base = stem
local suffix = 0
while true do
  local existing = io.open(base .. '.jsonl', 'r')
  if not existing then break end
  existing:close()
  suffix = suffix + 1
  base = stem .. '-' .. suffix
end
local output_path = base .. '.jsonl'
local out = assert(io.open(output_path, 'w'))
local function u16(a) return mainmemory.read_u16_le(a) end
local opponent_scenario = os.getenv('ISSD_AUTO_SCENARIO') == 'opponent_link'
local action_observation = os.getenv('ISSD_AUTO_SCENARIO') == 'two_player_action_observation'
local p2_action_enabled = os.getenv('ISSD_AUTO_P2_ACTION') ~= '0'
local p2_action_button = os.getenv('ISSD_AUTO_P2_BUTTON') or 'A'
assert(p2_action_button == 'A' or p2_action_button == 'B' or p2_action_button == 'X' or p2_action_button == 'Y', 'Invalid P2 action button')
local p2_move_button = os.getenv('ISSD_AUTO_P2_MOVE') or 'Right'
local p2_move_inputs = {
  Right={Right=true}, Left={Left=true}, Up={Up=true}, Down={Down=true},
  UpRight={Up=true,Right=true}, UpLeft={Up=true,Left=true},
  DownRight={Down=true,Right=true}, DownLeft={Down=true,Left=true},
}
assert(p2_move_inputs[p2_move_button], 'Invalid P2 movement button')
local p2_action_direction = os.getenv('ISSD_AUTO_P2_ACTION_DIRECTION')
assert(not p2_action_direction or p2_move_inputs[p2_action_direction], 'Invalid P2 action direction')
local controlled_experiment = action_observation or os.getenv('ISSD_AUTO_SCENARIO') == 'two_player_experiment'
local two_player_scenario = controlled_experiment or os.getenv('ISSD_AUTO_SCENARIO') == 'two_player_probe'
local target_frames = opponent_scenario and 10000 or (action_observation and 7500 or (controlled_experiment and 6500 or 4800))
local trigger_step = nil
local stable_frames = 0
local experiment_step = nil
local initial_clock = nil
local current_step = 0
local trace_execution = os.getenv('ISSD_AUTO_TRACE_EXEC') == '1'
local trace_draw = os.getenv('ISSD_AUTO_DRAW_TRACE') == '1'
local trace_selection = os.getenv('ISSD_AUTO_SELECTION_TRACE') == '1'
local trace_input_origin = os.getenv('ISSD_AUTO_INPUT_ORIGIN_TRACE') == '1'
local trace_alternate = os.getenv('ISSD_AUTO_ALTERNATE_TRACE') == '1'
local trace_ball_update = os.getenv('ISSD_AUTO_BALL_UPDATE_TRACE') == '1'
local force_geometry_68 = os.getenv('ISSD_AUTO_GEOMETRY_TEST_FORCE_68_ZERO') == '1'
assert(not force_geometry_68 or (trace_ball_update and os.getenv('ISSD_AUTO_REPLAY_STATE')), 'Synthetic geometry probe requires an isolated replay and ball tracing')
local forced_geometry_actor, forced_geometry_original = nil, nil
local ball_trace_start = tonumber(os.getenv('ISSD_AUTO_BALL_TRACE_START') or '480')
local ball_trace_end = tonumber(os.getenv('ISSD_AUTO_BALL_TRACE_END') or '510')
assert(ball_trace_start and ball_trace_end and ball_trace_start >= 0 and ball_trace_end <= 650 and ball_trace_start <= ball_trace_end, 'Invalid ball trace window')
local trace_ball_writes = os.getenv('ISSD_AUTO_BALL_WRITES_TRACE') == '1'
-- Some cores reach the player-selection screen later. Opt in explicitly;
-- once a stable match is detected, the controlled experiment takes over.
local extended_menu = os.getenv('ISSD_AUTO_EXTENDED_MENU') == '1'
local action_every_frame = os.getenv('ISSD_AUTO_ACTION_EVERY_FRAME') == '1'
local save_trigger = os.getenv('ISSD_AUTO_SAVE_TRIGGER') == '1'
local replay_state = os.getenv('ISSD_AUTO_REPLAY_STATE')
assert(not replay_state or action_observation, 'Replay requires two_player_action_observation')
local capture_graphics = os.getenv('ISSD_AUTO_CAPTURE_GRAPHICS') == '1'
local graphics_every_frame = os.getenv('ISSD_AUTO_GRAPHICS_EVERY_FRAME') == '1'
assert(not capture_graphics or replay_state, 'Graphics capture requires an isolated replay')
local graphics_out = capture_graphics and assert(io.open(base..'-graphics.jsonl', 'w')) or nil
local graphics_seen = {}
local function write_blob(path, size, reader)
  local file = assert(io.open(path, 'wb'))
  for i=0,size-1 do file:write(string.char(reader(i))) end
  file:close()
end
local function capture_pose(step)
  if not graphics_out or not experiment_step or step-experiment_step<477 or step-experiment_step>505 then return end
  local actor=u16(0x1AFC)
  if actor<0x0500 or actor>0x1A00 or actor%0x100~=0 then return end
  if not graphics_every_frame and u16(actor+0x1C)~=0xD007 then return end
  local descriptor=u16(actor+0x14)
  if not graphics_every_frame and graphics_seen[descriptor] then return end
  local name=base:match('([^/\\]+)$')..string.format('-pose-%04X',descriptor)
  if graphics_every_frame then name=name..string.format('-step-%d',step) end
  local prefix=directory..'/'..name
  write_blob(prefix..'-mirror.bin',544,function(i) return mainmemory.read_u8(0x1E0+i) end)
  write_blob(prefix..'-vram.bin',65536,function(i) return memory.read_u8(i,'VRAM') end)
  local ppu_ok=pcall(function() write_blob(prefix..'-ppu.bin',544,function(i) return memory.read_u8(i,'OAM') end) end)
  local ppu_cgram_ok=pcall(function() write_blob(prefix..'-ppu-cgram.bin',512,function(i) return memory.read_u8(i,'CGRAM') end) end)
  local cg=assert(io.open(prefix..'-cgram.hex','w'))
  for i=0,511 do cg:write(string.format('%02X',mainmemory.read_u8(0x2C00+i))) end
  cg:close()
  local shot_ok=pcall(client.screenshot,prefix..'-screen.png')
  local shot=io.open(prefix..'-screen.png','rb')
  if shot then shot:close() else shot_ok=false end
  graphics_out:write(string.format('{"schema":"issd-native-action-oam/v1","frame":%d,"step":%d,"obsel":%d,"oam_mirror":"%s-mirror.bin","oam_mirror_encoding":"low-512-reversed-high-32-forward","oam_ppu":%s,"vram":"%s-vram.bin","cgram":"%s-cgram.hex","cgram_ppu":%s,"screenshot":%s,"actor":{"address":%d,"animation_script":%d,"direction":%d,"descriptor":%d,"pose":%d,"animation_timer":%d,"animation_duration":%d,"animation_cursor":%d,"object_field_02":%d,"origin_x_raw":%d,"origin_y_raw":%d,"origin_y_offset_raw":%d,"object_flags":%d,"type":%d}}\n',
    emu.framecount(),step,mainmemory.read_u8(0x1EA6),name,ppu_ok and ('"'..name..'-ppu.bin"') or 'null',name,name,
    ppu_cgram_ok and ('"'..name..'-ppu-cgram.bin"') or 'null',
    shot_ok and ('"'..name..'-screen.png"') or 'null',actor,u16(actor+0x1C),u16(actor+0x2E),descriptor,u16(actor),
    u16(actor+0x16),u16(actor+0x18),u16(actor+0x1A),u16(actor+0x02),u16(actor+0x08),u16(actor+0x0C),u16(actor+0x10),mainmemory.read_u8(actor+0x04),mainmemory.read_u8(actor+0x30)))
  graphics_out:flush()
  graphics_seen[descriptor]=true
end
local function register_or_nil(name)
  local ok,value=pcall(emu.getregister,name)
  if ok and type(value)=='number' then return tostring(value) end
  return 'null'
end
if trace_execution then
  for _,entry in ipairs({{0x849473,'849473'},{0x84957E,'84957E'},
                          {0x849592,'849592'},{0x849755,'849755'},
                          {0x84979F,'84979F'},{0x85F3FE,'85F3FE'},
                          {0x85F410,'85F410'},{0x85F8B9,'85F8B9'},
                          {0x8394A4,'8394A4'}}) do
    local address,label=entry[1],entry[2]
    local ok,handle=pcall(event.onmemoryexecute,function()
      if experiment_step and current_step-experiment_step>=460 and current_step-experiment_step<=540 then
        local ok,dp=pcall(emu.getregister,'D')
        local action_word = ok and type(dp)=='number' and dp>=0 and dp<=0xFF90 and tostring(u16(dp+0x6E)) or 'null'
        out:write(string.format('{"type":"execution","step":%d,"frame":%d,"address":"%s","dp":%s,"a":%s,"x":%s,"y":%s,"action_word":%s,"ball_type":%d,"link_a6":%d}\n',
          current_step,emu.framecount(),label,register_or_nil('D'),register_or_nil('A'),
          register_or_nil('X'),register_or_nil('Y'),action_word,u16(0x430),u16(0xA6)))
      end
    end,address,'issd-exec-'..label)
    local handle_text=tostring(handle)
    local registered=ok and handle~=nil and handle_text~='00000000-0000-0000-0000-000000000000'
    out:write(string.format('{"type":"hook_registration","address":"%s","success":%s,"handle":"%s"}\n',label,tostring(registered),handle_text:gsub('["\\\r\n]','?')))
  end
  out:flush()
end
if trace_draw then
  local ok,handle=pcall(event.onmemoryexecute,function()
    if experiment_step and current_step-experiment_step>=477 and current_step-experiment_step<=505 then
      local yok,y=pcall(emu.getregister,'Y')
      local object = yok and type(y)=='number' and y>=0x1D40 and y<=0x1FFE and tostring(u16(y)) or 'null'
      out:write(string.format('{"type":"draw_entry","step":%d,"frame":%d,"list_y":%s,"object":%s,"stack":%s}\n',
        current_step,emu.framecount(),register_or_nil('Y'),object,register_or_nil('S')))
    end
  end,0x8095E3,'issd-draw-list')
  local h=tostring(handle)
  out:write(string.format('{"type":"draw_hook_registration","success":%s,"handle":"%s"}\n',
    tostring(ok and handle~=nil and h~='00000000-0000-0000-0000-000000000000'),h:gsub('["\\\r\n]','?')))
  out:flush()
end
if trace_selection then
  for _,entry in ipairs({{0x80E48D,'80E48D'},{0x80E49A,'80E49A'},
                          {0x84968B,'84968B'},{0x8496B8,'8496B8'},
                          {0x80E4C7,'80E4C7'},{0x84E600,'84E600'},
                          {0x84E60C,'84E60C'},{0x84E6AC,'84E6AC'}}) do
    local address,label=entry[1],entry[2]
    local ok,handle=pcall(event.onmemoryexecute,function()
      if not experiment_step or current_step-experiment_step<475 or current_step-experiment_step>510 then return end
      local dok,dp=pcall(emu.getregister,'D')
      if not dok or dp~=u16(0x1AFC) then return end
      out:write(string.format('{"type":"selection_execution","step":%d,"frame":%d,"address":"%s","dp":%d,"a":%s,"x":%s,"y":%s,"field_84":%d,"field_86":%d,"direction":%d}\n',
        current_step,emu.framecount(),label,dp,register_or_nil('A'),register_or_nil('X'),register_or_nil('Y'),u16(dp+0x84),u16(dp+0x86),u16(dp+0x2E)))
    end,address,'issd-selector-'..label)
    local h=tostring(handle)
    out:write(string.format('{"type":"selection_hook_registration","address":"%s","success":%s}\n',label,
      tostring(ok and handle~=nil and h~='00000000-0000-0000-0000-000000000000')))
  end
  out:flush()
end
if trace_input_origin then
  for _,entry in ipairs({{0x83F151,'83F151'},{0x83F19F,'83F19F'},
                          {0x83F1B1,'83F1B1'},{0x80DD34,'80DD34'},
                          {0x80DD45,'80DD45'},{0x80E770,'80E770'},
                          {0x80E7B0,'80E7B0'},{0x80F455,'80F455'},
                          {0x80DE35,'80DE35'}}) do
    local address,label=entry[1],entry[2]
    local ok,handle=pcall(event.onmemoryexecute,function()
      if not experiment_step or current_step-experiment_step<479 or current_step-experiment_step>485 then return end
      local dok,dp=pcall(emu.getregister,'D')
      if not dok or dp~=u16(0x1AFC) then return end
      local xok,x=pcall(emu.getregister,'X')
      local held = xok and type(x)=='number' and x>=0x1AA0 and x<=0x1B60 and (x-0x1AA0)%0x30==0 and tostring(u16(x+0x12)) or 'null'
      out:write(string.format('{"type":"input_origin_execution","step":%d,"frame":%d,"address":"%s","dp":%d,"a":%s,"x":%s,"y":%s,"carry":%s,"controller_held":%s,"field_84":%d,"field_86":%d,"field_6e":%d,"direction":%d}\n',
        current_step,emu.framecount(),label,dp,register_or_nil('A'),register_or_nil('X'),register_or_nil('Y'),register_or_nil('Flag C'),held,
        u16(dp+0x84),u16(dp+0x86),u16(dp+0x6E),u16(dp+0x2E)))
    end,address,'issd-input-origin-'..label)
    local h=tostring(handle)
    out:write(string.format('{"type":"input_origin_hook_registration","address":"%s","success":%s}\n',label,
      tostring(ok and handle~=nil and h~='00000000-0000-0000-0000-000000000000')))
  end
  out:flush()
end
if trace_ball_writes then
  for _,entry in ipairs({{0x0430,'type-low'},{0x0431,'type-high'},
                          {0x00A6,'link-low'},{0x00A7,'link-high'},
                          {0x7E0430,'type-low-wram'},{0x7E0431,'type-high-wram'},
                          {0x7E00A6,'link-low-wram'},{0x7E00A7,'link-high-wram'}}) do
    local address,label=entry[1],entry[2]
    local ok,handle=pcall(event.onmemorywrite,function()
      if not experiment_step or current_step-experiment_step<ball_trace_start or current_step-experiment_step>ball_trace_end then return end
      out:write(string.format('{"type":"ball_write","step":%d,"frame":%d,"watch":"%s","pc":%s,"pb":%s,"dp":%s,"a":%s,"x":%s,"y":%s,"ball_type":%d,"link_a6":%d}\n',
        current_step,emu.framecount(),label,register_or_nil('PC'),register_or_nil('PB'),register_or_nil('D'),
        register_or_nil('A'),register_or_nil('X'),register_or_nil('Y'),u16(0x430),u16(0xA6)))
    end,address,'issd-ball-write-'..label,'System Bus')
    local h=tostring(handle)
    out:write(string.format('{"type":"ball_write_hook_registration","watch":"%s","success":%s}\n',label,
      tostring(ok and handle~=nil and h~='00000000-0000-0000-0000-000000000000')))
  end
  out:flush()
end
if trace_ball_update then
  for _,entry in ipairs({{0x839E32,'839E32'},{0x839E92,'839E92'},{0x839EC3,'839EC3'},
                          {0x83953F,'83953F'},{0x83956E,'83956E'},{0x839722,'839722'},
                          {0x839750,'839750'},{0x85F91B,'85F91B'},
                          {0x8486E2,'8486E2'},{0x84BCDA,'84BCDA'},{0x84C24A,'84C24A'},
                          {0x84B9EC,'84B9EC'},{0x84B9F7,'84B9F7'},{0x84BA01,'84BA01'},
                          {0x84E8B0,'84E8B0'},{0x84E8BD,'84E8BD'},{0x84E8E4,'84E8E4'},
                          {0x84E8E7,'84E8E7'},{0x84E8E9,'84E8E9'},{0x84E902,'84E902'},
                          {0x84E91E,'84E91E'},
                          {0x84BA6F,'84BA6F'},{0x84BAA8,'84BAA8'},
                          {0x84BAB7,'84BAB7'},{0x84BAF6,'84BAF6'},
                          {0x84BAFB,'84BAFB'},{0x84BB14,'84BB14'},
                          {0x85F06E,'85F06E'},{0x85F088,'85F088'},
                          {0x85F0D3,'85F0D3'},{0x85F8BF,'85F8BF'},
                          {0x838CFA,'838CFA'},{0x85F8D6,'85F8D6'},
                          {0x85EEB9,'85EEB9'},{0x85EEC3,'85EEC3'},{0x85EECE,'85EECE'},
                          {0x838851,'838851'},{0x8397BE,'8397BE'},
                          {0x8387B5,'8387B5'},{0x8394EB,'8394EB'},
                          {0x85ECC3,'85ECC3'},{0x85EE94,'85EE94'},
                          {0x8390E6,'8390E6'},{0x8391F6,'8391F6'},
                          {0x839240,'839240'},{0x83924F,'83924F'},
                          {0x839264,'839264'},{0x83933B,'83933B'},
                          {0x83941F,'83941F'},{0x83882A,'83882A'}}) do
    local address,label=entry[1],entry[2]
    local ok,handle=pcall(event.onmemoryexecute,function()
      if not experiment_step or current_step-experiment_step<ball_trace_start or current_step-experiment_step>ball_trace_end then return end
      local ok,dp=pcall(emu.getregister,'D')
      if not ok or type(dp)~='number' then dp=0 end
      if force_geometry_68 and label=='84E8B0' and current_step-experiment_step==493 and dp==u16(0x1ACC) then
        assert(not forced_geometry_actor, 'Nested synthetic geometry entry')
        forced_geometry_actor=dp
        forced_geometry_original=u16(dp+0x68)
        mainmemory.write_u16_le(dp+0x68,0)
        out:write(string.format('{"type":"synthetic_geometry_override","step":%d,"actor":%d,"original_68":%d,"forced_68":0}\n',current_step,dp,forced_geometry_original))
      end
      local field60,team,ax,ay,az,gate3e,gate68=0,0,0,0,0,0,0
      if dp>=0x0500 and dp<=0x1A00 and dp%0x100==0 then
        field60=u16(dp+0x60);team=u16(dp+0x9A);ax=u16(dp+0x08);ay=u16(dp+0x0C);az=u16(dp+0x10)
        gate3e=u16(dp+0x3E);gate68=u16(dp+0x68)
      end
      local c8=u16(0xC8)
      local c8team=0
      if c8>=0x0500 and c8<=0x1A00 and c8%0x100==0 then c8team=u16(c8+0x9A) end
      out:write(string.format('{"type":"ball_update_execution","step":%d,"frame":%d,"address":"%s","dp":%s,"a":%s,"x":%s,"y":%s,"carry":%s,"actor_x":%d,"actor_y":%d,"actor_z":%d,"actor_3e":%d,"actor_68":%d,"global_11fa":%d,"actor_field60":%d,"actor_team":%d,"ref_c8":%d,"ref_c8_team":%d,"ball_age":%d,"scratch_00":%d,"scratch_02":%d,"scratch_04":%d,"scratch_06":%d,"angle":%d,"parameter":%d,"magnitude":%d,"global_ac":%d,"global_ae":%d,"release_type":%d,"ball_type":%d,"timer":%d,"x_fraction":%d,"x_pos":%d,"y_fraction":%d,"y_pos":%d,"z_fraction":%d,"z_pos":%d,"vx_fraction":%d,"vx":%d,"vy_fraction":%d,"vy":%d,"vz_fraction":%d,"vz":%d,"link_a6":%d}\n',
        current_step,emu.framecount(),label,register_or_nil('D'),register_or_nil('A'),register_or_nil('X'),register_or_nil('Y'),register_or_nil('Flag C'),ax,ay,az,gate3e,gate68,u16(0x11FA),field60,team,c8,c8team,u16(0x46C),
        u16(0),u16(2),u16(4),u16(6),u16(0x452),u16(0x456),u16(0x464),u16(0xAC),u16(0xAE),u16(0x12F4),u16(0x430),u16(0x454),u16(0x406),u16(0x408),u16(0x40A),u16(0x40C),u16(0x40E),u16(0x410),
        u16(0x422),u16(0x424),u16(0x426),u16(0x428),u16(0x434),u16(0x436),u16(0xA6)))
      if forced_geometry_actor==dp and (label=='84E8E4' or label=='84E8E7' or label=='84E91E') then
        mainmemory.write_u16_le(dp+0x68,forced_geometry_original)
        out:write(string.format('{"type":"synthetic_geometry_restore","step":%d,"actor":%d,"restored_68":%d}\n',current_step,dp,forced_geometry_original))
        forced_geometry_actor,forced_geometry_original=nil,nil
      end
    end,address,'issd-ball-update-'..label)
    local h=tostring(handle)
    out:write(string.format('{"type":"ball_update_hook_registration","address":"%s","success":%s}\n',label,
      tostring(ok and handle~=nil and h~='00000000-0000-0000-0000-000000000000')))
  end
  out:flush()
end
if trace_alternate then
  for _,entry in ipairs({{0x8496B8,'8496B8'},{0x8496CF,'8496CF'},
                          {0x8496D4,'8496D4'},{0x8496E5,'8496E5'},
                          {0x85F438,'85F438'},{0x85F45F,'85F45F'},
                          {0x85F871,'85F871'},{0x85F89B,'85F89B'},
                          {0x85F8B9,'85F8B9'}}) do
    local address,label=entry[1],entry[2]
    local ok,handle=pcall(event.onmemoryexecute,function()
      if not experiment_step or current_step-experiment_step<475 or current_step-experiment_step>520 then return end
      local dok,dp=pcall(emu.getregister,'D')
      if not dok or dp~=u16(0x1AFC) then return end
      out:write(string.format('{"type":"alternate_execution","step":%d,"frame":%d,"address":"%s","dp":%d,"a":%s,"x":%s,"y":%s,"field_6e":%d,"timer_70":%d,"ball_type":%d,"link_a4":%d,"link_a6":%d}\n',
        current_step,emu.framecount(),label,dp,register_or_nil('A'),register_or_nil('X'),register_or_nil('Y'),
        u16(dp+0x6E),u16(dp+0x70),u16(0x430),u16(0xA4),u16(0xA6)))
    end,address,'issd-alternate-'..label)
    local h=tostring(handle)
    out:write(string.format('{"type":"alternate_hook_registration","address":"%s","success":%s}\n',label,
      tostring(ok and handle~=nil and h~='00000000-0000-0000-0000-000000000000')))
  end
  out:flush()
end
local function valid_actor(a)
  return a>=0x0500 and a<=0x1A00 and a%0x100==0 and mainmemory.read_u8(a+0x30)~=0
end
local function button(frame)
  -- Conservative spaced pulses; remaining frames are neutral.
  if frame>=180 and frame<=1200 and frame%120<6 then
    return {Start=true}, 'Start'
  end
  if two_player_scenario and frame>=1500 and frame<1506 then
    return {Right=true}, 'Right'
  end
  if frame>1200 and frame<=3450 and frame%120<6 and not (two_player_scenario and frame>=1440 and frame<1446) then
    return {A=true}, 'A'
  end
  if controlled_experiment then
    if not experiment_step then
      if extended_menu and frame>3450 and frame%120<6 then return {A=true}, 'A' end
      return {}, 'neutral'
    end
    local elapsed=frame-experiment_step
    if elapsed>=60 and elapsed<180 then return {Right=true}, 'Right' end
    if elapsed>=420 and elapsed<426 then return {A=true}, 'A' end
    return {}, 'neutral'
  end
  if opponent_scenario then
    if trigger_step then
      local elapsed=frame-trigger_step
      if elapsed>=0 and elapsed<90 then return {Right=true}, 'Right' end
      if elapsed>=120 and elapsed<210 then return {Left=true}, 'Left' end
      if elapsed>=240 and elapsed<330 then return {Up=true}, 'Up' end
      if elapsed>=360 and elapsed<450 then return {Down=true}, 'Down' end
      return {}, 'neutral'
    end
    if frame>3450 and frame%180<6 then return {A=true}, 'A' end
    return {}, 'neutral'
  end
  if frame>=3510 and frame<3540 then return {B=true}, 'B' end
  if frame>=3600 and frame<3720 then return {Right=true}, 'Right' end
  if frame>=3780 and frame<3900 then return {Left=true}, 'Left' end
  if frame>=3960 and frame<4080 then return {Up=true}, 'Up' end
  if frame>=4140 and frame<4260 then return {Down=true}, 'Down' end
  return {}, 'neutral'
end
out:write(string.format('{"type":"session_start","schema":"issd-auto-probe/v3","menu_route":"experimental","scenario":"%s","p2_action_enabled":%s,"target_frames":%d}\n',opponent_scenario and 'opponent_link' or (action_observation and 'two_player_action_observation' or (controlled_experiment and 'two_player_experiment' or (two_player_scenario and 'two_player_probe' or 'timed_directions'))),tostring(p2_action_enabled),target_frames))
out:flush()
local start_step = 1
if replay_state then
  assert(savestate.load(replay_state, true), 'Unable to load experiment savestate')
  start_step = 4001 -- odd, so the comparator sees the same relative sample parity
  experiment_step = start_step
  assert(u16(0x11E6)==4 and u16(0x00C0)==0 and valid_actor(u16(0x1ACC)) and valid_actor(u16(0x1AFC)), 'Savestate is not a valid two-player match')
  out:write(string.format('{"type":"experiment_start","step":%d,"p1":%d,"p2":%d,"replay":true}\n',start_step,u16(0x1ACC),u16(0x1AFC)))
  out:flush()
end
local completed_steps = 0
for step=start_step,target_frames do
  completed_steps=step
  current_step=step
  if controlled_experiment and not experiment_step and step>3450 then
    local a=u16(0x1ACC); local b=u16(0x1AFC)
    if u16(0x11E6)==4 and u16(0x00C0)==0 and valid_actor(a) and valid_actor(b) and
       u16(a+0x9A)~=0 and u16(b+0x9A)~=0 and u16(a+0x9A)~=u16(b+0x9A) then
      stable_frames=stable_frames+1
      if action_observation and not initial_clock then initial_clock=u16(0x16D0) end
    else stable_frames=0; initial_clock=nil end
    if stable_frames>=30 and (not action_observation or (initial_clock and u16(0x16D0)~=initial_clock)) then
      experiment_step=step
      out:write(string.format('{"type":"experiment_start","step":%d,"p1":%d,"p2":%d}\n',step,a,b));out:flush()
      if save_trigger then
        assert(savestate.save(base..'-trigger.State', true), 'Unable to save experiment savestate')
        out:write('{"type":"savestate_saved","success":true}\n');out:flush()
      end
      pcall(client.screenshot,base..'-experiment-start.png')
    end
  end
  if opponent_scenario and not trigger_step and step>3450 then
    local controlled=u16(0x1ACC); local link=u16(0x00A6)
    if valid_actor(controlled) and valid_actor(link) and controlled~=link and
       u16(controlled+0x9A)~=0 and u16(link+0x9A)~=0 and
       u16(controlled+0x9A)~=u16(link+0x9A) and u16(0x11E6)==0 then
      trigger_step=step
      out:write(string.format('{"type":"candidate_trigger","step":%d,"controlled":%d,"link":%d}\n',step,controlled,link));out:flush()
      pcall(client.screenshot,base..'-candidate.png')
    end
  end
  local input,label=button(step)
  joypad.set(input,1)
  local p2label='neutral'
  if two_player_scenario and step>=1800 and (step<=3300 or (extended_menu and not experiment_step)) and step%120<6 then
    joypad.set({A=true},2);p2label='A'
  elseif controlled_experiment and experiment_step and step-experiment_step>=240 and step-experiment_step<360 then
    joypad.set(p2_move_inputs[p2_move_button],2);p2label=p2_move_button
  elseif controlled_experiment and p2_action_enabled and experiment_step and step-experiment_step>=480 and step-experiment_step<486 then
    local action_input={[p2_action_button]=true}
    if p2_action_direction then
      for name,pressed in pairs(p2_move_inputs[p2_action_direction]) do action_input[name]=pressed end
    end
    joypad.set(action_input,2)
    p2label=p2_action_button..(p2_action_direction and ('+'..p2_action_direction) or '')
  elseif two_player_scenario and not controlled_experiment and step>=3600 and step<3720 then
    joypad.set({Left=true},2);p2label='Left'
  elseif two_player_scenario and not controlled_experiment and step>=3780 and step<3900 then
    joypad.set({Right=true},2);p2label='Right'
  else joypad.set({},2) end
  emu.frameadvance()
  capture_pose(step)
  if step%600==0 or (two_player_scenario and step>=1200 and step<=3200 and step%120==0) or
     (action_observation and experiment_step and (step-experiment_step==420 or step-experiment_step==450 or step-experiment_step==480 or step-experiment_step==510)) then
    local ok, message=pcall(client.screenshot,base..'-'..step..'.png')
    print('screenshot '..step..': '..tostring(ok)..' '..tostring(message))
  end
  local action_window = action_every_frame and experiment_step and
    step-experiment_step>=470 and step-experiment_step<=520
  if step%2==0 or action_window then
    local selected=u16(0x1ACC)
    local valid=selected>=0x0500 and selected<=0x1A00 and selected%0x100==0
    local state,script,descriptor,direction,x,y=0,0,0,0,0,0
    if valid then
      state=u16(selected+0x32);script=u16(selected+0x1C)
      descriptor=u16(selected+0x14);direction=u16(selected+0x2E)
      x=u16(selected+0x08);y=u16(selected+0x0C)
    end
    local controls={}
    for address=0x1AA0,0x1B60,0x30 do
      controls[#controls+1]=string.format('{"address":%d,"actor":%d,"flags":%d,"held":%d}',
        address,u16(address+0x2C),u16(address+0x2E),u16(address+0x12))
    end
    local actors={}
    for address=0x0500,0x1A00,0x100 do
      actors[#actors+1]=string.format('{"address":%d,"type":%d,"state":%d,"script":%d,"descriptor":%d,"direction":%d,"x":%d,"x_fraction":%d,"y":%d,"y_fraction":%d,"team":%d}',
        address,mainmemory.read_u8(address+0x30),u16(address+0x32),u16(address+0x1C),u16(address+0x14),u16(address+0x2E),
        u16(address+0x08),u16(address+0x06),u16(address+0x0C),u16(address+0x0A),u16(address+0x9A))
    end
    out:write(string.format('{"step":%d,"frame":%d,"input":"%s","input_p2":"%s","joypad1":%d,"held_p1":%d,"held_p2":%d,"pressed_p1":%d,"player_setting":%d,"mode1":%d,"mode2":%d,"phase":%d,"selected_p1":%d,"actor_slot_valid":%s,"actor":{"state":%d,"script":%d,"descriptor":%d,"direction":%d,"x":%d,"y":%d},"ball":{"x":%d,"y":%d,"z":%d,"vx":%d,"vy":%d,"vz":%d,"type":%d},"link_a4":%d,"link_a6":%d,"controls":[%s],"actors":[%s]}\n',
      step,emu.framecount(),label,p2label,u16(0x10),u16(0x20),u16(0x22),u16(0x28),u16(0x11E6),u16(0x32),u16(0x70),u16(0xC0),selected,tostring(valid),
      state,script,descriptor,direction,x,y,u16(0x408),u16(0x40C),u16(0x410),u16(0x424),u16(0x428),u16(0x436),u16(0x430),u16(0xA4),u16(0xA6),table.concat(controls,','),table.concat(actors,',')))
    if step%120==0 then out:flush() end
  end
  if action_observation and experiment_step and step-experiment_step>=650 then break end
end
joypad.set({},1)
assert(not forced_geometry_actor, 'Synthetic geometry field was not restored')
if graphics_out then graphics_out:close() end
joypad.set({},2)
out:write(string.format('{"type":"session_end","steps":%d,"candidate_triggered":%s,"experiment_triggered":%s,"reason":"%s"}\n',completed_steps,tostring(trigger_step~=nil),tostring(experiment_step~=nil),completed_steps<target_frames and 'experiment_window_complete' or 'frame_limit'))
out:close()
print('ISSD auto probe complete: '..output_path)
