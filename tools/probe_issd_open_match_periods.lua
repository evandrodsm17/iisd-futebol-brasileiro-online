-- Isolated saved-state replay. Only the clock is accelerated; menu A pulses
-- are logged. No ROM or user-visible emulator state is modified.
local seed=assert(os.getenv('ISSD_PERIOD_STATE'))
local directory=assert(os.getenv('ISSD_PERIOD_OUTPUT'))
local scoreMode=os.getenv('ISSD_PERIOD_SCORE') or 'draw'
assert(scoreMode=='draw' or scoreMode=='home','Invalid synthetic score mode')
local overtimeOverride=os.getenv('ISSD_PERIOD_OVERTIME')
assert(not overtimeOverride or overtimeOverride=='0' or overtimeOverride=='1','Invalid overtime override')
local out=assert(io.open(directory..'/trace.jsonl','w'))
local function u(a)return mainmemory.read_u16_le(a)end
local function reg(n)local ok,v=pcall(emu.getregister,n);return ok and type(v)=='number' and v or -1 end
local step=0
for _,item in ipairs({{0xa4d898,'A4D898'},{0xa4d8a8,'A4D8A8'},{0xa49231,'A49231'},{0xa492cf,'A492CF'}}) do
 local addr,name=item[1],item[2]
 assert(event.onmemoryexecute(function()
  out:write(string.format('{"type":"hook","step":%d,"frame":%d,"site":"%s","d":%d,"a":%d,"phase":%d,"clock":%d,"mode":%d,"scene":%d}\n',step,emu.framecount(),name,reg('D'),reg('A'),u(0xa8),u(0x16d0),u(0x32),u(0x70)));out:flush()
 end,addr,'period-'..name))
end
assert(savestate.load(seed,true))
assert(u(0x32)==6 and u(0x70)==8 and u(0xa8)==0,'unexpected pre-shot match state')
out:write(string.format('{"type":"session_start","synthetic_clock":true,"score_mode":"%s","initial_overtime":%d,"game_time":%d,"home":%d,"away":%d}\n',scoreMode,u(0x1e64),u(0x1e5a),u(0xda2),u(0xea2)))
if overtimeOverride then
 local before=u(0x1e64);local after=tonumber(overtimeOverride);mainmemory.write_u16_le(0x1e64,after)
 out:write(string.format('{"type":"overtime_intervention","before":%d,"after":%d}\n',before,after))
end
if scoreMode=='home' then
 local before=u(0xda2);mainmemory.write_u16_le(0xda2,1)
 out:write(string.format('{"type":"score_intervention","side":"home","before":%d,"after":1}\n',before))
end
local forced,formations,lastKey,lastScene,sceneStart={},{},'','',0
for i=1,8000 do
 step=i;local mode,scene,phase=u(0x32),u(0x70),u(0xa8)
 local active=mode==6 and scene==8
 if active and phase<=3 and not formations[phase] then
  local actors={}
  for address=0x500,0x1a00,0x100 do
   local team=u(address+0x9a)
   if (team==0xd00 or team==0xe00) and u(address+0x30)~=0 then
    actors[#actors+1]=string.format('{"address":%d,"team":%d,"x":%d,"y":%d,"kind":%d,"state":%d}',address,team,u(address+0x2a),u(address+0x2c),u(address+0x30),u(address+0x32))
   end
  end
  out:write(string.format('{"type":"formation","step":%d,"phase":%d,"ballX":%d,"ballY":%d,"fieldWidth":%d,"fieldHeight":%d,"actors":[%s]}\n',step,phase,u(0x42a),u(0x42c),u(0x12a2),u(0x12a4),table.concat(actors,',')));out:flush()
  formations[phase]=true
 end
 if active and phase<=3 and not forced[phase] and u(0x16d0)>1 then
  local before=u(0x16d0);mainmemory.write_u16_le(0x16d0,1);forced[phase]=true
  out:write(string.format('{"type":"clock_intervention","step":%d,"phase":%d,"before":%d,"after":1}\n',step,phase,before));out:flush()
 end
 local pulse=not active and i%120<6
 joypad.set(pulse and {A=true} or {},1);joypad.set(pulse and {A=true} or {},2)
 if pulse and i%120==0 then out:write(string.format('{"type":"menu_pulse","step":%d,"mode":%d,"scene":%d}\n',step,mode,scene)) end
 emu.frameadvance()
 mode,scene,phase=u(0x32),u(0x70),u(0xa8)
 local sceneKey=string.format('%d/%d/%d',mode,scene,phase)
 if sceneKey~=lastScene then lastScene=sceneKey;sceneStart=step end
 if mode==6 and (scene==9 or scene==18 or scene==11 or scene==12) and (step-sceneStart==20 or step-sceneStart==80) then
  local filename=string.format('scene-%04d-%02d-%d.png',step,scene,phase)
  local success=pcall(client.screenshot,directory..'/'..filename)
  out:write(string.format('{"type":"screenshot","step":%d,"scene":%d,"phase":%d,"file":"%s","success":%s}\n',step,scene,phase,filename,tostring(success)))
 end
 local key=string.format('%d/%d/%d/%d/%d',mode,scene,phase,u(0xc0),u(0x16d0))
 if key~=lastKey or i%60==0 then
  local carrier=u(0xa6);local carrierTeam=-1
  if carrier>=0x500 and carrier<=0x1a00 and carrier%0x100==0 then carrierTeam=u(carrier+0x9a) end
  out:write(string.format('{"type":"frame","step":%d,"frame":%d,"mode":%d,"scene":%d,"phase":%d,"state":%d,"clock":%d,"display":%d,"frameCounter":%d,"home":%d,"away":%d,"carrier":%d,"carrierTeam":%d,"team0Flags":%d,"team1Flags":%d,"overtime":%d,"blocked":%d,"clockPhase":%d}\n',step,emu.framecount(),mode,scene,phase,u(0xc0),u(0x16d0),u(0x16d2),u(0x16d8),u(0xda2),u(0xea2),carrier,carrierTeam,u(0xda4),u(0xea4),u(0x1e64),u(0x11fa),u(0x16f8)))
  lastKey=key
 end
end
joypad.set({},1);joypad.set({},2);out:write('{"type":"session_end","steps":8000}\n');out:close();client.exit()
