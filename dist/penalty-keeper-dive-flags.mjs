// Flag writes in the lateral animation state 8C:91AC, after its selector call.
export function nativeLateralKeeperDiveFlags(flags){
 if(!Number.isInteger(flags)||flags<0||flags>0xffff)throw new RangeError('Invalid keeper animation flags');
 return (flags|0x2000)&0xfff7;
}
