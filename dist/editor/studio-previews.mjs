/** Original, DOM-independent SVG previews for the Campo Longo authoring studio. */
const esc=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const hex=value=>/^#[0-9a-f]{6}$/i.test(value)?value:'#6fa6a6';
export function kitPreviewSVG(kit){
 const c=kit?.colours??{},shirt=hex(c.shirt),shorts=hex(c.shorts),socks=hex(c.socks);
 const pattern=['solid','stripes','hoops','sash'].includes(kit?.pattern)?kit.pattern:'solid';
 const accent='#ffffff44',base='kit-'+esc(kit?.kind??'generic');
 let motif='';
 if(pattern==='stripes')motif=Array.from({length:9},(_,i)=>'<rect x="'+(54+i*12)+'" y="25" width="5" height="97" fill="'+accent+'"/>').join('');
 if(pattern==='hoops')motif=Array.from({length:6},(_,i)=>'<rect x="43" y="'+(31+i*17)+'" width="135" height="8" fill="'+accent+'"/>').join('');
 if(pattern==='sash')motif='<path d="M44 25h24l101 97h-23z" fill="'+accent+'"/>';
 return '<svg class="kit-art" viewBox="0 0 220 260" role="img" aria-label="Prévia do uniforme '+esc(kit?.kind??'')+'">'+
 '<defs><clipPath id="'+base+'"><path d="M78 22L50 36 20 70 44 93 64 71 65 138H155L156 71 176 93 200 70 170 36 141 22Q126 48 110 48T78 22Z"/></clipPath></defs>'+
 '<path d="M78 22L50 36 20 70 44 93 64 71 65 138H155L156 71 176 93 200 70 170 36 141 22Q126 48 110 48T78 22Z" fill="'+shirt+'" stroke="#ffffff55" stroke-width="2"/>'+
 '<g clip-path="url(#'+base+')">'+motif+'</g>'+
 '<path d="M81 22Q110 57 139 22" fill="none" stroke="#e5eef4" stroke-width="6"/>'+
 '<path d="M65 140H155L149 192 113 191 110 170 107 191 70 192Z" fill="'+shorts+'" stroke="#ffffff55" stroke-width="2"/>'+
 '<path d="M72 194h30l-4 51H70zM120 194h30l6 51h-32z" fill="'+socks+'" stroke="#ffffff55" stroke-width="2"/>'+
 '<path d="M69 242h30l4 8H64zM125 242h31l6 8h-39z" fill="#27333a"/>'+
 '</svg>';
}
const fieldRect='<rect width="460" height="240" rx="13" fill="#215b46"/><g fill="#ffffff0b">'+Array.from({length:10},(_,i)=>'<rect x="'+(i*46)+'" width="46" height="240" fill="'+(i%2?'#00000010':'#ffffff08')+'"/>').join('')+'</g><g fill="none" stroke="#e7f2e080" stroke-width="2"><rect x="15" y="14" width="430" height="212"/><path d="M230 14v212"/><circle cx="230" cy="120" r="33"/><rect x="15" y="66" width="72" height="108"/><rect x="373" y="66" width="72" height="108"/><rect x="15" y="94" width="28" height="52"/><rect x="417" y="94" width="28" height="52"/></g>';
export function rosterPreviewSVG(players=[]){
 const positions=[[29,120],[130,32],[130,90],[130,150],[130,208],[230,32],[230,90],[230,150],[230,208],[335,83],[335,157]];
 const markers=positions.map(([x,y],i)=>{
  const player=players[i]??{},name=esc(player.name||'Vaga '+(i+1));
  const shirt=Number(player.shirt_number)||i+1;
  return '<g class="roster-marker" data-player-id="'+esc(player.id??'')+'" transform="translate('+x+' '+y+')" role="img" aria-label="'+name+'"><circle r="17" fill="#0a2c34" stroke="#e3dd99" stroke-width="2"/><text y="5.5" font-size="14" text-anchor="middle" font-weight="700" fill="#f7f9ec">'+esc(shirt)+'</text><title>'+name+'</title></g>';
 }).join('');
 return '<svg viewBox="0 0 460 240" class="pitch-art" role="img" aria-label="Escalação inicial com onze jogadores">'+fieldRect+markers+'</svg>';
}
export function stadiumPreviewSVG(stadium={}){
 return '<svg viewBox="0 0 460 240" class="pitch-art" role="img" aria-label="Representação do gramado de '+esc(stadium.name||'estádio')+'">'+
 '<rect width="460" height="240" rx="13" fill="#18343d"/><path d="M4 45Q230 -3 456 45M4 195Q230 243 456 195" stroke="#69918a" stroke-width="15" fill="none"/>'+
 '<g transform="translate(28 31) scale(.88 .74)">'+fieldRect+'</g>'+
 '<text x="230" y="230" text-anchor="middle" font-size="12" fill="#d2e9e1">'+esc(stadium.name||'Estádio')+'</text></svg>';
}
