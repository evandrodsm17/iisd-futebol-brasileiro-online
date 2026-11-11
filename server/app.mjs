import {createServer} from 'node:http';
import {realpath,stat} from 'node:fs/promises';
import {createReadStream} from 'node:fs';
import path from 'node:path';

const MIME={'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8','.mjs':'text/javascript; charset=utf-8',
 '.css':'text/css; charset=utf-8','.json':'application/json; charset=utf-8','.png':'image/png','.jpg':'image/jpeg',
 '.jpeg':'image/jpeg','.webp':'image/webp','.gif':'image/gif','.svg':'image/svg+xml','.ico':'image/x-icon',
 '.woff':'font/woff','.woff2':'font/woff2','.ttf':'font/ttf','.mp3':'audio/mpeg','.ogg':'audio/ogg',
 '.wav':'audio/wav','.wasm':'application/wasm','.webmanifest':'application/manifest+json'};

function reply(res,status,payload,head=false){
 const data=JSON.stringify(payload);
 res.writeHead(status,{'content-type':'application/json; charset=utf-8','cache-control':'no-store','content-length':Buffer.byteLength(data),'x-content-type-options':'nosniff'});
 res.end(head?undefined:data);
}

// The lobby does not yet provide online match simulation.
export async function createGameServer({root}){
 const base=await realpath(root);
 return createServer(async(req,res)=>{
  const head=req.method==='HEAD';
  if(req.method!=='GET'&&!head){res.setHeader('allow','GET, HEAD');return reply(res,405,{error:'method_not_allowed'});}
  let pathname;
  try{pathname=decodeURIComponent((req.url??'/').split('?')[0]);}catch{return reply(res,400,{error:'invalid_path'},head);}
  if(pathname==='/api/v1/status')return reply(res,200,{service:'nostalgia-soccer-hd',status:'ok',mode:'local',online_multiplayer:false,database:'not_configured'},head);
  if(pathname.startsWith('/api/'))return reply(res,404,{error:'not_found'},head);
  if(!pathname.startsWith('/')||pathname.includes('\\')||pathname.includes('\0')||pathname.split('/').some(part=>part==='..'||part.startsWith('.'))||pathname.includes(':'))return reply(res,403,{error:'forbidden'},head);
  if(pathname.endsWith('/'))pathname+='index.html';
  const extension=path.extname(pathname).toLowerCase();
  if(!MIME[extension])return reply(res,404,{error:'not_found'},head);
  const candidate=path.resolve(base,'.'+pathname);
  try{
   const target=await realpath(candidate),relative=path.relative(base,target);
   if(relative.startsWith('..'+path.sep)||relative==='..'||path.isAbsolute(relative))return reply(res,403,{error:'forbidden'},head);
   if(path.extname(target).toLowerCase()!==extension)return reply(res,403,{error:'forbidden'},head);
   const info=await stat(target);if(!info.isFile())return reply(res,404,{error:'not_found'},head);
   res.writeHead(200,{'content-type':MIME[extension],'content-length':info.size,'cache-control':'no-cache','x-content-type-options':'nosniff'});
   if(head)return res.end();
   const stream=createReadStream(target);stream.on('error',()=>res.destroy());stream.pipe(res);
  }catch(error){if(error.code==='ENOENT'||error.code==='ENOTDIR')return reply(res,404,{error:'not_found'},head);return reply(res,500,{error:'internal_error'},head);}
 });
}
