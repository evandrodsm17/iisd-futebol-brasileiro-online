// Flag writes in the lateral animation state 8C:91AC, after its selector call.
export function nativeLateralKeeperDiveFlags(flags){
 if(!Number.isInteger(flags)||flags<0||flags>0xffff)throw new RangeError('Invalid keeper animation flags');
 return (flags|0x2000)&0xfff7;
}

// Flag writes in the central animation state 8C:92B8.
export function nativeCentralKeeperDiveFlags(flags){
 if(!Number.isInteger(flags)||flags<0||flags>0xffff)throw new RangeError('Invalid keeper animation flags');
 return (flags|0x2000)&0xfffb;
}

// Relevant 8C:91D2 branch after its animation helper has returned.
export function nativeLateralKeeperLandingFlags(flags,heightWord){
 for(const value of [flags,heightWord])if(!Number.isInteger(value)||value<0||value>0xffff)throw new RangeError('Invalid keeper landing state');
 return heightWord&0x8000?flags:flags&0xdffd;
}
