// Native index decoding only; controller-to-word and screen direction remain unverified.
const INPUT_CODES=[1,9,8,10,2];
export function nativePenaltyDirection(inputWord){
 if(!Number.isInteger(inputWord)||inputWord<0||inputWord>0xffff)throw new RangeError('Invalid input word');
 const code=(inputWord>>>8)&0x0b;
 let base=INPUT_CODES.lastIndexOf(code);if(base<0)base=2;
 return {code,base,flagSet:(inputWord&0x80)!==0};
}
export function nativePenaltyShotDirection(inputWord,flags){
 if(!Number.isInteger(flags)||flags<0||flags>0xffff)throw new RangeError('Invalid flags');
 const {code,base}=nativePenaltyDirection(inputWord);
 return {code,base,index:base+((flags&0x10)===0?5:0)};
}
