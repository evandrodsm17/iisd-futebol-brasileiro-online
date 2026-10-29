/* Small dependency-free ZIP writer/reader for local author-owned packages.
 * Only stored entries are emitted. Imports can read stored/deflate ZIP entries. */
const encode=new TextEncoder(),decode=new TextDecoder('utf-8',{fatal:true});
const limits={files:200,entry:12*1024*1024,total:80*1024*1024};
function checkName(name){
  if(name!=='content-package.json'&&!/^assets\/[a-z0-9][a-z0-9_.-]*\.png$/i.test(name)||name.includes('..'))throw new Error('Caminho ZIP proibido: '+name);
}
const table=Array.from({length:256},(_,i)=>{let v=i;for(let n=0;n<8;n++)v=(v&1)?0xedb88320^(v>>>1):v>>>1;return v>>>0;});
export function crc32(data){
  let crc=0xffffffff;for(const byte of data)crc=table[(crc^byte)&255]^(crc>>>8);return (crc^0xffffffff)>>>0;
}
function u16(view,pos,value){view.setUint16(pos,value,true);}
function u32(view,pos,value){view.setUint32(pos,value>>>0,true);}
function read16(view,pos){return view.getUint16(pos,true);}
function read32(view,pos){return view.getUint32(pos,true);}
export function writeContentZip(files){
  if(files.length>limits.files)throw new Error('Muitos arquivos no pacote');
  const chunks=[],central=[];
  let offset=0,total=0;
  const names=new Set();
  for(const file of files){
    checkName(file.name);
    if(names.has(file.name))throw new Error('Arquivo repetido no ZIP');
    names.add(file.name);
    const name=encode.encode(file.name),bytes=file.bytes;
    if(!(bytes instanceof Uint8Array))throw new Error('Arquivo ZIP inválido');
    total+=bytes.length;if(bytes.length>limits.entry||total>limits.total)throw new Error('Pacote ZIP muito grande');
    const crc=crc32(bytes);
    const h=new Uint8Array(30+name.length),v=new DataView(h.buffer);
    u32(v,0,0x04034b50);u16(v,4,20);u16(v,6,0x800);u16(v,8,0);u32(v,14,crc);
    u32(v,18,bytes.length);u32(v,22,bytes.length);u16(v,26,name.length);h.set(name,30);
    chunks.push(h,bytes);
    const c=new Uint8Array(46+name.length),w=new DataView(c.buffer);
    u32(w,0,0x02014b50);u16(w,4,20);u16(w,6,20);u16(w,8,0x800);u16(w,10,0);
    u32(w,16,crc);u32(w,20,bytes.length);u32(w,24,bytes.length);u16(w,28,name.length);u32(w,42,offset);c.set(name,46);
    central.push(c);offset+=h.length+bytes.length;
  }
  const centralSize=central.reduce((s,c)=>s+c.length,0);
  const end=new Uint8Array(22),e=new DataView(end.buffer);
  u32(e,0,0x06054b50);u16(e,8,files.length);u16(e,10,files.length);u32(e,12,centralSize);u32(e,16,offset);
  return new Blob([...chunks,...central,end],{type:'application/zip'});
}
async function inflate(data){
  if(typeof DecompressionStream!=='function')throw new Error('ZIP comprimido não suportado neste navegador.');
  return new Uint8Array(await new Response(new Blob([data]).stream().pipeThrough(new DecompressionStream('deflate-raw'))).arrayBuffer());
}
export async function readContentZip(blob){
  if(blob.size>limits.total+1024*1024)throw new Error('ZIP muito grande');
  const bytes=new Uint8Array(await blob.arrayBuffer()),v=new DataView(bytes.buffer),files=new Map();
  let end=-1;
  for(let p=bytes.length-22;p>=Math.max(0,bytes.length-65557);p--){if(read32(v,p)===0x06054b50){end=p;break;}}
  if(end<0)throw new Error('Fim de ZIP não encontrado');
  const entries=read16(v,end+10),size=read32(v,end+12),start=read32(v,end+16);
  if(entries>limits.files||start+size>bytes.length)throw new Error('Diretório ZIP inválido');
  let p=start,total=0;
  for(let i=0;i<entries;i++){
    if(p+46>bytes.length||read32(v,p)!==0x02014b50)throw new Error('Índice ZIP inválido');
    const flags=read16(v,p+8),method=read16(v,p+10),crc=read32(v,p+16),compressed=read32(v,p+20),raw=read32(v,p+24),
      nameSize=read16(v,p+28),extra=read16(v,p+30),comment=read16(v,p+32),local=read32(v,p+42);
    if(flags&1||!([0,8].includes(method))||raw>limits.entry||compressed>limits.entry)throw new Error('Entrada ZIP incompatível');
    if(p+46+nameSize+extra+comment>bytes.length)throw new Error('Nome ZIP truncado');
    const name=decode.decode(bytes.subarray(p+46,p+46+nameSize));checkName(name);
    if(files.has(name))throw new Error('Arquivo duplicado no ZIP');
    if(local+30>bytes.length||read32(v,local)!==0x04034b50)throw new Error('Arquivo ZIP sem cabeçalho');
    const offset=local+30+read16(v,local+26)+read16(v,local+28);
    if(offset+compressed>bytes.length)throw new Error('Dados ZIP truncados');
    const packed=bytes.subarray(offset,offset+compressed);
    const data=method===0?new Uint8Array(packed):await inflate(packed);
    if(data.length!==raw||crc32(data)!==crc)throw new Error('Falha de integridade ZIP: '+name);
    total+=data.length;if(total>limits.total)throw new Error('Pacote ZIP muito grande');
    files.set(name,data);
    p+=46+nameSize+extra+comment;
  }
  if(!files.has('content-package.json'))throw new Error('content-package.json ausente');
  return files;
}
