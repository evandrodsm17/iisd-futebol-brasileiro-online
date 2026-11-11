-- Isolated synthetic cases: RAM edits only after restoring the same state.
-- These samples demonstrate the exercised paths, not natural match outcomes.
local state=assert(os.getenv('ISSD_GOAL_STATE'),'missing state')
local output=assert(os.getenv('ISSD_GOAL_OUTPUT'),'missing output')
local f=assert(io.open(output,'w'))
local function u(a)return mainmemory.read_u16_le(a)end
local function w(a,v)mainmemory.write_u16_le(a,v%65536)end
local trial,step=0,0
local active=false
local frames=tonumber(os.getenv('ISSD_GOAL_FRAMES') or '24')
assert(frames and frames%1==0 and frames>=24 and frames<=300,'invalid frame count')
local focused=os.getenv('ISSD_GOAL_FOCUSED')=='1'
local edge=os.getenv('ISSD_GOAL_EDGE')=='1'
local longCamera=os.getenv('ISSD_GOAL_CAMERA_LONG')=='1'
local visible=longCamera or os.getenv('ISSD_GOAL_CAMERA_WARMUP')=='1' -- experimental; does not guarantee camera alignment
local sides=visible and {1} or {-1,1}
local offsets=longCamera and {55} or visible and {-55,-49,48,55} or edge and {-56,-55,-49,-48,47,48,55,56} or focused and {-49,-48,0,47,48} or {-57,-56,-49,-48,0,47,48,55,56}
local heights=visible and {0} or edge and {0,-55,-56,-57,-63,-64} or focused and {0,-56} or {0,-55,-56,-64}
local shots=os.getenv('ISSD_GOAL_SCREENSHOT_DIR')
local hooks={{0x838bab,'838BAB'},{0x838bc8,'838BC8'},{0x838bf8,'838BF8'},{0x83a000,'83A000'},{0xa49af2,'A49AF2'},{0x80bf05,'80BF05'},{0x838c3b,'838C3B'},{0x838c51,'838C51'},{0x8390b3,'8390B3'},{0x83a900,'83A900'},{0x838726,'838726'},{0x839073,'839073'},{0x8390cb,'8390CB'},{0x83a90e,'83A90E'},{0x838d76,'838D76'},{0x838d23,'838D23'},{0x838ddc,'838DDC'},{0x838f04,'838F04'},{0x86d98c,'86D98C'}}
for _,h in ipairs(hooks) do
 local addr,name=h[1],h[2]
 assert(event.onmemoryexecute(function()
  if not active then return end
  f:write(string.format('{"type":"hook","trial":%d,"step":%d,"pc":"%s","x":%d,"y":%d,"z":%d,"vx":%d,"vy":%d,"vz":%d,"vxLo":%d,"vyLo":%d,"vzLo":%d,"direction":%d,"state":%d,"regA":%d,"regX":%d,"local2a":%d,"local2c":%d,"bandLow":%d,"bandHigh":%d}\n',trial,step,name,u(0x408),u(0x40c),u(0x410),u(0x424),u(0x428),u(0x436),u(0x422),u(0x426),u(0x434),u(0x452),u(0x430),emu.getregister("A"),emu.getregister("X"),u(0x42a),u(0x42c),u(0x1c80),u(0x1c86)))
 end,addr,'goal-audit-'..name))
end
for _,side in ipairs(sides) do
 for _,offset in ipairs(offsets) do
  for _,height in ipairs(heights) do
   trial=trial+1;step=0
   active=false
   assert(savestate.load(state,true),'state load failed')
   local width,heightField=u(0x12a2),u(0x12a4)
   assert(width>0 and heightField>0,'missing stadium dimensions')
   if visible then
    for warm=1,(longCamera and 2100 or 150) do
     local targetX,targetY=width-(longCamera and 40 or 180),math.floor(heightField/2)+offset
     w(0xa4,0);w(0xa6,0);w(0x406,0);w(0x408,targetX+targetY-u(0x98));w(0x40a,0);w(0x40c,targetY-u(0x9a));w(0x40e,0);w(0x410,0)
     w(0x422,0);w(0x424,0);w(0x426,0);w(0x428,0);w(0x434,0);w(0x436,0);w(0x430,3)
     joypad.set({},1);joypad.set({},2);emu.frameadvance()
    end
   end
   w(0xa4,0);w(0xa6,0)
   -- D31A: $2C=$009A+$0C; $2A=$0098+$08-$2C. Invert it.
   local nativeX=side==-1 and 12 or width-12
   local nativeY=math.floor(heightField/2)+offset
   w(0x406,0);w(0x408,nativeX+nativeY-u(0x98));w(0x40a,0);w(0x40c,nativeY-u(0x9a));w(0x40e,0);w(0x410,height)
   w(0x422,0);w(0x424,side*4);w(0x426,0);w(0x428,0);w(0x434,0);w(0x436,0);w(0x430,3)
   f:write(string.format('{"type":"case","trial":%d,"side":%d,"offset":%d,"height":%d,"width":%d,"fieldHeight":%d,"stadium":%d}\n',trial,side,offset,height,width,heightField,u(0x86)))
   active=true
   for i=1,frames do
    step=i;joypad.set({},1);joypad.set({},2);emu.frameadvance()
    f:write(string.format('{"type":"frame","trial":%d,"step":%d,"x":%d,"y":%d,"z":%d,"vx":%d,"vy":%d,"vz":%d,"state":%d,"globalBA":%d,"nativeX":%d,"nativeY":%d,"score1":%d,"score2":%d,"gameState":%d}\n',trial,step,u(0x408),u(0x40c),u(0x410),u(0x424),u(0x428),u(0x436),u(0x430),u(0xba),u(0x42a),u(0x42c),u(0xda2),u(0xea2),u(0x14d6)))
    if shots and (i==1 or i==4 or i==8 or i==12 or i==24 or i==40 or i==100) then pcall(client.screenshot,shots..string.format("/goal-%02d-%03d.png",trial,i)) end
   end
  end
 end
end
f:flush();f:close();print('Goal audit complete: '..trial..' synthetic trials')
client.exit()
