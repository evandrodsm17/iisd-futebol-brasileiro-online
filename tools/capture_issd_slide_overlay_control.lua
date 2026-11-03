-- Read-only neutral replay screenshots at the six slide snapshot frames.
local directory=assert(os.getenv('ISSD_AUTO_OUTPUT_DIR'),'Missing output directory')
assert(os.getenv('ISSD_AUTO_REPLAY_STATE'),'An isolated replay is required')
local out=assert(io.open(directory..'/overlay-control.jsonl','w'))
local wanted={[4276]=true,[4278]=true,[4280]=true,[4291]=true,[4296]=true,[4301]=true}
local handle=event.onframeend(function()
 local frame=emu.framecount()
 if not wanted[frame] then return end
 local file=string.format('control-%d.png',frame)
 local ok=pcall(client.screenshot,directory..'/'..file)
 out:write(string.format('{"frame":%d,"screenshot":"%s","success":%s}\n',frame,file,tostring(ok)))
 out:flush()
end,'issd-slide-overlay-control')
assert(handle,'Unable to register control capture')
dofile(assert(os.getenv('ISSD_AUTO_PROBE_SCRIPT'),'Missing replay driver'))
out:close()
