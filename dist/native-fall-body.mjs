import {createNativeCapturedAction} from './native-jump-body.mjs';
export function createNativeFallBody(data,preview,detailManifest,makeCanvas){
 return createNativeCapturedAction(data,preview,detailManifest,makeCanvas,{schema:'issd-fall-dynamic-local/v1',duration:40});
}

export async function loadNativeFallBody(){
 const responses=await Promise.all(['./assets/issd/slide-lab-local/fall-dynamic.json','./assets/issd/editor-preview-local.json','./data/issd-team-detail-colors.json'].map(path=>fetch(path)));
 if(responses.some(r=>!r.ok))throw Error('Dados locais de queda indisponíveis');
 const [data,preview,detail]=await Promise.all(responses.map(r=>r.json()));
 return createNativeFallBody(data,preview,detail,(w,h)=>{const canvas=document.createElement('canvas');canvas.width=w;canvas.height=h;return canvas;});
}
