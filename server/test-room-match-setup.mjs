import test from 'node:test';
import assert from 'node:assert/strict';
import {buildRoomMatchSetup} from './room-match-setup.mjs';
test('builds a stable side mapping only after both select and confirm',()=>{
 const first={seat:1,team:30,kit:0,ready:true},second={seat:2,team:2,kit:1,ready:true};
 assert.deepEqual(buildRoomMatchSetup([second,first],'epoch','build'),{epoch:'epoch',build:'build',sides:[{team:30,kit:'home'},{team:2,kit:'away'}]});
 assert.equal(buildRoomMatchSetup([first,{...second,ready:false}],'epoch','build'),null);
 assert.equal(buildRoomMatchSetup([first,{...second,team:null}],'epoch','build'),null);
 assert.equal(buildRoomMatchSetup([first,{...second,seat:1}],'epoch','build'),null);
 assert.equal(buildRoomMatchSetup([first,{...second,kit:3}],'epoch','build'),null);
 assert.equal(buildRoomMatchSetup([first],'epoch','build'),null);
});
