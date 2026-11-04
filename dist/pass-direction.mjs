// Provisional web pass direction: current input wins; otherwise retain facing.
const DIRECTIONS=[[0,-1],[1,-1],[1,0],[1,1],[0,1],[-1,1],[-1,0],[-1,-1]];
export function passDirection(inputX,inputY,facing){
 let x=Math.sign(Number.isFinite(inputX)?inputX:0),y=Math.sign(Number.isFinite(inputY)?inputY:0);
 if(!x&&!y)[x,y]=DIRECTIONS[Number.isInteger(facing)&&facing>=0&&facing<8?facing:2];
 const length=Math.hypot(x,y);
 return {x:x/length,y:y/length};
}
