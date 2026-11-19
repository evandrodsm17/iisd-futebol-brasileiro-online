import {selectNativePenaltyContact} from './penalty-contact-sequence.mjs';
const DIRECTIONS=['left','neutral','right'];
// A lookup of audited recordings, not a predictor for new shots or saves.
export function recordedPenaltyContact(data,tables,shooter,keeper){
 if(data?.schema!=='issd-penalty-contact-grid/v1'||!Array.isArray(data.cases)||!DIRECTIONS.includes(shooter)||!DIRECTIONS.includes(keeper))throw new RangeError('Invalid captured penalty comparison');
 const matches=data.cases.filter(item=>item.shooter===shooter&&item.keeper===keeper);
 if(matches.length!==1)throw new RangeError('Ambiguous captured penalty');
 const item=matches[0];
 if(!['contact_deferred','goal_branch'].includes(item.outcome)||![item.before_score,item.after_score].every(score=>Array.isArray(score)&&score.length===2&&score.every(value=>Number.isInteger(value)&&value>=0)))throw new RangeError('Invalid captured outcome');
 let contactVerified=null;
 if(item.outcome==='contact_deferred'&&tables){
  const found=selectNativePenaltyContact({tables,selector:item.selector,geometry:item.geometry,flags:item.flags,shotIndex:item.shot_index,tick:item.contact_frame});
  if(found.disposition!=='selected')throw new RangeError('Recorded contact does not match native hitbox');
  contactVerified=true;
 }
 return {outcome:item.outcome,before:[...item.before_score],after:[...item.after_score],contactVerified};
}
