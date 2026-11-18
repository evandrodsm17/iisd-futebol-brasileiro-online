-- Replay one local pre-shot state with directional input; no RAM intervention.
local seed=assert(os.getenv('ISSD_HOLD_STATE'))
local out=assert(io.open(assert(os.getenv('ISSD_HOLD_OUTPUT')),'w'))
local trial,step=0,0
local function u(a)return mainmemory.read_u16_le(a)end
local function reg(n)local ok,v=pcall(emu.getregister,n);return ok and type(v)=='number' and v or -1 end
local hooks={{0x80e770,'80E770'},{0x80e781,'80E781'},{0x80e788,'80E788'},
 {0x80e7b0,'80E7B0'},{0x80e833,'80E833'},{0x85f694,'85F694'},
 {0x85f6be,'85F6BE'},{0x85f871,'85F871'},{0x85f89b,'85F89B'}}
for _,item in ipairs(hooks) do
 local addr,name=item[1],item[2]
 assert(event.onmemoryexecute(function()
  local d=reg('D');if trial==0 or d~=0x1900 then return end
  local team=u(d+0x9a);local control=u(d+0x88)
  if team>0xff30 or control>0xffec then error('Unexpected actor references') end
  out:write(string.format('{"type":"hook","trial":%d,"step":%d,"frame":%d,"site":"%s","d":%d,"a":%d,"x":%d,"y":%d,"flags":%d,"actor40":%d,"actor2a":%d,"middle":%d,"charge":%d,"team":%d,"team_a4":%d,"team_cc":%d,"control":%d,"control13":%d,"held":%d}\n',trial,step,emu.framecount(),name,d,reg('A'),reg('X'),reg('Y'),u(d+0x6e),u(d+0x40),u(d+0x2a),u(0x12f2),u(d+0x82),team,u(team+0xa4),u(team+0xcc),control,u(control+0x13),u(0x22)));out:flush()
 end,addr,'shot-sweep-'..name))
end
local inputs={{'neutral',{}},{'up',{Up=true}},{'down',{Down=true}},{'left',{Left=true}},
 {'right',{Right=true}},{'up_left',{Up=true,Left=true}},{'up_right',{Up=true,Right=true}},
 {'down_left',{Down=true,Left=true}},{'down_right',{Down=true,Right=true}}}
out:write('{"type":"session_start","synthetic":false}\n')
for _,holdDirection in ipairs({false,true}) do
for _,item in ipairs(inputs) do
 trial=trial+1;step=0;assert(savestate.load(seed,true));assert(u(0xa6)==0x1900 and u(0x192e)==4,'unexpected replay state')
 out:write(string.format('{"type":"case","trial":%d,"direction":"%s","heldFrames":6,"holdDirection":%s}\n',trial,item[1],tostring(holdDirection)))
 for i=1,45 do
  step=i;local input={};if i<=6 then input.X=true end
  if holdDirection or i<=6 then for k,v in pairs(item[2]) do input[k]=v end end
  joypad.set({},1);joypad.set(input,2);emu.frameadvance()
  out:write(string.format('{"type":"frame","trial":%d,"step":%d,"flags":%d,"held":%d,"charge":%d,"carrier":%d,"ballType":%d}\n',trial,step,u(0x196e),u(0x22),u(0x1982),u(0xa6),u(0x430)))
 end
end
end
trial=0;joypad.set({},1);joypad.set({},2);out:write('{"type":"session_end"}\n');out:close();client.exit()
