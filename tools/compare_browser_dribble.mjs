import { DRIBBLE, settleDribble } from '../dist/dribble-contact.mjs';

export function compareBrowserDribble() {
  const results={};
  for (const variant of ['legacy','current']) {
    const player={x:490,y:370,vx:0,vy:0,team:0,facingDirection:2};
    const ball={x:502,y:375,vx:0,vy:0,owner:true};
    const samples=[];
    for(let frame=0;frame<150;frame++){
      const [vx,vy,direction]=frame<60?[2,0,2]:frame<90?[0,-2,0]:frame<120?[-2,0,6]:[0,0,6];
      Object.assign(player,{vx,vy,facingDirection:direction});
      player.x+=vx;player.y+=vy;
      if(ball.owner){
        if(variant==='legacy'){
          const distance=Math.hypot(player.x-ball.x,player.y-ball.y);
          if(distance>=24)ball.owner=false;
          else if(distance<16&&Math.hypot(vx,vy)>.25){
            const speed=Math.hypot(vx,vy),kick=3.2+Math.min(.6,speed*.12);
            ball.vx=vx/speed*kick;ball.vy=vy/speed*kick;
          }
        }else{
          const state=settleDribble(ball,player,1);
          if(state.distanceAfter>DRIBBLE.releaseDistance)ball.owner=false;
        }
      }
      if(variant==='legacy'||!ball.owner){
        ball.x+=ball.vx;ball.y+=ball.vy;
        const speed=Math.hypot(ball.vx,ball.vy),next=Math.max(0,speed-.03125);
        if(speed){ball.vx=ball.vx*next/speed;ball.vy=ball.vy*next/speed;}
      }
      samples.push({frame:frame+1,distance:Math.hypot(player.x-ball.x,player.y-ball.y),owner:ball.owner});
    }
    results[variant]={
      ownerLostAt:samples.find(s=>!s.owner)?.frame??null,
      distanceByFrame:Object.fromEntries([30,60,120,150].map(n=>[n,Number(samples[n-1].distance.toFixed(3))])),
      largestDistance:Number(Math.max(...samples.map(s=>s.distance)).toFixed(3))
    };
  }
  return {schema:'issd-browser-dribble-comparison/v1',frames:150,segments:['straight:60','up:30','reverse:30','stop:30'],results,
    limitation:'Browser world units; not equivalent to ROM WRAM units. The legacy branch is a historical reconstruction.'};
}
if(import.meta.url===new URL('file://'+process.argv[1]).href)console.log(JSON.stringify(compareBrowserDribble(),null,2));
