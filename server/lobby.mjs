import {WebSocketServer,WebSocket} from 'ws';
import {randomBytes} from 'node:crypto';

// Ephemeral signalling only: no simulation, persistence or player identity.
export function attachLobby(server){
 const rooms=new Map(), members=new Map();
 const wss=new WebSocketServer({server,path:'/api/v1/lobby',maxPayload:1024,perMessageDeflate:false});
 const send=(socket,message)=>{if(socket.readyState===WebSocket.OPEN)socket.send(JSON.stringify(message));};
 const snapshot=room=>({type:'room',code:room.code,players:room.players.length,capacity:2});
 function leave(socket){
  const room=members.get(socket);if(!room)return;
  members.delete(socket);room.players=room.players.filter(player=>player!==socket);
  if(!room.players.length)rooms.delete(room.code);else room.players.forEach(player=>send(player,snapshot(room)));
 }
 function code(){let value;do{value=randomBytes(4).toString('hex').toUpperCase();}while(rooms.has(value));return value;}
 wss.on('connection',socket=>{
  let windowStart=Date.now(),count=0;
  send(socket,{type:'connected',protocol:1});
  socket.on('message',(data,isBinary)=>{
   const now=Date.now();if(now-windowStart>=10000){windowStart=now;count=0;}
   if(++count>30){socket.close(1008,'rate limit');return;}
   if(isBinary)return send(socket,{type:'error',code:'invalid_message'});
   let message;try{message=JSON.parse(data.toString());}catch{return send(socket,{type:'error',code:'invalid_message'});}
   if(!message||typeof message!=='object'||Array.isArray(message))return send(socket,{type:'error',code:'invalid_message'});
   if(message.type==='create'){
    if(members.has(socket))return send(socket,{type:'error',code:'already_in_room'});
    if(rooms.size>=1000)return send(socket,{type:'error',code:'lobby_full'});
    const room={code:code(),players:[socket]};rooms.set(room.code,room);members.set(socket,room);send(socket,snapshot(room));
   }else if(message.type==='join'){
    if(members.has(socket))return send(socket,{type:'error',code:'already_in_room'});
    if(typeof message.code!=='string'||!/^[A-Fa-f0-9]{8}$/.test(message.code))return send(socket,{type:'error',code:'invalid_room_code'});
    const room=rooms.get(message.code.toUpperCase());
    if(!room)return send(socket,{type:'error',code:'room_not_found'});
    if(room.players.length>=2)return send(socket,{type:'error',code:'room_full'});
    room.players.push(socket);members.set(socket,room);room.players.forEach(player=>send(player,snapshot(room)));
   }else if(message.type==='leave'){
    leave(socket);send(socket,{type:'left'});
   }else send(socket,{type:'error',code:'unknown_message'});
  });
  socket.on('close',()=>leave(socket));socket.on('error',()=>{});
 });
 return wss;
}
