/** Author-owned HD sprites; purely a rendering adapter, independent of SNES data. */
export const HD_DIRECTIONS = Object.freeze(['up','up-right','right','down-right','down','down-left','left','up-left']);
export const HD_MOTIONS = Object.freeze(['idle','walking','running']);
function ensure(ok,message){if(!ok)throw new Error('Pacote HD inválido: '+message);}
function integer(v,min,max){return Number.isInteger(v)&&v>=min&&v<=max;}
function finite(v,min,max){return typeof v==='number'&&Number.isFinite(v)&&v>=min&&v<=max;}
function pngName(s){return typeof s==='string'&&/^[a-z0-9][a-z0-9_. -]*\.png$/i.test(s)&&!s.includes('..');}

export function validateHDManifest(input){
  ensure(input&&typeof input==='object'&&!Array.isArray(input),'objeto JSON esperado');
  ensure(input.schema_version===1,'schema_version deve ser 1');
  ensure(typeof input.id==='string'&&/^[a-z0-9][a-z0-9-]{1,63}$/.test(input.id),'id inválido');
  const options=input.render??{};
  ensure(options&&typeof options==='object'&&!Array.isArray(options),'render inválido');
  const render={
    world_height:options.world_height??38,anchor_x:options.anchor_x??0.5,
    anchor_y:options.anchor_y??1,offset_x:options.offset_x??0,offset_y:options.offset_y??0
  };
  ensure(finite(render.world_height,4,256),'render.world_height fora de 4..256');
  ensure(finite(render.anchor_x,0,1)&&finite(render.anchor_y,0,1),'âncoras fora de 0..1');
  ensure(finite(render.offset_x,-256,256)&&finite(render.offset_y,-256,256),'offsets fora de -256..256');
  ensure(input.animations&&typeof input.animations==='object'&&!Array.isArray(input.animations),'animations inválido');
  const keys=Object.keys(input.animations);
  ensure(keys.length>0&&keys.every(k=>HD_MOTIONS.includes(k)),'animations precisa conter idle, walking e/ou running');
  const animations={};
  for(const motion of keys){
    const a=input.animations[motion];
    ensure(a&&typeof a==='object'&&!Array.isArray(a),motion+': objeto esperado');
    ensure(pngName(a.file),motion+': PNG deve ter nome simples, sem diretórios');
    ensure(integer(a.frames,1,60),motion+': frames fora de 1..60');
    ensure(integer(a.frame_width,1,2048)&&integer(a.frame_height,1,2048),motion+': tamanho de quadro inválido');
    const rows=a.direction_rows??[0,1,2,3,4,5,6,7];
    ensure(Array.isArray(rows)&&rows.length===8&&rows.every(v=>integer(v,0,7))&&new Set(rows).size===8,motion+': direction_rows deve conter 0..7 sem repetição');
    const durations=Array.isArray(a.ticks_per_frame)?[...a.ticks_per_frame]:Array(a.frames).fill(a.ticks_per_frame??3);
    ensure(durations.length===a.frames&&durations.every(v=>integer(v,1,120)),motion+': ticks_per_frame inválido');
    animations[motion]={file:a.file,frames:a.frames,frame_width:a.frame_width,
      frame_height:a.frame_height,direction_rows:[...rows],ticks_per_frame:durations};
  }
  return {schema_version:1,id:input.id,render,animations};
}

export function resolveHDFrame(pack,motion,direction,tick){
  if(!pack||!HD_MOTIONS.includes(motion)||!integer(direction,0,7)||!Number.isFinite(tick))return null;
  const animation=pack.manifest?.animations?.[motion];
  const image=animation&&pack.images?.[animation.file];
  if(!image)return null;
  const total=animation.ticks_per_frame.reduce((s,n)=>s+n,0);
  let t=((Math.floor(tick)%total)+total)%total,index=0;
  while(t>=animation.ticks_per_frame[index])t-=animation.ticks_per_frame[index++];
  return {image,sx:index*animation.frame_width,
    sy:animation.direction_rows[direction]*animation.frame_height,
    sw:animation.frame_width,sh:animation.frame_height,
    render:pack.manifest.render,frame:index};
}
function openImage(file,url){
  return new Promise((resolve,reject)=>{
    const img=new Image();
    img.onload=()=>resolve(img);
    img.onerror=()=>reject(new Error('Falha ao abrir '+file.name));
    img.src=url;
  });
}
export async function importHDManifest(data,files){
  const manifest=validateHDManifest(data),supplied=new Map();
  for(const file of Array.from(files??[])){
    ensure(file&&pngName(file.name),'selecione somente PNGs com nomes simples');
    ensure(!supplied.has(file.name),'PNG duplicado: '+file.name);
    ensure(file.size<=20*1024*1024,'PNG maior que 20 MB: '+file.name);
    supplied.set(file.name,file);
  }
  const names=new Set(Object.values(manifest.animations).map(a=>a.file));
  const images={},urls=[];
  try{
    for(const name of names){
      const file=supplied.get(name);
      ensure(file,'PNG não encontrado: '+name);
      const url=URL.createObjectURL(file);
      urls.push(url);
      const img=await openImage(file,url);
      for(const a of Object.values(manifest.animations).filter(a=>a.file===name)){
        ensure(img.naturalWidth===a.frames*a.frame_width&&img.naturalHeight===8*a.frame_height,
          name+' precisa ter '+a.frames*a.frame_width+'×'+8*a.frame_height+' pixels');
      }
      images[name]=img;
    }
    return {manifest,images,dispose(){urls.splice(0).forEach(url=>URL.revokeObjectURL(url));}};
  }catch(error){urls.forEach(url=>URL.revokeObjectURL(url));throw error;}
}
