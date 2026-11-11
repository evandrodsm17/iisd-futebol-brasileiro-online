-- Compare RAM injection timing in isolated state replays. No ROM/state writes.
local state=assert(os.getenv('ISSD_TIMING_STATE'));local out=assert(io.open(assert(os.getenv('ISSD_TIMING_OUTPUT')),'w'))
local case=0;local step=0;local enabled=false;local started=false;local freshLink=0
local function u(a)return mainmemory.read_u16_le(a)end
local function w(a,v)mainmemory.write_u16_le(a,v%65536)end
local function log(site)
 out:write(string.format('{"case":%d,"step":%d,"site":"%s","frame":%d,"x":%d,"y":%d,"nativeX":%d,"nativeY":%d,"camX":%d,"camY":%d,"carrier":%d,"a4":%d,"link":%d,"ballType":%d,"ballFlags":%d,"ballState":%d,"keeperState":%d,"keeperScript":%d,"keeperFlags":%d}\n',case,step,site,emu.framecount(),u(0x408),u(0x40c),u(0x42a),u(0x42c),u(0x98),u(0x9a),u(0xa6),u(0xa4),u(0x1b90),u(0x430),u(0x404),u(0x432),u(0x532),u(0x51c),u(0x504)));out:flush()
end
local function inject()
 local targetX=u(0x12a2)-180;local targetY=math.floor(u(0x12a4)/2)
 w(0xa4,0);w(0xa6,0);w(0x406,0);w(0x408,targetX+targetY-u(0x98));w(0x40a,0);w(0x40c,targetY-u(0x9a));w(0x40e,0);w(0x410,0)
 w(0x422,0);w(0x424,0);w(0x426,0);w(0x428,0);w(0x434,0);w(0x436,0);w(0x430,3)
 if case>=5 then w(0x1b90,freshLink) end
 log('injected')
end
assert(event.onframestart(function()
 if not enabled then return end
 log('frame_start')
 if started then inject() end
end,'timing-start'))
assert(event.onframeend(function()if enabled then log('frame_end') end end,'timing-end'))
for _,h in ipairs({{0x8389e3,'8389E3'},{0x8389fb,'8389FB'},{0x83cfbd,'83CFBD'},{0x80d31a,'80D31A'}}) do
 local addr,name=h[1],h[2]
 assert(event.onmemoryexecute(function()if enabled then log(name)end end,addr,'timing-'..name))
end
for id=1,6 do
 enabled=false;case=id;step=0;started=(id==3 or id==4 or id==6)
 assert(savestate.load(state,true))
 freshLink=u(0x1b90)
 if id==2 or id==4 or id==5 or id==6 then for _=1,2 do joypad.set({},1);joypad.set({},2);emu.frameadvance() end end
 enabled=true
 for i=1,3 do
  step=i;log('before')
  if not started then inject() end
  joypad.set({},1);joypad.set({},2);emu.frameadvance();log('after')
 end
end
enabled=false;out:close();client.exit()
