-- Passive observation of roster selector helpers during automated startup.
local output=assert(os.getenv('ISSD_MODE_RECORD_OUTPUT'))
local automation=assert(os.getenv('ISSD_INIT_AUTOMATION'))
local out=assert(io.open(output,'w'))
out:write('{"site":"session_start"}\n');out:flush()
client.speedmode(800)
local function u(a) return mainmemory.read_u16_le(a) end
local function reg(n) local ok,v=pcall(emu.getregister,n);return ok and type(v)=='number' and v or -1 end
for _,item in ipairs({{0x8c9e44,'penalty_shot_decode_start'},{0x8c9e5c,'penalty_shot_decode_end'},{0x8c9f24,'penalty_shot_base_written'},{0x8c9f66,'penalty_shot_final'}}) do
 local address,name=item[1],item[2]
 assert(event.onmemoryexecute(function()
  out:write(string.format('{"site":"%s","frame":%d,"d":%d,"a":%d,"input_word":%d,"flags":%d,"direction":%d,"side":%d,"round":%d}\n',name,emu.framecount(),reg('D'),reg('A'),u(0x140c),u(0x14aa),u(0x1706),u(0x1440),u(0x1704)));out:flush()
 end,address,'mode-'..name))
end
for _,item in ipairs({{0x8c9f72,'penalty_shot_vector'},{0x8c9f73,'penalty_shot_step'}}) do
 local address,name=item[1],item[2]
 assert(event.onmemoryexecute(function()
  local d=reg('D')
  if d<0 or d>0xffc8 then error('Unexpected penalty ball context') end
  out:write(string.format('{"site":"%s","frame":%d,"d":%d,"x":%d,"side":%d,"round":%d,"index":%d,"variant":%d,"flags":%d,"px":%d,"py":%d,"pz":%d,"dx":%d,"dx_ext":%d,"dy":%d,"dy_ext":%d,"dz":%d,"dz_ext":%d}\n',name,emu.framecount(),d,reg('X'),u(0x1440),u(0x1704),u(0x1706),u(0x174e),u(0x14aa),u(d+7),u(d+0xb),u(d+0xf),u(d+0x28),mainmemory.read_u8(d+0x2a),u(d+0x32),mainmemory.read_u8(d+0x34),u(d+0x2b),mainmemory.read_u8(d+0x2d)));out:flush()
 end,address,'mode-'..name))
end
for _,item in ipairs({{0x8ca236,'penalty_history_before'},{0x8ca23a,'penalty_history_after'},{0x8ca248,'penalty_history_counter'}}) do
 local address,name=item[1],item[2]
 assert(event.onmemoryexecute(function()
  local side,x= u(0x1440),reg('X')
  local value=(x>=0x1760 and x<=0x179e and x%2==0) and u(x) or -1
  local cursor=(side==0 or side==2) and u(0x1758+side) or -1
  out:write(string.format('{"site":"%s","frame":%d,"d":%d,"a":%d,"x":%d,"entry":%d,"cursor":%d,"side":%d,"round":%d,"source_direction":%d}\n',name,emu.framecount(),reg('D'),reg('A'),x,value,cursor,side,u(0x1704),u(0x1706)));out:flush()
 end,address,'mode-'..name))
end
for _,item in ipairs({{0x8ca0af,'penalty_cpu_before'},{0x8ca0b2,'penalty_cpu_after'},{0x8ca299,'penalty_cpu_random_gate'},{0x8ca2ac,'penalty_cpu_random_pick'},{0x8ca2bd,'penalty_cpu_history'},{0x8ca2cb,'penalty_cpu_write'},{0x8ca2ce,'penalty_cpu_return'}}) do
 local address,name=item[1],item[2]
 assert(event.onmemoryexecute(function()
  out:write(string.format('{"site":"%s","frame":%d,"d":%d,"a":%d,"x":%d,"direction":%d,"other_direction":%d,"input_word":%d,"level":%d,"side":%d,"round":%d,"mask":%d,"penalty_home":%d,"penalty_away":%d,"player_setting":%d}\n',name,emu.framecount(),reg('D'),reg('A'),reg('X'),u(0x1708),u(0x1706),u(0x141a),u(0x1e54),u(0x1440),u(0x1704),u(0),mainmemory.read_u8(0xd442),mainmemory.read_u8(0xd443),u(0x11e6)));out:flush()
 end,address,'mode-'..name))
end
for _,item in ipairs({{0x8c9e2b,'penalty_direction_decode_start'},{0x8c9e43,'penalty_direction_decode_end'}}) do
 local address,name=item[1],item[2]
 assert(event.onmemoryexecute(function()
  out:write(string.format('{"site":"%s","frame":%d,"d":%d,"a":%d,"input_word":%d,"side":%d,"round":%d}\n',name,emu.framecount(),reg('D'),reg('A'),u(0x141a),u(0x1440),u(0x1704)));out:flush()
 end,address,'mode-'..name))
end
local selector_pose_seen={}
local selector_indexed_load=false
assert(event.onmemoryexecute(function() selector_indexed_load=true end,0x8c952d,'mode-selector-indexed-start'))
assert(event.onmemoryexecute(function() selector_indexed_load=false end,0x8c953b,'mode-selector-indexed-end'))
assert(event.onmemoryexecute(function()
 local dp,a,y,bank=reg('D'),reg('A'),reg('Y'),reg('B')
 if dp<0 or dp>0xffc8 then error('Unexpected animation selector context') end
 local value=a%256
 local old=u(dp+0x14)
 local pointer=u(dp+0x24)
 local source=(pointer+y)%65536
 if old~=value then
  local byte=-1
  if selector_indexed_load then
   local ok,v=pcall(memory.read_u8,bank*65536+source,'System Bus')
   if ok and type(v)=='number' then byte=v end
  else source=-1 end
  out:write(string.format('{"site":"penalty_selector_write","frame":%d,"d":%d,"old":%d,"value":%d,"bank":%d,"sequence_offset":%d,"index":%d,"indexed_load":%s,"source":%d,"source_byte":%d,"animation_state":%d,"descriptor":%d,"side":%d,"round":%d,"direction_word":%d,"input_word":%d}\n',emu.framecount(),dp,old,value,bank,pointer,y,tostring(selector_indexed_load),source,byte,u(dp+0x38),u(dp),u(0x1440),u(0x1704),u(0x1708),u(0x141a)));out:flush()
  if value==30 and not selector_pose_seen[dp] then
   selector_pose_seen[dp]=true
   pcall(client.screenshot,output..'-selector-30-'..dp..'.png')
  end
 end
end,0x8c9539,'mode-penalty-selector-write'))
local forced_text=os.getenv('ISSD_FORCE_PENALTY_SELECTOR')
local forced_selector=forced_text and tonumber(forced_text) or nil
assert(not forced_text or (forced_selector==30 and os.getenv('ISSD_AUTO_FAST_COMPETITION')=='1' and os.getenv('ISSD_AUTO_MENU_MODE')=='world_series'), 'Selector override requires isolated World Series probe')
local saved_selector=nil
local selector_writes,selector_restores=0,0
if forced_selector then
 out:write('{"site":"synthetic_selector_config","value":30}\n');out:flush()
 assert(event.onmemoryexecute(function()
  assert(not saved_selector,'Previous selector was not restored')
  local dp=reg('D')
  assert(dp>=0 and dp<=0xffc8,'Unexpected selector context')
  local object=u(dp+0x36)
  assert(object>=0x0400 and object<=0x1c00,'Unexpected selector object')
  saved_selector={object=object,original=u(object+0x14)}
  mainmemory.write_u16_le(object+0x14,forced_selector)
  selector_writes=selector_writes+1
 end,0x8c94cf,'mode-penalty-selector-override'))
 for _,item in ipairs({{0x8ca3a8,'selector_last_normal'},{0x8ca3da,'selector_last_mirrored'},{0x8ca3b1,'selector_last_upper_normal'},{0x8ca3e3,'selector_last_upper_mirrored'},{0x8ca3b4,'selector_last_after_upper_normal'},{0x8ca3e6,'selector_last_after_upper_mirrored'}}) do
  local address,name=item[1],item[2]
  assert(event.onmemoryexecute(function()
   if reg('Y')==0xde8b then
    local function bus(address) local ok,v=pcall(memory.read_u8,address,'System Bus');return ok and type(v)=='number' and v or -1 end
    out:write(string.format('{"site":"%s","frame":%d,"d":%d,"db":%d,"b":%d,"a":%d,"x":%d,"y":%d,"bus_00":%d,"bus_81":%d}\n',name,emu.framecount(),reg('D'),reg('DB'),reg('B'),reg('A'),reg('X'),reg('Y'),bus(0x00de8e),bus(0x81de8e)));out:flush()
   end
  end,address,'mode-'..name))
 end
end
local collision_snapshot=nil
local collision_checks=0
assert(event.onmemoryexecute(function()
 local dp,x,y=reg('D'),reg('X'),reg('Y')
 if dp<0 or dp>0xffc8 or x<0 or x>0xffee then error('Unexpected collision object') end
 collision_snapshot={frame=emu.framecount(),dp=dp,other=x,table_pointer=y,
  x=mainmemory.read_u8(dp+8),y=mainmemory.read_u8(dp+12),z=mainmemory.read_u8(dp+16),
  other_x=mainmemory.read_u8(x+8),other_y=mainmemory.read_u8(x+12),other_z=mainmemory.read_u8(x+16),
  object_flags=mainmemory.read_u8(dp+0x30),selector=u(dp+0x14),original_selector=saved_selector and saved_selector.original or -1,offset=mainmemory.read_u8(0x170a),side=u(0x1440),round=u(0x1704)}
 if saved_selector then
  assert(saved_selector.object==dp,'Selector object changed unexpectedly')
  mainmemory.write_u16_le(dp+0x14,saved_selector.original)
  assert(u(dp+0x14)==saved_selector.original,'Selector restore failed')
  selector_restores=selector_restores+1
  saved_selector=nil
 end
end,0x8ca375,'mode-penalty-collision-input'))
for _,item in ipairs({{0x8ca3d5,'collision_miss'},{0x8ca3d9,'collision_hit'}}) do
 local address,name=item[1],item[2]
 assert(event.onmemoryexecute(function()
  collision_checks=collision_checks+1
  local v=assert(collision_snapshot,'Missing collision input')
  if name=='collision_hit' or v.selector==30 or collision_checks%60==0 then
   out:write(string.format('{"site":"%s","frame":%d,"dp":%d,"other":%d,"table_pointer":%d,"x":%d,"y":%d,"z":%d,"other_x":%d,"other_y":%d,"other_z":%d,"object_flags":%d,"selector":%d,"original_selector":%d,"offset":%d,"side":%d,"round":%d}\n',name,v.frame,v.dp,v.other,v.table_pointer,v.x,v.y,v.z,v.other_x,v.other_y,v.other_z,v.object_flags,v.selector,v.original_selector,v.offset,v.side,v.round))
   out:flush()
  end
  collision_snapshot=nil
 end,address,'mode-'..name))
end
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
if saved_selector then mainmemory.write_u16_le(saved_selector.object+0x14,saved_selector.original);selector_restores=selector_restores+1;saved_selector=nil end
if not ok then
 local detail=tostring(problem):match('^[^\r\n]*'):gsub('\\','\\\\'):gsub('"','\\"')
 out:write('{"site":"error","detail":"'..detail..'"}\n')
end
if forced_selector then out:write(string.format('{"site":"synthetic_selector_summary","writes":%d,"restores":%d}\n',selector_writes,selector_restores));out:flush() end
out:write('{"site":"session_end"}\n')
out:close();client.exit()
