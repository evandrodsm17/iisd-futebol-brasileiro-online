// Machine-readable pixels for cross-checking the actual browser compositor.
import {readFileSync} from 'node:fs';
import {createJumpCapture} from '../dist/editor/jump-lab.mjs';
const data=JSON.parse(readFileSync(process.argv[2],'utf8'));
const make=(w,h)=>{const c={};c.getContext=()=>c;c.createImageData=()=>({data:new Uint8ClampedArray(w*h*4)});c.putImageData=img=>{c.pixels=img.data};return c;};
const jump=createJumpCapture(data,make),frames=[];
for(let i=0;i<jump.duration;i++)frames.push(Buffer.from(jump.frame(i).pixels).toString('base64'));
process.stdout.write(JSON.stringify(frames));
