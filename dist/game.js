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
const player = { x: 490, y: 370, vx: 0, vy: 0, team: 0, controlled: true, number: 10 };
const ball = { x: 515, y: 385, vx: 0, vy: 0, owner: player, r: 9 };

const base = [
  [205, 190],[285, 480],[390, 250],[390, 520],[520, 330],[640, 200],[670, 510],[790, 310],[850, 480],[1000, 270],[1040, 450],
  [1010, 190],[930, 480],[830, 250],[820, 525],[700, 335],[570, 205],[570, 515],[445, 300],[385, 475],[260, 265],[210, 455]
];
const players = base.map((p, i) => i === 0 ? player : ({ x:p[0], y:p[1], homeX:p[0], homeY:p[1], team:i < 11 ? 0 : 1, number:(i % 11)+1, controlled:false, phase:i*.7 }));

addEventListener('keydown', e => { if(['KeyW','KeyA','KeyS','KeyD','Space','KeyR'].includes(e.code)) e.preventDefault(); keys.add(e.code); if(e.code === 'KeyR') reset(); if(e.code === 'Space') shoot(); });
addEventListener('keyup', e => keys.delete(e.code));

function reset() { player.x=490; player.y=370; ball.x=515; ball.y=385; ball.vx=ball.vy=0; ball.owner=player; resetAt=performance.now()+1000; }
function shoot() { if(ball.owner !== player || performance.now() < resetAt) return; ball.owner=null; ball.vx=10.5; ball.vy=player.vy*.35; }
function update(dt) {
  elapsed += dt; const t = Math.floor(elapsed); clock.textContent = `${String(Math.floor(t/60)).padStart(2,'0')}:${String(t%60).padStart(2,'0')}`;
  let ax=(keys.has('KeyD')?1:0)-(keys.has('KeyA')?1:0), ay=(keys.has('KeyS')?1:0)-(keys.has('KeyW')?1:0); const len=Math.hypot(ax,ay)||1; ax/=len; ay/=len;
  player.vx += (ax*4.8-player.vx)*Math.min(1,dt*11); player.vy += (ay*4.8-player.vy)*Math.min(1,dt*11); player.x += player.vx*dt*60; player.y += player.vy*dt*60;
  player.x=Math.max(field.x+15,Math.min(field.x+field.w-15,player.x)); player.y=Math.max(field.y+15,Math.min(field.y+field.h-15,player.y));
  players.forEach(p => { if(p===player)return; const drift=Math.sin(elapsed*1.2+p.phase)*12; p.x += ((p.homeX+drift)-p.x)*dt*.7; p.y += ((p.homeY+Math.cos(elapsed+p.phase)*10)-p.y)*dt*.7; });
  if(ball.owner) { ball.x += ((player.x+18)-ball.x)*Math.min(1,dt*14); ball.y += ((player.y+7)-ball.y)*Math.min(1,dt*14); } else { ball.x+=ball.vx*dt*60; ball.y+=ball.vy*dt*60; ball.vx*=Math.pow(.982,dt*60); ball.vy*=Math.pow(.982,dt*60); if(ball.y<field.y+ball.r||ball.y>field.y+field.h-ball.r)ball.vy*=-.8; if(ball.x>field.x+field.w+20 && ball.y>H/2-field.goalH/2 && ball.y<H/2+field.goalH/2) goal(0); else if(ball.x<field.x-20 && ball.y>H/2-field.goalH/2 && ball.y<H/2+field.goalH/2) goal(1); else if(Math.abs(ball.vx)+Math.abs(ball.vy)<.25) ball.owner=player; }
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
