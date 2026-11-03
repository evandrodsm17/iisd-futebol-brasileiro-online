-- Passive execution hooks for the selected P1 in an isolated replay.
local directory=assert(os.getenv('ISSD_AUTO_OUTPUT_DIR'),'Missing output directory')
assert(os.getenv('ISSD_AUTO_REPLAY_STATE'),'An isolated replay state is required')
local out=assert(io.open(directory..'/defense-route.jsonl','w'))
local function u16(a) return mainmemory.read_u16_le(a) end
local function reg(name)
  local ok,value=pcall(emu.getregister,name)
  return ok and type(value)=='number' and value or -1
end
local locations={
  [0x849fed]='entry_9fed', [0x84a00c]='entry_02c0',
  [0x84a124]='entry_a124', [0x84a136]='branch_68_nonzero',
  [0x84a154]='carry_clear', [0x84a16e]='branch_a16e',
  [0x84a056]='entry_a056', [0x84a05e]='entry_a05e',
  [0x84a067]='entry_a067', [0x84a08d]='shared_action_handler',
  [0x849fc1]='recovery', [0x85faea]='ball_gate'
}
for address,label in pairs(locations) do
  assert(event.onmemoryexecute(function()
    local actor=reg('D')
    if actor~=u16(0x1acc) or actor<0x0500 or actor>0x1a00 or actor%0x100~=0 then return end
    out:write(string.format('{"frame":%d,"site":"%s","address":%d,"actor":%d,"a":%d,"x":%d,"y":%d,"p":%d,"link_a6":%d,"state":%d,"script":%d,"f68":%d,"f6c":%d,"f6e":%d,"f70":%d,"f76":%d,"f7a":%d,"f7e":%d,"f84":%d}\n',
      emu.framecount(),label,address,actor,reg('A'),reg('X'),reg('Y'),reg('P'),u16(0xa6),
      u16(actor+0x32),u16(actor+0x1c),u16(actor+0x68),u16(actor+0x6c),u16(actor+0x6e),
      u16(actor+0x70),u16(actor+0x76),u16(actor+0x7a),u16(actor+0x7e),u16(actor+0x84)))
    out:flush()
  end,address,'issd-defense-'..label),'Unable to register '..label)
end
dofile(assert(os.getenv('ISSD_AUTO_PROBE_SCRIPT'),'Missing replay driver'))
out:close()
