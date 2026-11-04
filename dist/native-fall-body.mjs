import {createNativeCapturedAction} from './native-jump-body.mjs';
export function createNativeFallBody(data,preview,detailManifest,makeCanvas){
 return createNativeCapturedAction(data,preview,detailManifest,makeCanvas,{schema:'issd-fall-dynamic-local/v1',duration:40});
}
