// Exact 80:DA68..DA7B update on 16-bit words. This module does not determine
// the caller's frequency, which controller is active, or web button mapping.
const word=n=>Number.isInteger(n)&&n>=0&&n<=0xffff;
export function updateNativeActionCharge({held,mask,count}) {
 if(![held,mask,count].every(word))throw new RangeError('Invalid native charge state');
 return held&mask && count<11 ? {mask,count:count+1} : {mask:0,count};
}
