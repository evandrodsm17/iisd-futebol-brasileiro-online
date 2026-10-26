const canvas = document.querySelector('#game');
const ctx = canvas.getContext('2d');
const W = canvas.width, H = canvas.height;
const keys = new Set();
const blueScore = document.querySelector('#blue-score');
const redScore = document.querySelector('#red-score');
const clock = document.querySelector('#clock');
const toast = document.querySelector('#goal-toast');

const field = { x: 65, y: 52, w: 1150, h: 616, goalW: 62, goalH: 168 };
let score = [0, 0], elapsed = 0, last = performance.now(), resetAt = 0;
const player = { x: 490, y: 370, homeX: 490, homeY: 370, vx: 0, vy: 0, team: 0, controlled: true, number: 10 };
const ball = { x: 515, y: 385, vx: 0, vy: 0, owner: player, r: 9 };
let controlled = player, lastKick = 0;

const base = [
  [205, 190],[285, 480],[390, 250],[390, 520],[520, 330],[640, 200],[670, 510],[790, 310],[850, 480],[1000, 270],[1040, 450],
  [1010, 190],[930, 480],[830, 250],[820, 525],[700, 335],[570, 205],[570, 515],[445, 300],[385, 475],[260, 265],[210, 455]
];
const players = base.map((p, i) => i === 0 ? player : ({ x:p[0], y:p[1], homeX:p[0], homeY:p[1], team:i < 11 ? 0 : 1, number:(i % 11)+1, controlled:false, phase:i*.7 }));

addEventListener('keydown', e => { if(['KeyW','KeyA','KeyS','KeyD','KeyQ','Space','KeyR'].includes(e.code)) e.preventDefault(); keys.add(e.code); if(e.code === 'KeyR') reset(); if(e.code === 'KeyQ') switchPlayer(); if(e.code === 'Space') shoot(); });
addEventListener('keyup', e => keys.delete(e.code));

function reset() { players.forEach((p,i)=>{p.x=p.homeX ?? 490;p.y=p.homeY ?? 370;p.vx=p.vy=0;}); controlled=player; players.forEach(p=>p.controlled=p===controlled); ball.x=515; ball.y=385; ball.vx=ball.vy=0; ball.owner=controlled; resetAt=performance.now()+1000; }
function switchPlayer() { const candidates=players.filter(p=>p.team===0); const next=candidates.reduce((best,p)=>Math.hypot(p.x-ball.x,p.y-ball.y)<Math.hypot(best.x-ball.x,best.y-ball.y)?p:best,candidates[0]); controlled=next;players.forEach(p=>p.controlled=p===controlled); }
function shoot() { if(ball.owner !== controlled || performance.now() < resetAt) return; const direction=controlled.team===0?1:-1; ball.owner=null; ball.vx=direction*(10.2+Math.abs(controlled.vx)*.45); ball.vy=controlled.vy*.48; lastKick=performance.now(); }
function steer(p, tx, ty, speed, dt) { const dx=tx-p.x,dy=ty-p.y,mag=Math.hypot(dx,dy)||1;p.vx+=(dx/mag*speed-p.vx)*Math.min(1,dt*4.5);p.vy+=(dy/mag*speed-p.vy)*Math.min(1,dt*4.5);p.x+=p.vx*dt*60;p.y+=p.vy*dt*60; }
function update(dt) {
  elapsed += dt; const t = Math.floor(elapsed); clock.textContent = `${String(Math.floor(t/60)).padStart(2,'0')}:${String(t%60).padStart(2,'0')}`;
  let ax=(keys.has('KeyD')?1:0)-(keys.has('KeyA')?1:0), ay=(keys.has('KeyS')?1:0)-(keys.has('KeyW')?1:0); const len=Math.hypot(ax,ay)||1; ax/=len; ay/=len;
  controlled.vx += (ax*4.8-controlled.vx)*Math.min(1,dt*11); controlled.vy += (ay*4.8-controlled.vy)*Math.min(1,dt*11); controlled.x += controlled.vx*dt*60; controlled.y += controlled.vy*dt*60;
  players.forEach(p => { if(p===controlled)return; const own=ball.owner===p; const chaser=players.filter(q=>q.team===p.team).sort((a,b)=>Math.hypot(a.x-ball.x,a.y-ball.y)-Math.hypot(b.x-ball.x,b.y-ball.y))[0]===p; const attacking=ball.owner?.team===p.team; let tx=p.homeX,ty=p.homeY; if(own){tx=p.team===0?field.x+field.w-60:field.x+60;ty=H/2;} else if(chaser&&!attacking){tx=ball.x;ty=ball.y;} else if(attacking){tx=p.homeX+(p.team===0?35:-35);ty=p.homeY;} steer(p,tx,ty,chaser?3.35:2.25,dt); });
  players.forEach(p=>{p.x=Math.max(field.x+15,Math.min(field.x+field.w-15,p.x));p.y=Math.max(field.y+15,Math.min(field.y+field.h-15,p.y));});
  if(ball.owner) { ball.x += ((ball.owner.x+(ball.owner.team===0?18:-18))-ball.x)*Math.min(1,dt*14); ball.y += ((ball.owner.y+7)-ball.y)*Math.min(1,dt*14); } else { ball.x+=ball.vx*dt*60; ball.y+=ball.vy*dt*60; ball.vx*=Math.pow(.982,dt*60); ball.vy*=Math.pow(.982,dt*60); if(ball.y<field.y+ball.r||ball.y>field.y+field.h-ball.r)ball.vy*=-.8; if(ball.x>field.x+field.w+20 && ball.y>H/2-field.goalH/2 && ball.y<H/2+field.goalH/2) goal(0); else if(ball.x<field.x-20 && ball.y>H/2-field.goalH/2 && ball.y<H/2+field.goalH/2) goal(1); else if(performance.now()-lastKick>260){const nearest=players.reduce((best,p)=>Math.hypot(p.x-ball.x,p.y-ball.y)<Math.hypot(best.x-ball.x,best.y-ball.y)?p:best,players[0]);if(Math.hypot(nearest.x-ball.x,nearest.y-ball.y)<20)ball.owner=nearest;} }
}
function goal(team) { score[team]++; blueScore.textContent=score[0];redScore.textContent=score[1]; toast.textContent='GOOOL!';toast.classList.add('show');setTimeout(()=>toast.classList.remove('show'),1100);reset(); }
function line(x1,y1,x2,y2,w=3) {ctx.lineWidth=w;ctx.strokeStyle='#eff6c9cc';ctx.beginPath();ctx.moveTo(x1,y1);ctx.lineTo(x2,y2);ctx.stroke();}
function draw() {
  ctx.clearRect(0,0,W,H); ctx.fillStyle='#197045';ctx.fillRect(field.x,field.y,field.w,field.h);
  for(let i=0;i<10;i++){ctx.fillStyle=i%2?'#237b4a':'#1d7445';ctx.fillRect(field.x+i*field.w/10,field.y,field.w/10,field.h);}
  ctx.strokeStyle='#eff6c9cc';ctx.lineWidth=3;ctx.strokeRect(field.x,field.y,field.w,field.h);line(W/2,field.y,W/2,field.y+field.h);ctx.beginPath();ctx.arc(W/2,H/2,78,0,Math.PI*2);ctx.stroke();ctx.beginPath();ctx.arc(W/2,H/2,4,0,Math.PI*2);ctx.fillStyle='#eff6c9';ctx.fill();
  [[field.x,1],[field.x+field.w,-1]].forEach(([x,d])=>{ctx.strokeStyle='#ecf1d0bb';ctx.strokeRect(x-(d===1?0:92),H/2-115,92,230);ctx.strokeRect(x-(d===1?0:42),H/2-56,42,112);ctx.strokeStyle='#cfd7c066';ctx.strokeRect(x-(d===1?13:105),H/2-field.goalH/2,18,field.goalH);});
  players.forEach(drawPlayer); drawBall();
}
function drawPlayer(p) { const c=p.team?'#d94b3f':'#2787d4';ctx.save();ctx.translate(p.x,p.y);ctx.fillStyle='#0005';ctx.beginPath();ctx.ellipse(0,12,14,5,0,0,Math.PI*2);ctx.fill();ctx.fillStyle='#f1b37e';ctx.beginPath();ctx.arc(0,-10,7,0,Math.PI*2);ctx.fill();ctx.fillStyle=c;ctx.fillRect(-8,-2,16,18);ctx.fillStyle='#e8eff0';ctx.font='700 11px DM Mono';ctx.textAlign='center';ctx.fillText(p.number,0,12);ctx.fillStyle='#142d3c';ctx.fillRect(-7,16,5,9);ctx.fillRect(2,16,5,9);if(p.controlled){ctx.strokeStyle='#f9da62';ctx.lineWidth=3;ctx.beginPath();ctx.arc(0,5,17,0,Math.PI*2);ctx.stroke();}ctx.restore(); }
function drawBall(){ctx.save();ctx.translate(ball.x,ball.y);ctx.fillStyle='#0005';ctx.beginPath();ctx.ellipse(2,8,10,4,0,0,Math.PI*2);ctx.fill();ctx.fillStyle='#f4f0dc';ctx.beginPath();ctx.arc(0,0,ball.r,0,Math.PI*2);ctx.fill();ctx.fillStyle='#243331';ctx.beginPath();ctx.arc(0,0,3,0,Math.PI*2);ctx.fill();ctx.restore();}
function frame(now){const dt=Math.min(.035,(now-last)/1000);last=now;update(dt);draw();requestAnimationFrame(frame);} requestAnimationFrame(frame);
