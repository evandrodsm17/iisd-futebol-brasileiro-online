import {createNativeCapturedAction} from './native-jump-body.mjs';

// Separate palette banks for the captured opposing-player reception.
export async function loadNativeContestedReceiptBody(){
 const responses=await Promise.all(['./assets/issd/slide-lab-local/receipt-contested-dynamic.json','./assets/issd/editor-preview-local.json','./data/issd-team-detail-colors.json'].map(path=>fetch(path)));
 if(responses.some(r=>!r.ok))throw Error('Dados locais de recepção disputada indisponíveis');
 const [data,preview,detail]=await Promise.all(responses.map(r=>r.json()));
 return createNativeCapturedAction(data,preview,detail,(w,h)=>{const canvas=document.createElement('canvas');canvas.width=w;canvas.height=h;return canvas;},{schema:'issd-contested-receipt-local/v1',duration:44});
}
