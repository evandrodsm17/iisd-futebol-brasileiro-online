import {encodeOnlineInput} from './online-input.mjs';
import {decodePairedInputs} from './paired-inputs.mjs';

// Experimental transport adapter. The caller owns the socket, clock and game.
export function createOnlineInputSession(socket,seat,epoch){
 if(!socket||![1,2].includes(seat)||typeof epoch!=='string'||!/^[a-f0-9]{32}$/.test(epoch))throw new TypeError('Sessão de entrada inválida');
 let state='active',nextSend=0,nextReceive=0,nextTake=0;
 const pending=new Map(),queue=[];
 function stop(reason){state=reason;pending.clear();queue.length=0;}
 return {
  get state(){return state;},
  submit(frame){
   if(state!=='active')return {ok:false,reason:state};
   if(socket.readyState!==1){stop('disconnected');return {ok:false,reason:state};}
   if(nextSend-nextTake>=8)return {ok:false,reason:'window_full'};
   const input=encodeOnlineInput(nextSend,frame);
   if(!input)return {ok:false,reason:'invalid_input'};
   try{socket.send(JSON.stringify({type:'input-pair-test',epoch,input}));}catch{stop('disconnected');return {ok:false,reason:state};}
   pending.set(nextSend,input);nextSend++;
   return {ok:true,tick:input.tick};
  },
  receive(message){
   if(state!=='active')return false;
   if(message?.type==='room'&&(message.inputEpoch!==epoch||message.phase!=='ready')){stop('room_changed');return false;}
   if(message?.type==='error'){stop('server_error');return false;}
   if(message?.type!=='input-pair-test')return false;
   const inputs=decodePairedInputs(message,epoch,nextReceive),expected=pending.get(nextReceive);
   const received=message.inputs?.[seat-1];
   if(!inputs||!expected||!received||received.tick!==expected.tick||received.held!==expected.held||JSON.stringify(received.actions)!==JSON.stringify(expected.actions)){stop('invalid_pair');return false;}
   pending.delete(nextReceive);queue.push({tick:nextReceive,inputs});nextReceive++;
   return true;
  },
  take(){if(state!=='active'||!queue.length)return null;const pair=queue.shift();nextTake++;return pair;},
  disconnect(){if(state==='active')stop('disconnected');},
  close(){if(state==='active')stop('closed');},
 };
}
