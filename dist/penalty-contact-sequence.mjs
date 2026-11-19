import {nativePenaltyRectanglesForSelector,nativePenaltyHitbox,nativePenaltyContactDisposition} from './penalty-hitbox.mjs';
import {nativePenaltyContactResponse} from './penalty-contact-response.mjs';

// Native coordinates and selectors only. The caller supplies the correct objects
// and advances their scripts; no browser-to-native coordinate mapping is assumed.
export function selectNativePenaltyContact({tables,selector,geometry,flags,shotIndex,tick}){
 if(!Number.isSafeInteger(tick)||tick<0)throw new RangeError('Invalid contact tick');
 const preliminary=nativePenaltyContactDisposition({flags,shotIndex,hit:false});
 if(preliminary==='blocked')return {disposition:'blocked',hit:null,selection:null};
 const rectangles=nativePenaltyRectanglesForSelector(tables,selector);
 const hit=nativePenaltyHitbox({...geometry,rectangles});
 const disposition=nativePenaltyContactDisposition({flags,shotIndex,hit});
 return {disposition,hit,selection:disposition==='selected'?{phase:'pending',selectedAt:tick,selector}:null};
}

// 8C:950A is a later scripted action. A caller supplies the objects and the
// current flags, and remains responsible for advancing to deferred resolution.
export function applySelectedNativePenaltyContact(selection,{tick,flags,target,peerY,source}){
 if(!selection||selection.phase!=='pending'||!Number.isSafeInteger(tick)||tick<=selection.selectedAt||!Number.isInteger(flags)||flags<0||flags>0xffff)throw new RangeError('Invalid contact action');
 if(flags&0x20)return {...selection,phase:'cancelled',actionAt:tick,flags,target:null};
 const updatedFlags=((flags|0x800)&~0x100)&0xffff;
 return {...selection,phase:'applied',actionAt:tick,flags:updatedFlags,target:nativePenaltyContactResponse({target,peerY,source})};
}
