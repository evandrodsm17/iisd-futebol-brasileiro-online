import test from 'node:test';
import assert from 'node:assert/strict';
import {createOnlineInputSession} from './online-input-session.mjs';
const frame={up:false,down:false,left:false,right:true,run:false,actions:['pass']},epoch='a'.repeat(32);
function socket(){return {readyState:1,messages:[],send(message){this.messages.push(JSON.parse(message));}};}
test('bounds unconsumed input and invalidates on room change',()=>{
 const ws=socket(),session=createOnlineInputSession(ws,1,epoch);
 for(let tick=0;tick<8;tick++)assert.deepEqual(session.submit(frame),{ok:true,tick});
 assert.deepEqual(session.submit(frame),{ok:false,reason:'window_full'});
 const pair={type:'input-pair-test',epoch,tick:0,inputs:[ws.messages[0].input,{tick:0,held:0,actions:[]}]};
 assert.equal(session.receive(pair),true);assert.equal(session.submit(frame).reason,'window_full');
 assert.equal(session.take().tick,0);assert.deepEqual(session.submit(frame),{ok:true,tick:8});
 session.receive({type:'room',inputEpoch:'b'.repeat(32),phase:'ready'});assert.equal(session.state,'room_changed');assert.equal(session.take(),null);
});
test('rejects invalid frames and mismatched server pair',()=>{
 const ws=socket(),session=createOnlineInputSession(ws,2,epoch);
 assert.equal(session.submit({...frame,actions:['reset']}).reason,'invalid_input');
 session.submit(frame);
 assert.equal(session.receive({type:'input-pair-test',epoch,tick:0,inputs:[{tick:0,held:0,actions:[]},{tick:0,held:0,actions:[]}]}),false);
 assert.equal(session.state,'invalid_pair');assert.equal(session.submit(frame).reason,'invalid_pair');
});
