// Isolated post-8B:95DF translation of 8B:A1E6..A21B.
// These words are raw native inputs; their sporting semantics are unconfirmed.
export function nativeModeFlagSelection(playerTeam,wordEDD00,wordEDD02){
 for(const value of [playerTeam,wordEDD00,wordEDD02]){
  if(!Number.isInteger(value)||value<0||value>0xffff)throw new RangeError('Expected 16-bit word');
 }
 const selector=(wordEDD00===playerTeam?1:0)+(wordEDD02===playerTeam?2:0);
 return selector===3?{selector,field1642:6,field1648:0x0160}:{selector,field1642:5,field1648:0x00e0};
}
