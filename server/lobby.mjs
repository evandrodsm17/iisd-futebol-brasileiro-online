import {WebSocketServer,WebSocket} from 'ws';
import {randomBytes} from 'node:crypto';
import {readFileSync} from 'node:fs';
import {gameBuildIdentity} from './build-identity.mjs';
import {decodeOnlineInput} from '../dist/online-input.mjs';
import {createInputPairBuffer} from './input-pair-buffer.mjs';
import {buildRoomMatchSetup} from './room-match-setup.mjs';

const teams=JSON.parse(readFileSync(new URL('../dist/data/issd-rom-catalog.json',import.meta.url),'utf8')).teams.map(({id,name})=>({id,name}));
const stadiums=JSON.parse(readFileSync(new URL('../dist/data/issd-stadium-layouts.json',import.meta.url),'utf8')).layouts.map(({id,name})=>({id,name}));
const stadiumIds=new Set(stadiums.map(stadium=>stadium.id));
const gameTimes=new Set(JSON.parse(readFileSync(new URL('../dist/data/issd-match-settings.json',import.meta.url),'utf8')).settings.game_time.values);
const PROTOCOL=2;
const teamIds=new Set(teams.map(team=>team.id));

// Ephemeral signalling only: no simulation, persistence or player identity.
export async function attachLobby(server,{heartbeatMs=15000}={}){
 const build=await gameBuildIdentity();
 const rooms=new Map(), members=new Map();
 const wss=new WebSocketServer({server,path:'/api/v1/lobby',maxPayload:1024,perMessageDeflate:false});
 const heartbeat=setInterval(()=>{
  for(const socket of wss.clients){if(!socket.isAlive){socket.terminate();continue;}socket.isAlive=false;socket.ping();}
 },heartbeatMs);
 heartbeat.unref();
 wss.on('close',()=>clearInterval(heartbeat));
 const send=(socket,message)=>{if(socket.readyState===WebSocket.OPEN)socket.send(JSON.stringify(message));};
 const snapshot=(room,socket)=>({type:'room',code:room.code,players:room.players.length,capacity:2,hostSeat:room.players.find(player=>player.socket===room.host).seat,settings:{...room.settings},inputEpoch:room.inputEpoch,matchSetup:buildRoomMatchSetup(room.players,room.inputEpoch,build,room.settings),phase:room.players.length<2?'waiting':room.players.every(player=>player.team!==null&&player.ready)?'ready':'selection',seat:room.players.find(player=>player.socket===socket).seat,participants:room.players.map(({seat,ready,team,kit})=>({seat,ready,team,kit})).sort((a,b)=>a.seat-b.seat)});
 const resetStreams=room=>{room.inputEpoch=randomBytes(16).toString('hex');room.inputPairs=createInputPairBuffer();room.players.forEach(player=>{player.nextInputTick=0;});};
 const broadcast=room=>room.players.forEach(player=>send(player.socket,snapshot(room,player.socket)));
 function leave(socket){
  const room=members.get(socket);if(!room)return;
  members.delete(socket);room.players=room.players.filter(player=>player.socket!==socket);if(room.host===socket&&room.players.length)room.host=room.players[0].socket;
  if(!room.players.length)rooms.delete(room.code);else {room.players.forEach(player=>{player.ready=false;});resetStreams(room);broadcast(room);}
 }
 function code(){let value;do{value=randomBytes(4).toString('hex').toUpperCase();}while(rooms.has(value));return value;}
 wss.on('connection',socket=>{
  socket.isAlive=true;socket.on('pong',()=>{socket.isAlive=true;});
  let windowStart=Date.now(),count=0,inputCount=0;
  send(socket,{type:'connected',protocol:PROTOCOL,build,teams,stadiums,gameTimes:[...gameTimes]});
  socket.on('message',(data,isBinary)=>{
   const now=Date.now();if(now-windowStart>=10000){windowStart=now;count=0;inputCount=0;}
   const invalid=()=>{if(++count>30)socket.close(1008,'rate limit');else send(socket,{type:'error',code:'invalid_message'});};
   if(isBinary)return invalid();
   let message;try{message=JSON.parse(data.toString());}catch{return invalid();}
   if(!message||typeof message!=='object'||Array.isArray(message))return invalid();
   if((message.type==='input-test'||message.type==='input-pair-test') ? ++inputCount>900 : ++count>30){socket.close(1008,'rate limit');return;}
   if((message.type==='create'||message.type==='join')&&message.protocol!==PROTOCOL)return send(socket,{type:'error',code:'protocol_mismatch'});
   if((message.type==='create'||message.type==='join')&&message.build!==build)return send(socket,{type:'error',code:'build_mismatch'});
   if(message.type==='create'){
    if(members.has(socket))return send(socket,{type:'error',code:'already_in_room'});
    if(rooms.size>=1000)return send(socket,{type:'error',code:'lobby_full'});
    const room={code:code(),host:socket,settings:{stadium:1,gameTime:1},inputEpoch:randomBytes(16).toString('hex'),inputPairs:createInputPairBuffer(),players:[{socket,seat:1,ready:false,team:null,kit:0,nextInputTick:0}]};rooms.set(room.code,room);members.set(socket,room);broadcast(room);
   }else if(message.type==='join'){
    if(members.has(socket))return send(socket,{type:'error',code:'already_in_room'});
    if(typeof message.code!=='string'||!/^[A-Fa-f0-9]{8}$/.test(message.code))return send(socket,{type:'error',code:'invalid_room_code'});
    const room=rooms.get(message.code.toUpperCase());
    if(!room)return send(socket,{type:'error',code:'room_not_found'});
    if(room.players.length>=2)return send(socket,{type:'error',code:'room_full'});
    room.players.forEach(player=>{player.ready=false;});
    room.players.push({socket,seat:room.players.some(player=>player.seat===1)?2:1,ready:false,team:null,kit:0,nextInputTick:0});members.set(socket,room);resetStreams(room);broadcast(room);
   }else if(message.type==='selection'){
    const room=members.get(socket);
    if(!room)return send(socket,{type:'error',code:'not_in_room'});
    if(!Number.isInteger(message.team)||!teamIds.has(message.team)||(message.kit!==0&&message.kit!==1))return send(socket,{type:'error',code:'invalid_selection'});
    const player=room.players.find(player=>player.socket===socket);
    if(player.team!==message.team||player.kit!==message.kit){player.team=message.team;player.kit=message.kit;room.players.forEach(p=>{p.ready=false;});resetStreams(room);}
    broadcast(room);
   }else if(message.type==='settings'){
    const room=members.get(socket);
    if(!room)return send(socket,{type:'error',code:'not_in_room'});
    if(room.host!==socket)return send(socket,{type:'error',code:'host_only'});
    if(!Number.isInteger(message.stadium)||!stadiumIds.has(message.stadium)||!Number.isInteger(message.gameTime)||!gameTimes.has(message.gameTime))return send(socket,{type:'error',code:'invalid_settings'});
    if(room.settings.stadium!==message.stadium||room.settings.gameTime!==message.gameTime){room.settings={stadium:message.stadium,gameTime:message.gameTime};room.players.forEach(player=>{player.ready=false;});resetStreams(room);}
    broadcast(room);
   }else if(message.type==='ready'){
    const room=members.get(socket);
    if(!room)return send(socket,{type:'error',code:'not_in_room'});
    if(typeof message.ready!=='boolean')return send(socket,{type:'error',code:'invalid_ready'});
    const player=room.players.find(player=>player.socket===socket);
    if(message.ready&&player.team===null)return send(socket,{type:'error',code:'selection_required'});
    if(player.ready!==message.ready){player.ready=message.ready;resetStreams(room);}
    broadcast(room);
   }else if(message.type==='input-pair-test'){
    const room=members.get(socket);
    if(!room)return send(socket,{type:'error',code:'not_in_room'});
    if(room.players.length!==2||!room.players.every(player=>player.ready&&player.team!==null))return send(socket,{type:'error',code:'room_not_ready'});
    if(typeof message.epoch!=='string'||message.epoch!==room.inputEpoch)return send(socket,{type:'error',code:'stale_input_epoch'});
    const player=room.players.find(player=>player.socket===socket);
    const result=room.inputPairs.submit(player.seat,message.input);
    if(result.error)return send(socket,{type:'error',code:result.error});
    if(result.pair)room.players.forEach(other=>send(other.socket,{type:'input-pair-test',epoch:room.inputEpoch,...result.pair}));
   }else if(message.type==='input-test'){
    const room=members.get(socket);
    if(!room)return send(socket,{type:'error',code:'not_in_room'});
    if(room.players.length!==2||!room.players.every(player=>player.ready&&player.team!==null))return send(socket,{type:'error',code:'room_not_ready'});
    if(typeof message.epoch!=='string'||message.epoch!==room.inputEpoch)return send(socket,{type:'error',code:'stale_input_epoch'});
    const decoded=decodeOnlineInput(message.input);
    if(!decoded)return send(socket,{type:'error',code:'invalid_input'});
    const player=room.players.find(player=>player.socket===socket);
    if(decoded.tick!==player.nextInputTick)return send(socket,{type:'error',code:'unexpected_tick'});
    player.nextInputTick++;
    const peer=room.players.find(other=>other.socket!==socket);
    send(peer.socket,{type:'input-test',epoch:room.inputEpoch,seat:player.seat,input:{tick:decoded.tick,held:message.input.held,actions:decoded.frame.actions}});
   }else if(message.type==='leave'){
    leave(socket);send(socket,{type:'left'});
   }else send(socket,{type:'error',code:'unknown_message'});
  });
  socket.on('close',()=>leave(socket));socket.on('error',()=>{});
 });
 return wss;
}
