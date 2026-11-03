// Browser-space line crossing. Ball size, crossbar height, and the mapping to
// the native stadium geometry remain provisional, not recovered ROM values.
const BALL_RADIUS=4.7;
const CROSSBAR_HEIGHT=24;

export function classifyFieldExit(previous,current,field,lastTouchTeam){
 if(![previous.x,previous.y,previous.z,current.x,current.y,current.z,field.x,field.y,field.w,field.h,field.goalH].every(Number.isFinite)||![0,1].includes(lastTouchTeam))throw new RangeError('Dados de saída inválidos');
 const planes=[
  {axis:'x',side:'left',line:field.x-BALL_RADIUS,sign:-1},
  {axis:'x',side:'right',line:field.x+field.w+BALL_RADIUS,sign:1},
  {axis:'y',side:'top',line:field.y-BALL_RADIUS,sign:-1},
  {axis:'y',side:'bottom',line:field.y+field.h+BALL_RADIUS,sign:1},
 ];
 const crossed=[];
 for(const p of planes){
  const before=(previous[p.axis]-p.line)*p.sign,after=(current[p.axis]-p.line)*p.sign;
  if(after<=0)continue;
  const t=before>=0?0:(-before/(after-before));
  crossed.push({...p,t});
 }
 if(!crossed.length)return null;
 crossed.sort((a,b)=>a.t-b.t);
 const hit=crossed[0],x=previous.x+(current.x-previous.x)*hit.t,y=previous.y+(current.y-previous.y)*hit.t,z=previous.z+(current.z-previous.z)*hit.t;
 if(hit.axis==='y')return {type:'throw_in',team:1-lastTouchTeam,side:hit.side,x:Math.max(field.x+28,Math.min(field.x+field.w-28,x)),y:hit.side==='top'?field.y+12:field.y+field.h-12};
 const defending=hit.side==='right'?1:0,goalTop=field.y+field.h/2-field.goalH/2,goalBottom=field.y+field.h/2+field.goalH/2;
 if(y>goalTop&&y<goalBottom&&z>=-CROSSBAR_HEIGHT)return {type:'goal',team:1-defending,side:hit.side};
 const corner=lastTouchTeam===defending;
 return {type:corner?'corner':'goal_kick',team:corner?1-defending:defending,side:hit.side,
  x:hit.side==='right'?field.x+field.w-(corner?18:65):field.x+(corner?18:65),
  y:corner?(y<field.y+field.h/2?field.y+18:field.y+field.h-18):(field.y+field.h/2+(y<field.y+field.h/2?-30:30))};
}
