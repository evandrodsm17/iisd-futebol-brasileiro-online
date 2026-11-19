import {nativePenaltyHitbox,nativePenaltyRectanglesForSelector} from './penalty-hitbox.mjs';
const DIRECTIONS=['left','neutral','right'];
// Replays logged calls only. Gaps are not assumed to be negative tests.
export function recordedPenaltyChecks(data,tables,shooter,keeper){
 if(data?.schema!=='issd-penalty-contact-timeline/v1'||!Array.isArray(data.cases)||!DIRECTIONS.includes(shooter)||!DIRECTIONS.includes(keeper))throw new RangeError('Invalid recorded contact sequence');
 const matches=data.cases.filter(c=>c.shooter===shooter&&c.keeper===keeper);
 if(matches.length===0)return null;
 if(matches.length!==1||!Array.isArray(matches[0].checks)||!matches[0].checks.length)throw new RangeError('Ambiguous contact sequence');
 let previous=-1;
 return matches[0].checks.map(check=>{
  if(!Number.isSafeInteger(check.frame)||check.frame<=previous||typeof check.hit!=='boolean')throw new RangeError('Invalid recorded check');
  previous=check.frame;
  let verified=null;
  if(tables){
   const rectangles=nativePenaltyRectanglesForSelector(tables,check.selector);
   const result=nativePenaltyHitbox({...check.geometry,rectangles});
   if(result!==check.hit)throw new RangeError('Recorded hitbox result differs');
   verified=true;
  }
  return {frame:check.frame,selector:check.selector,hit:check.hit,verified};
 });
}
