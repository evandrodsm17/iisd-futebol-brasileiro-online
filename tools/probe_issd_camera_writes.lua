-- Observe camera candidates in a disposable emulator after restoring the save.
local state=assert(os.getenv('ISSD_CAMERA_STATE'));local output=assert(os.getenv('ISSD_CAMERA_OUTPUT'));local screenshot=assert(os.getenv('ISSD_CAMERA_SCREENSHOT'))
assert(savestate.load(state,true),'state load failed')
local out=assert(io.open(output,'w'));local phase=0;local step=0
local function u(a)return mainmemory.read_u16_le(a)end
local function w(a,v)mainmemory.write_u16_le(a,v%65536)end
local function reg(n)local ok,v=pcall(emu.getregister,n);return ok and type(v)=='number' and v or -1 end
for _,address in ipairs({0x98,0x9a,0x13a0,0x13b0,0x7e0098,0x7e009a,0x7e13a0,0x7e13b0,0x408,0x40c,0x7e0408,0x7e040c}) do
 assert(event.onmemorywrite(function()
  if phase==0 then return end
  out:write(string.format('{"type":"write","phase":%d,"step":%d,"watch":%d,"pb":%d,"pc":%d,"a":%d,"x":%d,"y":%d,"d":%d,"r98":%d,"r9a":%d,"r13a0":%d,"r13b0":%d}\n',phase,step,address,reg('PB'),reg('PC'),reg('A'),reg('X'),reg('Y'),reg('D'),u(0x98),u(0x9a),u(0x13a0),u(0x13b0)))
 end,address,string.format('camera-observation-%06X',address),'System Bus'))
end
local width,height=u(0x12a2),u(0x12a4)
for mode=1,2 do
 phase=mode
 for i=1,90 do
  step=i
  if mode==2 then
   local targetX,targetY=width-180,math.floor(height/2)
   w(0xa4,0);w(0xa6,0);w(0x406,0);w(0x408,targetX+targetY-u(0x98));w(0x40a,0);w(0x40c,targetY-u(0x9a));w(0x40e,0);w(0x410,0)
   w(0x422,0);w(0x424,0);w(0x426,0);w(0x428,0);w(0x434,0);w(0x436,0);w(0x430,3)
   if i<=3 then out:write(string.format('{"type":"inject","phase":%d,"step":%d,"targetX":%d,"targetY":%d,"ball08":%d,"ball0c":%d,"r98":%d,"r9a":%d}\n',phase,step,targetX,targetY,u(0x408),u(0x40c),u(0x98),u(0x9a))) end
  end
  joypad.set({},1);joypad.set({},2);emu.frameadvance()
  out:write(string.format('{"type":"frame","phase":%d,"step":%d,"r98":%d,"r9a":%d,"r13a0":%d,"r13b0":%d,"ball08":%d,"ball0c":%d,"ball2a":%d,"ball2c":%d,"carrier":%d,"controlled":%d}\n',phase,step,u(0x98),u(0x9a),u(0x13a0),u(0x13b0),u(0x408),u(0x40c),u(0x42a),u(0x42c),u(0xa6),u(0x1acc)))
 end
 pcall(client.screenshot,screenshot..'-'..mode..'.png')
end
phase=0;out:close();client.exit()
