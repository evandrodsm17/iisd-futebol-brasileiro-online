-- Target-selection observer in disposable emulator; second phase injects RAM.
local state=assert(os.getenv('ISSD_TARGET_STATE'));local out=assert(io.open(assert(os.getenv('ISSD_TARGET_OUTPUT')),'w'));local shots=assert(os.getenv('ISSD_TARGET_SCREENSHOT'))
local phase,step=0,0
local longFrames=tonumber(os.getenv('ISSD_TARGET_FRAMES') or '60')
assert(longFrames and longFrames>=60 and longFrames<=2000 and longFrames%1==0)
local function u(a)return mainmemory.read_u16_le(a)end
local function w(a,v)mainmemory.write_u16_le(a,v%65536)end
local function reg(n)local ok,v=pcall(emu.getregister,n);return ok and type(v)=='number' and v or -1 end
assert(event.onmemoryexecute(function()
 if phase==0 then return end
 local x=reg('X');local d=reg('D')
 out:write(string.format('{"type":"target","phase":%d,"step":%d,"x":%d,"d":%d,"a4":%d,"a6":%d,"c0":%d,"ee":%d,"f4":%d,"f0":%d,"ballType":%d,"ballX":%d,"ballY":%d,"targetX":%d,"targetY":%d,"targetFlags":%d}\n',phase,step,x,d,u(0xa4),u(0xa6),u(0xc0),u(0xee),u(0xf4),u(0xf0),u(0x430),u(0x408),u(0x40c),u(x+8),u(x+12),u(x+0x60)))
end,0x8b825a,'camera-selected-target'))
for mode=1,2 do
 phase=0;assert(savestate.load(state,true));phase=mode
 for i=1,(mode==2 and longFrames or 60) do
  step=i
  if mode==2 then
   local targetX,targetY=u(0x12a2)-180,math.floor(u(0x12a4)/2)
   w(0xa4,0);w(0xa6,0);w(0x406,0);w(0x408,targetX+targetY-u(0x98));w(0x40a,0);w(0x40c,targetY-u(0x9a));w(0x40e,0);w(0x410,0);w(0x422,0);w(0x424,0);w(0x426,0);w(0x428,0);w(0x434,0);w(0x436,0);w(0x430,3)
  end
  joypad.set({},1);joypad.set({},2);emu.frameadvance()
  if mode==2 and (i==600 or i==1200 or i==longFrames) then pcall(client.screenshot,shots..'-frame-'..i..'.png') end
  out:write(string.format('{"type":"frame","phase":%d,"step":%d,"camX":%d,"camY":%d,"ballNativeX":%d,"carrier":%d,"selected":%d}\n',phase,step,u(0x98),u(0x9a),u(0x42a),u(0xa6),u(0x1acc)))
 end
 pcall(client.screenshot,shots..'-'..mode..'.png')
end
phase=0;out:close();client.exit()
