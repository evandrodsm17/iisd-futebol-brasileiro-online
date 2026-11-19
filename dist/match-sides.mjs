// Team 0 defends left initially. A future period transition may swap sides.
export function defendingTeamOnSide(side,field){
 if(side!=='left'&&side!=='right')throw new RangeError('Invalid field side');
 const left=field?.teamsSwapped===true?1:0;
 return side==='left'?left:1-left;
}
export function teamDefendsLeft(team,field){
 if(team!==0&&team!==1)throw new RangeError('Invalid team');
 return team===defendingTeamOnSide('left',field);
}
export function mirrorFieldX(x,field){
 if(![x,field?.x,field?.w].every(Number.isFinite)||field.w<=0)throw new RangeError('Invalid field coordinates');
 return field.x+field.w-(x-field.x);
}
