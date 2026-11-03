-- Passive hooks inside an isolated, automatically driven replay.
local directory=assert(os.getenv('ISSD_AUTO_OUTPUT_DIR'),'Missing output directory')
local out=assert(io.open(directory..'/slide-ball-gate.jsonl','w'))
local function u16(a)return mainmemory.read_u16_le(a) end
local function reg(name)local ok,value=pcall(emu.getregister,name);return ok and type(value)=='number' and value or -1 end
local pending=nil
local synthetic=os.getenv('ISSD_SLIDE_SYNTHETIC_CONTACT')=='1'
local function actorValid(a)return a>=0x0500 and a<=0x1a00 and a%0x100==0 end
local h1=event.onmemoryexecute(function()
 local actor=reg('D')
 if pending or reg('Y')~=0xcf6b or not actorValid(actor) then return end
 pending={frame=emu.framecount(),actor=actor,script=u16(actor+0x1c),timer=u16(actor+0x70),flags=u16(actor+0x6e),
  phase=u16(0xc0),global=u16(0x11fa),x=u16(actor+8),y=u16(actor+12),z=u16(actor+16),
  ox=u16(actor+0x38),oy=u16(actor+0x3a),oz=u16(actor+0x3c),bx=u16(0x408),by=u16(0x40c),bz=u16(0x410)}
 if synthetic then
  pending.original={pending.bx,pending.by,pending.bz}
  pending.bx=(pending.x+pending.ox)%0x10000;pending.by=(pending.y+pending.oy)%0x10000;pending.bz=(pending.z+pending.oz)%0x10000
  mainmemory.write_u16_le(0x408,pending.bx);mainmemory.write_u16_le(0x40c,pending.by);mainmemory.write_u16_le(0x410,pending.bz)
 end
end,0x85faea,'issd-slide-gate-entry')
local function finish(route)
 if not pending then return end
 local p=pending;local status=reg('P');local carry=status>=0 and status%2 or -1
 out:write(string.format('{"frame":%d,"actor":%d,"script":%d,"timer":%d,"flags":%d,"phase":%d,"global":%d,"actor_xyz":[%d,%d,%d],"offset_xyz":[%d,%d,%d],"ball_xyz":[%d,%d,%d],"synthetic":%s,"route":"%s","status":%d,"carry":%d,"flags_after":%d}\n',
  p.frame,p.actor,p.script,p.timer,p.flags,p.phase,p.global,p.x,p.y,p.z,p.ox,p.oy,p.oz,p.bx,p.by,p.bz,tostring(synthetic),route,status,carry,u16(p.actor+0x6e)))
 if p.original then mainmemory.write_u16_le(0x408,p.original[1]);mainmemory.write_u16_le(0x40c,p.original[2]);mainmemory.write_u16_le(0x410,p.original[3]) end
 out:flush();pending=nil
end
local h2=event.onmemoryexecute(function()finish('volume_return')end,0x85fb36,'issd-slide-gate-volume-return')
local h3=event.onmemoryexecute(function()finish('blocked_return')end,0x85fae4,'issd-slide-gate-blocked-return')
assert(h1 and h2 and h3,'Unable to register probes')
dofile(assert(os.getenv('ISSD_AUTO_PROBE_SCRIPT'),'Missing replay driver'))
out:close()
