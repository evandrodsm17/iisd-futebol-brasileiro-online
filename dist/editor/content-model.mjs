/* Author-owned content schema. Independent from the reference ROM and its catalog. */
const ID=/^[a-z0-9][a-z0-9-]{1,63}$/;
const HEX=/^#[0-9a-fA-F]{6}$/;
const POSITIONS=new Set(['GK','DF','MF','FW']);
const KINDS=new Set(['home','away','third','goalkeeper']);
export function contentId(value){
  const slug=String(value??'').normalize('NFD').replace(/[\u0300-\u036f]/g,'')
    .toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/^-+|-+$/g,'').slice(0,64);
  return slug.length>=2?slug:'clube';
}
function assert(ok,message){if(!ok)throw new Error('Conteúdo inválido: '+message);}
function simpleText(value,max=90){return typeof value==='string'&&value.trim().length>0&&value.length<=max;}
function unique(list,label){
  assert(Array.isArray(list),label+' deve ser uma lista');
  const ids=new Set();
  for(const item of list){assert(item&&typeof item==='object'&&ID.test(item.id),label+' contém ID inválido');assert(!ids.has(item.id),label+' contém ID duplicado: '+item.id);ids.add(item.id);}
  return ids;
}
export function assetPath(path){
  return typeof path==='string'&&/^assets\/[a-z0-9][a-z0-9_.-]*\.png$/i.test(path)&&!path.includes('..');
}
export function createEmptyPackage(){
  return {schema_version:1,package_id:'clubes-autorais',revision:1,
    metadata:{name:'Meu futebol',author:'Criador local',license:'Conteúdo autoral'},
    assets:[],clubs:[],players:[],stadiums:[],competitions:[]};
}
export function defaultKits(){
  return [
    {id:'home',kind:'home',colours:{shirt:'#147D86',shorts:'#FFFFFF',socks:'#147D86'},pattern:'solid'},
    {id:'away',kind:'away',colours:{shirt:'#FFFFFF',shorts:'#147D86',socks:'#FFFFFF'},pattern:'solid'}
  ];
}
export function validateContentPackage(value){
  assert(value&&typeof value==='object'&&!Array.isArray(value),'pacote JSON esperado');
  assert(value.schema_version===1,'schema_version deve ser 1');
  assert(typeof value.package_id==='string'&&ID.test(value.package_id),'package_id inválido');
  assert(Number.isInteger(value.revision)&&value.revision>=1,'revision inválida');
  assert(value.metadata&&['name','author','license'].every(k=>simpleText(value.metadata[k],180)),'metadata requer nome, autor e licença');
  assert(Array.isArray(value.assets)&&value.assets.every(assetPath),'assets exige caminhos PNG relativos');
  assert(new Set(value.assets).size===value.assets.length,'asset duplicado');
  const clubs=unique(value.clubs,'clubs'),stadiums=unique(value.stadiums,'stadiums');
  unique(value.players,'players');unique(value.competitions,'competitions');
  const media=new Set(value.assets);
  for(const club of value.clubs){
    assert(simpleText(club.name)&&simpleText(club.city??'Não informada')&&simpleText(club.country??'Brasil'),'clube exige nome e localização');
    if(club.crest!=null)assert(media.has(club.crest),'escudo não listado em assets: '+club.id);
    if(club.stadium_id!=null)assert(stadiums.has(club.stadium_id),'estádio do clube inexistente: '+club.id);
    assert(Array.isArray(club.kits)&&club.kits.length>=2,'clube precisa de uniformes');
    const kitIds=new Set(),kinds=new Set();
    for(const kit of club.kits){
      assert(kit&&ID.test(kit.id)&&KINDS.has(kit.kind),'uniforme inválido: '+club.id);
      assert(!kitIds.has(kit.id)&&!kinds.has(kit.kind),'uniforme duplicado: '+club.id);
      kitIds.add(kit.id);kinds.add(kit.kind);
      assert(kit.colours&&Object.values(kit.colours).length>=3,'uniforme precisa de três cores');
      for(const item of ['shirt','shorts','socks'])assert(HEX.test(kit.colours[item]),'cor '+item+' inválida em '+club.id);
      if(kit.pattern!=null)assert(['solid','stripes','hoops','sash'].includes(kit.pattern),'padrão inválido');
    }
    assert(kinds.has('home')&&kinds.has('away'),'clube precisa de titular e reserva');
  }
  for(const stadium of value.stadiums){
    assert(simpleText(stadium.name),'nome de estádio inválido');
    assert(Number.isInteger(stadium.layout_id)&&stadium.layout_id>=0&&stadium.layout_id<=7,'layout de estádio deve ser 0..7');
    if(stadium.image!=null)assert(media.has(stadium.image),'imagem de estádio não listada em assets');
  }
  for(const player of value.players){
    assert(simpleText(player.name),'nome de jogador inválido');
    assert(player.club_id==null||clubs.has(player.club_id),'jogador aponta para clube inexistente');
    assert(POSITIONS.has(player.position),'posição de jogador inválida');
    assert(Number.isInteger(player.shirt_number)&&player.shirt_number>=1&&player.shirt_number<=99,'camisa deve ser 1..99');
    if(player.overall!=null)assert(Number.isInteger(player.overall)&&player.overall>=1&&player.overall<=99,'overall deve ser 1..99');
  }
  return value;
}
function uniformToGame(kit){
  const {shirt,shorts,socks}=kit.colours;
  return {shirt:[shirt,shirt,shirt],shorts:[shorts,shorts,shorts],socks:[socks,socks,socks]};
}
export function customCatalogTeams(pack){
  validateContentPackage(pack);
  return pack.clubs.map(club=>{
    const members=pack.players.filter(p=>p.club_id===club.id);
    const first=members.slice(0,11).map(p=>({name:p.name,position:p.position,shirt_number:p.shirt_number,id:p.id}));
    while(first.length<11){const n=first.length+1;first.push({name:'Atleta '+n,position:n===1?'GK':n<6?'DF':n<9?'MF':'FW',shirt_number:n});}
    return {
      id:'custom:'+club.id,name:club.name,custom:true,crest:club.crest??null,
      stadium_id:club.stadium_id??null,players:first,
      kit:Object.fromEntries(club.kits.map(k=>[k.kind,uniformToGame(k)])),
      formation:{label:'4-4-2',outfield_slots:[]}
    };
  });
}
export function customStadiums(pack,layouts,assetUrl){
  validateContentPackage(pack);
  return pack.stadiums.map(stadium=>{
    const layout=layouts.find(item=>item.id===stadium.layout_id);
    if(!layout)throw new Error('Layout-base de estádio indisponível');
    return {...layout,id:'custom:'+stadium.id,layout_id:layout.id,name:stadium.name,
      asset:stadium.image&&assetUrl(stadium.image)||layout.asset};
  });
}


/** Pure, validated edits preserve the previous package when a form is invalid. */
export function replaceContentRecord(packageData,collection,id,record) {
  assert(['clubs','players','stadiums'].includes(collection),'coleção não editável');
  assert(record?.id===id,'não é possível modificar o ID permanente');
  const copy=structuredClone(packageData),index=copy[collection].findIndex(item=>item.id===id);
  assert(index>=0,'registro não encontrado: '+id);
  copy[collection][index]=structuredClone(record);
  return validateContentPackage(copy);
}
export function addOptionalClubKit(packageData,clubId,kind) {
  assert(kind==='third'||kind==='goalkeeper','uniforme adicional inválido');
  const copy=structuredClone(packageData),club=copy.clubs.find(c=>c.id===clubId);
  assert(club,'clube não encontrado: '+clubId);
  assert(!club.kits.some(kit=>kit.kind===kind),'uniforme já cadastrado');
  club.kits.push({id:kind,kind,colours:{shirt:'#333333',shorts:'#333333',socks:'#333333'},pattern:'solid'});
  return validateContentPackage(copy);
}
