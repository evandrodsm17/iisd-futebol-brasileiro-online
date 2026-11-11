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
local variation=os.getenv('ISSD_GOAL_VARIATION')=='1'
local variationSide=tonumber(os.getenv('ISSD_GOAL_SIDE') or '1')
assert(variationSide==1 or variationSide==-1,'invalid goal side')
local matrix=variation or os.getenv('ISSD_GOAL_MATRIX')=='1'
local reuseWarm=matrix and os.getenv('ISSD_GOAL_MATRIX_REUSE')=='1'
local warmState=matrix and assert(os.getenv('ISSD_GOAL_WARM_STATE'),'missing warm state path') or nil
local longCamera=matrix or os.getenv('ISSD_GOAL_CAMERA_LONG')=='1'
local visible=longCamera or os.getenv('ISSD_GOAL_CAMERA_WARMUP')=='1' -- experimental; does not guarantee camera alignment
local sides=variation and {variationSide} or visible and {1} or {-1,1}
local speeds=variation and {2,4,6} or {4}
local offsets=variation and {0} or matrix and {-55,-49,0,48,55} or longCamera and {55} or visible and {-55,-49,48,55} or edge and {-56,-55,-49,-48,47,48,55,56} or focused and {-49,-48,0,47,48} or {-57,-56,-49,-48,0,47,48,55,56}
local heights=variation and {-56,-63,-64} or matrix and {0,-55,-56,-63,-64} or visible and {0} or edge and {0,-55,-56,-57,-63,-64} or focused and {0,-56} or {0,-55,-56,-64}
local shots=os.getenv('ISSD_GOAL_SCREENSHOT_DIR')
local hooks={{0x838aff,'838AFF'},{0x838b15,'838B15'},{0x838b47,'838B47'},{0x838b75,'838B75'},{0x838b85,'838B85'},{0x838b96,'838B96'},{0x838d08,'838D08'},{0x838bab,'838BAB'},{0x838bc8,'838BC8'},{0x838bf8,'838BF8'},{0x83a000,'83A000'},{0xa49af2,'A49AF2'},{0x80bf05,'80BF05'},{0x838c3b,'838C3B'},{0x838c51,'838C51'},{0x8390b3,'8390B3'},{0x83a900,'83A900'},{0x838726,'838726'},{0x839073,'839073'},{0x8390cb,'8390CB'},{0x83a90e,'83A90E'},{0x838d76,'838D76'},{0x838d23,'838D23'},{0x838ddc,'838DDC'},{0x838f04,'838F04'},{0x86d98c,'86D98C'}}
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
   for _,speed in ipairs(speeds) do
   trial=trial+1;step=0
   active=false
   assert(savestate.load(matrix and (trial>1 or reuseWarm) and warmState or state,true),'state load failed')
   local width,heightField=u(0x12a2),u(0x12a4)
   assert(width>0 and heightField>0,'missing stadium dimensions')
   if visible and (not matrix or (trial==1 and not reuseWarm)) then
    for warm=1,(longCamera and 2100 or 150) do
     local targetX,targetY=(variation and variationSide==-1) and 40 or width-(longCamera and 40 or 180),math.floor(heightField/2)+(matrix and 55 or offset)
     w(0xa4,0);w(0xa6,0);w(0x406,0);w(0x408,targetX+targetY-u(0x98));w(0x40a,0);w(0x40c,targetY-u(0x9a));w(0x40e,0);w(0x410,0)
     w(0x422,0);w(0x424,0);w(0x426,0);w(0x428,0);w(0x434,0);w(0x436,0);w(0x430,3)
     joypad.set({},1);joypad.set({},2);emu.frameadvance()
    end
    if matrix then assert(savestate.save(warmState,true),'warm state save failed') end
   end
   w(0xa4,0);w(0xa6,0)
   -- D31A: $2C=$009A+$0C; $2A=$0098+$08-$2C. Invert it.
   local nativeX=side==-1 and 12 or width-12
   local nativeY=math.floor(heightField/2)+offset
   w(0x406,0);w(0x408,nativeX+nativeY-u(0x98));w(0x40a,0);w(0x40c,nativeY-u(0x9a));w(0x40e,0);w(0x410,height)
   w(0x422,0);w(0x424,side*speed);w(0x426,0);w(0x428,0);w(0x434,0);w(0x436,0);w(0x430,3)
   f:write(string.format('{"type":"case","trial":%d,"side":%d,"offset":%d,"height":%d,"speed":%d,"width":%d,"fieldHeight":%d,"stadium":%d}\n',trial,side,offset,height,speed,width,heightField,u(0x86)))
   active=true
   for i=1,frames do
    step=i;joypad.set({},1);joypad.set({},2);emu.frameadvance()
    f:write(string.format('{"type":"frame","trial":%d,"step":%d,"x":%d,"y":%d,"z":%d,"vx":%d,"vy":%d,"vz":%d,"state":%d,"globalBA":%d,"nativeX":%d,"nativeY":%d,"score1":%d,"score2":%d,"gameState":%d}\n',trial,step,u(0x408),u(0x40c),u(0x410),u(0x424),u(0x428),u(0x436),u(0x430),u(0xba),u(0x42a),u(0x42c),u(0xda2),u(0xea2),u(0x14d6)))
    if shots and (i==1 or i==4 or i==8 or i==12 or i==24 or i==40 or i==100) then pcall(client.screenshot,shots..string.format("/goal-%02d-%03d.png",trial,i)) end
   end
   end
  end
 end
end
f:flush();f:close();print('Goal audit complete: '..trial..' synthetic trials')
client.exit()
