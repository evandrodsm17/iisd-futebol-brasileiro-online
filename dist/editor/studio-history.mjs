/** Transaction-agnostic undo/redo snapshots; Blob assets are immutable by reference. */
export function createEditorHistory(limit=30){
 let past=[],future=[];
 function snapshot(state){return {package:structuredClone(state.package),images:{...state.images}};}
 return {
  capture(state){past.push(snapshot(state));if(past.length>limit)past.shift();future=[];},
  undo(state){if(!past.length)return null;future.push(snapshot(state));return past.pop();},
  redo(state){if(!future.length)return null;past.push(snapshot(state));return future.pop();},
  clear(){past=[];future=[];},
  get canUndo(){return past.length>0;},
  get canRedo(){return future.length>0;}
 };
}
