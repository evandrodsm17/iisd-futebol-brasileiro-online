// Proposed transport contract, independent of the lobby and match runtime.
// It does not send messages or advance a simulation.
const ACTIONS=new Set(['switch','shot','pass','press']);
const FIELDS=['up','down','left','right','run'];
const MASKS=[1,2,4,8,16];
const MAX_ACTIONS=32;

function validTick(tick){return Number.isSafeInteger(tick)&&tick>=0;}
function validActions(actions){return Array.isArray(actions)&&actions.length<=MAX_ACTIONS&&actions.every(action=>typeof action==='string'&&ACTIONS.has(action));}

export function encodeOnlineInput(tick,frame){
 if(!validTick(tick)||!frame||typeof frame!=='object'||Array.isArray(frame)||!FIELDS.every(field=>typeof frame[field]==='boolean')||!validActions(frame.actions))return null;
 let held=0;for(let i=0;i<FIELDS.length;i++)if(frame[FIELDS[i]])held|=MASKS[i];
 return {tick,held,actions:[...frame.actions]};
}

export function decodeOnlineInput(packet){
 if(!packet||typeof packet!=='object'||Array.isArray(packet)||Object.keys(packet).length!==3||!Object.hasOwn(packet,'tick')||!Object.hasOwn(packet,'held')||!Object.hasOwn(packet,'actions')||!validTick(packet.tick)||!Number.isInteger(packet.held)||packet.held<0||packet.held>31||!validActions(packet.actions))return null;
 const frame={};for(let i=0;i<FIELDS.length;i++)frame[FIELDS[i]]=!!(packet.held&MASKS[i]);
 frame.actions=[...packet.actions];
 return {tick:packet.tick,frame};
}
