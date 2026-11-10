import {readFileSync} from 'node:fs';
import {renderRuntimeBody} from '../dist/native-runtime-body.mjs';
const data=JSON.parse(readFileSync(process.argv[2],'utf8'));
const palette=data.palette.map(word=>'#'+[0,5,10].map(shift=>{const c=(word>>shift)&31;return ((c<<3)|(c>>2)).toString(16).padStart(2,'0');}).join(''));
console.log(JSON.stringify(data.frames.map((_,i)=>Buffer.from(renderRuntimeBody(data,i,palette,{4:palette}).rgba).toString('base64'))));
