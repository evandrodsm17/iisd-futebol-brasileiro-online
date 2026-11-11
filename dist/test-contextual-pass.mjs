import test from 'node:test';
import assert from 'node:assert/strict';
import { contextualPassAction } from './contextual-pass.mjs';
test('passe com posse, desarme sem posse e nenhuma acao contra companheiro',()=>{
 const a={team:0},mate={team:0},opponent={team:1},input={right:true},calls=[];
 const handlers={pass:(actor,frame)=>calls.push(['pass',actor,frame]),press:(actor,frame)=>calls.push(['press',actor,frame])};
 contextualPassAction(a,a,input,handlers);contextualPassAction(a,opponent,input,handlers);contextualPassAction(a,null,input,handlers);contextualPassAction(a,mate,input,handlers);contextualPassAction(null,opponent,input,handlers);
 assert.deepEqual(calls,[['pass',a,input],['press',a,input],['press',a,input]]);
});
