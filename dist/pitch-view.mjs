import {projectPitchToCanvas,canvasDirectionToPitch} from './stadium-pitch-projection.mjs';

// Presentation adapter only; match rules remain in world coordinates.
// Custom images and unloaded/invalid resources deliberately use identity.
export function createPitchView({enabled,layout,field,crop,imageReady}){
 const active=!!enabled&&!!imageReady&&Number.isInteger(layout)&&layout>=0&&layout<=7;
 function point(x,y){return active?projectPitchToCanvas(x,y,field,crop,layout):{x,y};}
 function input(dx,dy,at){
  if(!active||(!dx&&!dy))return {x:dx,y:dy};
  const p=point(at.x,at.y),world=canvasDirectionToPitch(dx,dy,field,crop,layout,p),length=Math.hypot(world.x,world.y);
  return length?{x:world.x/length,y:world.y/length}:{x:0,y:0};
 }
 function vector(dx,dy,at){
  if(!active||(!dx&&!dy))return {x:dx,y:dy};
  const p=point(at.x,at.y),q=point(at.x+dx,at.y+dy);
  return {x:q.x-p.x,y:q.y-p.y};
 }
 return {active,point,input,vector};
}
