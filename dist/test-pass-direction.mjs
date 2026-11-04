import assert from 'node:assert/strict';
import {passDirection} from './pass-direction.mjs';
const vectors=[[0,-1],[1,-1],[1,0],[1,1],[0,1],[-1,1],[-1,0],[-1,-1]];
for(let i=0;i<vectors.length;i++){
 const [x,y]=vectors[i],n=Math.hypot(x,y),result=passDirection(x,y,(i+4)%8),facing=passDirection(0,0,i);
 assert.equal(result.x,x/n);assert.equal(result.y,y/n);
 assert.equal(facing.x,x/n);assert.equal(facing.y,y/n);
}
assert.deepEqual(passDirection(0,0,undefined),{x:1,y:0});
console.log('OK: passe respeita entrada atual e orientação anterior nas oito direções');
