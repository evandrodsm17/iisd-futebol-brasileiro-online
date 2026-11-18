-- Passive observation of roster selector helpers during automated startup.
local output=assert(os.getenv('ISSD_MODE_RECORD_OUTPUT'))
local automation=assert(os.getenv('ISSD_INIT_AUTOMATION'))
local out=assert(io.open(output,'w'))
out:write('{"site":"session_start"}\n');out:flush()
client.speedmode(800)
local function u(a) return mainmemory.read_u16_le(a) end
local function reg(n) local ok,v=pcall(emu.getregister,n);return ok and type(v)=='number' and v or -1 end
local contact_count=0
for _,item in ipairs({{0x8c8da1,'penalty_goal_branch'},{0x8c8dc1,'penalty_crossing_resolved'},{0x8c8e3d,'penalty_deferred_start'},{0x8c8e6f,'penalty_deferred_finalize'},{0x8c94fc,'penalty_collision_selected'},{0x8c950a,'penalty_contact_action'}}) do
 local address,name=item[1],item[2]
 assert(event.onmemoryexecute(function()
  local dp=reg('D')
  if dp<0 or dp>0xffc8 then error('Unexpected direct page') end
  out:write(string.format('{"site":"%s","frame":%d,"d":%d,"x_coord":%d,"y_coord":%d,"height":%d,"field_24":%d,"field_28":%d,"field_29":%d,"field_32":%d,"field_33":%d,"linked_object":%d,"shot_flags":%d,"side":%d,"round":%d,"penalty_home":%d,"penalty_away":%d}\n',name,emu.framecount(),dp,u(dp+8),u(dp+12),u(dp+16),u(dp+0x24),u(dp+0x28),u(dp+0x29),u(dp+0x32),u(dp+0x33),u(dp+0x36),u(0x14aa),u(0x1440),u(0x1704),mainmemory.read_u8(0xd442),mainmemory.read_u8(0xd443)))
  if name=='penalty_contact_action' then
   contact_count=contact_count+1
   pcall(client.screenshot,output..'-contact-'..contact_count..'.png')
  end
  out:flush()
 end,address,'mode-record-'..name))
end
for _,item in ipairs({{0x8c9cd2,'penalty_increment'},{0x8c9d18,'penalty_check'},{0x8c9d56,'penalty_winner'},{0x85dad6,'result_compare'}}) do
 local address,name=item[1],item[2]
 assert(event.onmemoryexecute(function()
  out:write(string.format('{"site":"%s","frame":%d,"d":%d,"a":%d,"x":%d,"y":%d,"penalty_home":%d,"penalty_away":%d,"side":%d,"round":%d,"winner":%d,"result_flags":%d,"home_score":%d,"away_score":%d}\n',name,emu.framecount(),reg('D'),reg('A'),reg('X'),reg('Y'),mainmemory.read_u8(0xd442),mainmemory.read_u8(0xd443),u(0x1440),u(0x1704),u(0x1700),u(0x0dd0),u(0x0da2),u(0x0ea2)))
  out:flush()
 end,address,'mode-record-'..name))
end
for _,item in ipairs({{0x8b9b0d,'record_write_before'},{0x8b9b11,'record_write_after'}}) do
 local address,name=item[1],item[2]
 assert(event.onmemoryexecute(function()
  local index=reg('X')
  local value=(index>=0 and index<=70 and index%2==0) and u(0xdc26+index) or -1
  out:write(string.format('{"site":"%s","frame":%d,"index":%d,"a":%d,"value":%d,"home_team":%d,"away_team":%d,"home_score":%d,"away_score":%d,"result_flags":%d,"tiebreak_word":%d}\n',name,emu.framecount(),index,reg('A'),value,u(0x0da0),u(0x0ea0),u(0x0da2),u(0x0ea2),u(0x0dd0),u(0xd442)))
  out:flush()
 end,address,'mode-record-'..name))
end
local lastRouter={}
for _,h in ipairs({{0x8ba0b2,'router'},{0x8ba0cb,'router_resolved'},{0x8b95df,'helper_before'},{0x8b9611,'helper_after'},{0x8b9f19,'ranking_start'},{0x8b9f74,'ranking_store'},{0x8b9f83,'ranking_end'},{0x8ba1e2,'selector_before'},{0x8ba1e6,'selector_after_helper'},{0x8ba21b,'selector_after'}}) do
 local address,name=h[1],h[2]
 assert(event.onmemoryexecute(function()
  if name=='router' or name=='router_resolved' then
   local signature=string.format('%d:%d:%d:%d',u(0x1642),u(0x1648),u(0x0da0),u(0xdd08))
   if signature==lastRouter[name] then return end
   lastRouter[name]=signature
  end
  if name=='ranking_start' then
   local values={}
   for offset=0,70,2 do values[#values+1]=tostring(u(0xdc26+offset)) end
   out:write(string.format('{"site":"ranking_input","frame":%d,"selected":%d,"records":[%s]}\n',emu.framecount(),u(0x19a6),table.concat(values,',')))
  end
  out:write(string.format('{"site":"%s","frame":%d,"d":%d,"a":%d,"x":%d,"y":%d,"flags":%d,"stage":%d,"mode":%d,"team":%d,"first":%d,"second":%d,"candidate":%d,"saved_team":%d}\n',name,emu.framecount(),reg('D'),reg('A'),reg('X'),reg('Y'),u(0x1648),u(0x1642),u(0x1654),u(0x0da0),u(0xdd00),u(0xdd02),u(0xdd08),u(0xdde0)))
  out:flush()
 end,address,'mode-record-'..name))
end
local ok,problem=xpcall(function() dofile(automation) end,debug.traceback)
if not ok then
 local detail=tostring(problem):match('^[^\r\n]*'):gsub('\\','\\\\'):gsub('"','\\"')
 out:write('{"site":"error","detail":"'..detail..'"}\n')
end
out:write('{"site":"session_end"}\n')
out:close();client.exit()
