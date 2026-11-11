import test from 'node:test';
import assert from 'node:assert/strict';
import {dispatchHumanActions} from './human-actions.mjs';

test('dispatches actions to each team and resolves player again after switching',()=>{
 const one={team:0,id:'one'},two={team:1,id:'two'},substitute={team:1,id:'substitute'};
 const actors=new Map([[0,one],[1,two]]),calls=[];
 const handlers={reset:()=>calls.push('reset'),switchPlayer:team=>{calls.push(`switch-${team}`);actors.set(team,substitute);},getActor:team=>actors.get(team),shoot:(actor)=>calls.push(`shoot-${actor.id}`),pass:(actor)=>calls.push(`pass-${actor.id}`),press:(actor)=>calls.push(`press-${actor.id}`)};
 dispatchHumanActions(1,{actions:['pass','switch','shot','press','reset']},handlers);
 dispatchHumanActions(0,{actions:['shot','reset']},handlers);
 assert.deepEqual(calls,['pass-two','switch-1','shoot-substitute','press-substitute','shoot-one','reset']);
});
test('ignores player actions when a team has no human actor',()=>{
 let called=false;const handlers={getActor:()=>undefined,shoot:()=>{called=true;},pass:()=>{called=true;},press:()=>{called=true;}};
 dispatchHumanActions(1,{actions:['shot','pass','press']},handlers);assert.equal(called,false);
});
