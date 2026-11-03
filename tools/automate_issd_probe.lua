-- Isolated experimental navigation. Sends P1 inputs; never writes ROM or RAM.
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
local controlled_experiment = action_observation or os.getenv('ISSD_AUTO_SCENARIO') == 'two_player_experiment'
local two_player_scenario = controlled_experiment or os.getenv('ISSD_AUTO_SCENARIO') == 'two_player_probe'
local target_frames = opponent_scenario and 10000 or (action_observation and 7500 or (controlled_experiment and 6500 or 4800))
local trigger_step = nil
local stable_frames = 0
local experiment_step = nil
local initial_clock = nil
local current_step = 0
local trace_execution = os.getenv('ISSD_AUTO_TRACE_EXEC') == '1'
-- Some cores reach the player-selection screen later. Opt in explicitly;
-- once a stable match is detected, the controlled experiment takes over.
local extended_menu = os.getenv('ISSD_AUTO_EXTENDED_MENU') == '1'
local function register_or_nil(name)
  local ok,value=pcall(memory.getregister,name)
  if ok and type(value)=='number' then return tostring(value) end
  return 'null'
end
if trace_execution then
  for _,entry in ipairs({{0x849473,'849473'},{0x849755,'849755'},
                          {0x84979F,'84979F'},{0x85F3FE,'85F3FE'},
                          {0x85F410,'85F410'},{0x85F8B9,'85F8B9'}}) do
    local address,label=entry[1],entry[2]
    local ok,handle=pcall(event.onmemoryexecute,function()
      if experiment_step and current_step-experiment_step>=460 and current_step-experiment_step<=540 then
        out:write(string.format('{"type":"execution","step":%d,"frame":%d,"address":"%s","dp":%s,"a":%s,"x":%s,"y":%s,"ball_type":%d,"link_a6":%d}\n',
          current_step,emu.framecount(),label,register_or_nil('D'),register_or_nil('A'),
          register_or_nil('X'),register_or_nil('Y'),u16(0x430),u16(0xA6)))
      end
    end,address,'issd-exec-'..label)
    local handle_text=tostring(handle)
    local registered=ok and handle~=nil and handle_text~='00000000-0000-0000-0000-000000000000'
    out:write(string.format('{"type":"hook_registration","address":"%s","success":%s,"handle":"%s"}\n',label,tostring(registered),handle_text:gsub('["\\\r\n]','?')))
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
local completed_steps = 0
for step=1,target_frames do
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
    joypad.set({Right=true},2);p2label='Right'
  elseif controlled_experiment and p2_action_enabled and experiment_step and step-experiment_step>=480 and step-experiment_step<486 then
    joypad.set({A=true},2);p2label='A'
  elseif two_player_scenario and not controlled_experiment and step>=3600 and step<3720 then
    joypad.set({Left=true},2);p2label='Left'
  elseif two_player_scenario and not controlled_experiment and step>=3780 and step<3900 then
    joypad.set({Right=true},2);p2label='Right'
  else joypad.set({},2) end
  emu.frameadvance()
  if step%600==0 or (two_player_scenario and step>=1200 and step<=3200 and step%120==0) or
     (action_observation and experiment_step and (step-experiment_step==420 or step-experiment_step==450 or step-experiment_step==480 or step-experiment_step==510)) then
    local ok, message=pcall(client.screenshot,base..'-'..step..'.png')
    print('screenshot '..step..': '..tostring(ok)..' '..tostring(message))
  end
  if step%2==0 then
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
joypad.set({},2)
out:write(string.format('{"type":"session_end","steps":%d,"candidate_triggered":%s,"experiment_triggered":%s,"reason":"%s"}\n',completed_steps,tostring(trigger_step~=nil),tostring(experiment_step~=nil),completed_steps<target_frames and 'experiment_window_complete' or 'frame_limit'))
out:close()
print('ISSD auto probe complete: '..output_path)
