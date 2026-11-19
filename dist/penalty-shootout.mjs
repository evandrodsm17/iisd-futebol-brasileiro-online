// Decision at 8C:9D18, as audited against the USA ROM and captured hooks.
// side=0/2 is the native order, not a universal team or controller mapping.
const LIMITS = [[5, 5, 5, 3, 2], [5, 5, 3, 2, 1]];
export function nativePenaltyDecision({home,away,side,round}) {
 for(const value of [home,away])if(!Number.isInteger(value)||value<0||value>127)throw new RangeError('Invalid penalty count');
 if(![0,2].includes(side)||!Number.isInteger(round)||round<0||round>0xffff)throw new RangeError('Invalid native side or round');
 const difference=home-away;
 if(round>=5)return side!==0&&difference!==0?(difference>=0?0:2):null;
 const limit=LIMITS[side/2][round]-(side===0&&difference<0?1:0);
 return Math.abs(difference)>=limit?(difference>=0?0:2):null;
}

// Web adapter: firstTeam chooses the ordering; it is not a recovered ROM rule.
// Accept a completed outcome only. Aim, save, and completion detection are external.
export function createPenaltyShootout(firstTeam=0){
 if(![0,1].includes(firstTeam))throw new RangeError('Invalid first team');
 return {firstTeam,nextTeam:firstTeam,score:[0,0],attempts:[],winner:null};
}
export function recordPenaltyKick(state,team,scored){
 if(!state||![0,1].includes(state.firstTeam)||![0,1].includes(team)||team!==state.nextTeam||typeof scored!=='boolean'||!Array.isArray(state.score)||state.score.length!==2||!Array.isArray(state.attempts))throw new RangeError('Invalid penalty attempt');
 if(state.winner!==null)throw new RangeError('Penalty shootout has ended');
 const first=state.firstTeam,side=team===first?0:2,round=Math.floor(state.attempts.length/2);
 if(side!==(state.attempts.length%2)*2)throw new RangeError('Unexpected penalty order');
 const score=[...state.score];if(scored)score[team]++;
 const nativeWinner=nativePenaltyDecision({home:score[first],away:score[1-first],side,round});
 const winner=nativeWinner===null?null:nativeWinner===0?first:1-first;
 return {firstTeam:first,nextTeam:winner===null?1-team:null,score,attempts:[...state.attempts,{team,scored}],winner};
}
