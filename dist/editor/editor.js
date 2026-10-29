import {createEmptyPackage,defaultKits,validateContentPackage,contentId} from './content-model.mjs';
import {loadContent,saveContent} from './content-storage.mjs';
import {writeContentZip,readContentZip} from './content-zip.mjs';
import {kitPreviewSVG,rosterPreviewSVG,stadiumPreviewSVG} from './studio-previews.mjs';
import {createEditorHistory} from './studio-history.mjs';
const $=id=>document.getElementById(id);
let state={package:createEmptyPackage(),images:{}},selection={kind:'clubs',id:null};
const history=createEditorHistory();
function checkpoint(){history.capture(state);updateHistory();}
function updateHistory(){$('undo').disabled=!history.canUndo;$('redo').disabled=!history.canRedo;}
async function restore(snapshot){state=snapshot;selection.id=state.package[selection.kind].find(x=>x.id===selection.id)?.id??state.package[selection.kind][0]?.id??null;await persist();render();updateHistory();}
$('undo').onclick=()=>{const s=history.undo(state);if(s)restore(s);};
$('redo').onclick=()=>{const s=history.redo(state);if(s)restore(s);};
const kinds={clubs:'Clubes',players:'Jogadores',stadiums:'Estádios'};
const fields={
 clubs:[['name','Nome'],['city','Cidade'],['country','País'],['nickname','Apelido']],
 players:[['name','Nome'],['position','Posição (GK, DF, MF, FW)'],['shirt_number','Número'],['overall','Força (1-99)'],['club_id','ID do clube']],
 stadiums:[['name','Nome'],['layout_id','Layout-base (0-7)']]
};
const text=v=>String(v??'');
function msg(value,error=false){$('status').textContent=value;$('status').dataset.error=error?'true':'false';}
function escapeHTML(value){return text(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
function distinctId(prefix,label){let id=contentId(label);if(state.package[prefix].some(x=>x.id===id)){let i=2;while(state.package[prefix].some(x=>x.id===id+'-'+i))i++;id+='-'+i;}return id;}
function active(){return state.package[selection.kind].find(x=>x.id===selection.id);}
function options(list,value){return list.map(x=>'<option value="'+escapeHTML(x.id)+'" '+(x.id===value?'selected':'')+'>'+escapeHTML(x.name)+'</option>').join('');}
function drawList(){
 $('nav').replaceChildren();
 for(const kind of Object.keys(kinds)){
  const button=document.createElement('button');button.type='button';button.className=kind===selection.kind?'active':'';
  button.textContent=kinds[kind]+' ('+state.package[kind].length+')';
  button.onclick=()=>{selection={kind,id:state.package[kind][0]?.id??null};render();};$('nav').append(button);
 }
 $('items').replaceChildren();
 for(const entry of state.package[selection.kind]){
  const button=document.createElement('button');button.type='button';
  button.className=entry.id===selection.id?'selected':'';
  button.textContent=entry.name+'  ·  '+entry.id;
  button.onclick=()=>{selection.id=entry.id;render();};$('items').append(button);
 }
}
function kitRow(kit,index){
 return '<fieldset class="kit" data-kit="'+index+'"><legend>'+escapeHTML(kit.kind.toUpperCase())+'</legend>'+
 ['shirt','shorts','socks'].map(k=>'<label>'+({shirt:'Camisa',shorts:'Calção',socks:'Meias'}[k])+
 '<input data-kit-color="'+k+'" type="color" value="'+escapeHTML(kit.colours[k])+'"></label>').join('')+
 '<label>Estilo<select data-kit-pattern>'+['solid','stripes','hoops','sash'].map(p=>'<option value="'+p+'" '+(kit.pattern===p?'selected':'')+'>'+p+'</option>').join('')+'</select></label></fieldset>';
}
function drawStudioPreview(){
 const entry=active(),slot=$('visual-preview');slot.replaceChildren();
 $('editor-section').textContent=(kinds[selection.kind]||'Editor').toUpperCase();
 $('preview-title').textContent=selection.kind==='clubs'?'Identidade e uniformes':selection.kind==='players'?'Campo e escalação':'Prévia do estádio';
 if(!entry){$('preview-caption').textContent='Crie um registro para visualizar.';return;}
 if(selection.kind==='clubs'){
  const crest=entry.crest&&state.images[entry.crest];
  if(crest){const img=document.createElement('img');img.className='preview-crest';img.alt='Escudo do clube';const url=URL.createObjectURL(crest);img.src=url;img.onload=()=>URL.revokeObjectURL(url);slot.append(img);}
  for(const kit of entry.kits){const card=document.createElement('div');card.className='kit-preview-card';const title=document.createElement('strong');title.textContent=kit.kind.toUpperCase();card.append(title);const view=document.createElement('div');view.innerHTML=kitPreviewSVG(kit);card.append(view);slot.append(card);}
  const associated=state.package.players.filter(p=>p.club_id===entry.id);
  if(associated.length){const stage=document.createElement('div');stage.innerHTML=rosterPreviewSVG(associated);slot.append(stage);}
  $('preview-caption').textContent='Prévia vetorial original dos uniformes e escalação, sem modificar os sprites HD.';
 }else if(selection.kind==='players'){
  const club=state.package.clubs.find(c=>c.id===entry.club_id),associated=state.package.players.filter(p=>p.club_id===entry.club_id);
  const stage=document.createElement('div');stage.innerHTML=rosterPreviewSVG(associated);slot.append(stage);
  const name=document.createElement('p');name.textContent=(club?.name||'Sem equipe')+' · '+entry.name+' · '+entry.position;slot.append(name);
  $('preview-caption').textContent='Visualização ilustrativa: a formação tática editável será uma etapa separada.';
 }else{
  const stage=document.createElement('div');stage.innerHTML=stadiumPreviewSVG(entry);slot.append(stage);
  $('preview-caption').textContent='Prévia conceitual. O campo real usa um dos oito layouts-base do jogo.';
 }
}
function drawForm(){
 const entry=active();$('editor').replaceChildren();$('editor-title').textContent=entry?entry.name:'Selecione ou crie um registro';
 if(!entry)return;
 const form=document.createElement('form');form.id='record';
 form.innerHTML='<p class="small">ID permanente: <code>'+escapeHTML(entry.id)+'</code></p>'+
 fields[selection.kind].map(([key,label])=>{
  let value=entry[key]??'';
  if(key==='club_id')return '<label>'+label+'<select name="club_id"><option value="">Sem clube</option>'+options(state.package.clubs,value)+'</select></label>';
  const type=key==='overall'||key==='shirt_number'||key==='layout_id'?'number':'text';
  return '<label>'+label+'<input type="'+type+'" name="'+key+'" value="'+escapeHTML(value)+'" '+(key==='name'?'required':'')+'></label>';
 }).join('')+
 (selection.kind==='clubs'?'<label>Estádio do clube<select name="stadium_id"><option value="">Nenhum</option>'+options(state.package.stadiums,entry.stadium_id)+'</select></label>'+
 '<label>Escudo PNG <input id="crest-upload" type="file" accept=".png,image/png"></label><div class="preview" id="crest-preview"></div>'+
 '<div class="kit-grid">'+entry.kits.map(kitRow).join('')+'</div>'+
 '<button type="button" id="add-third">Adicionar terceiro uniforme</button><button type="button" id="add-goalie">Adicionar uniforme de goleiro</button>':'')+
 (selection.kind==='stadiums'?'<label>Imagem do estádio PNG <input id="stadium-upload" type="file" accept=".png,image/png"></label><div class="preview" id="stadium-preview"></div>':'')+
 '<div class="actions"><button class="primary" type="submit">Salvar alterações</button><button class="danger" type="button" id="delete">Excluir</button></div>';
 $('editor').append(form);
 if(selection.kind==='clubs'){
  preview('crest-preview',entry.crest);
  $('crest-upload').onchange=e=>upload(e,entry,'crest');
  for(const type of ['third','goalkeeper']){
   const button=$('add-'+(type==='third'?'third':'goalie'));
   button.disabled=entry.kits.some(k=>k.kind===type);
   button.onclick=()=>{checkpoint();entry.kits.push({id:type,kind:type,colours:{shirt:'#333333',shorts:'#333333',socks:'#333333'},pattern:'solid'});render();};
  }
 }
 if(selection.kind==='stadiums'){preview('stadium-preview',entry.image);$('stadium-upload').onchange=e=>upload(e,entry,'image');}
 $('delete').onclick=()=>{
  if(!confirm('Excluir '+entry.name+'?'))return;
  checkpoint();
  if(selection.kind==='clubs')state.package.players.forEach(p=>{if(p.club_id===entry.id)p.club_id=null;});
  if(selection.kind==='stadiums')state.package.clubs.forEach(c=>{if(c.stadium_id===entry.id)c.stadium_id=null;});
  state.package[selection.kind]=state.package[selection.kind].filter(x=>x.id!==entry.id);
  selection.id=state.package[selection.kind][0]?.id??null;render();persist();
 };
 form.onsubmit=event=>{
  event.preventDefault();
  const data=new FormData(form),copy=structuredClone(entry);
  for(const [key] of fields[selection.kind]){
   const value=text(data.get(key)).trim();
   copy[key]=['shirt_number','overall','layout_id'].includes(key)?Number(value):value;
  }
  if(selection.kind==='players')copy.club_id=copy.club_id||null;
  if(selection.kind==='clubs'){
   copy.stadium_id=text(data.get('stadium_id'))||null;
   for(const node of form.querySelectorAll('[data-kit]')){
    const kit=copy.kits[Number(node.dataset.kit)];
    for(const input of node.querySelectorAll('[data-kit-color]'))kit.colours[input.dataset.kitColor]=input.value.toUpperCase();
    kit.pattern=node.querySelector('[data-kit-pattern]').value;
   }
  }
  checkpoint();
  const idx=state.package[selection.kind].findIndex(x=>x.id===entry.id);
  state.package[selection.kind][idx]=copy;
  persist().then(ok=>{if(ok)render();});
 };
}
function preview(id,path){
 const node=$(id);if(!path)return;
 const asset=state.images[path];if(!asset)return;
 const img=document.createElement('img');img.alt='Prévia do arquivo';img.src=URL.createObjectURL(asset);
 img.onload=()=>URL.revokeObjectURL(img.src);node.append(img);
}
async function upload(event,entry,field){
 const file=event.target.files?.[0];if(!file)return;
 if(file.size>8*1024*1024||file.type!=='image/png'){msg('Escolha PNG com no máximo 8 MB.',true);return;}
 const header=new Uint8Array(await file.slice(0,8).arrayBuffer());
 if(header.join(',')!=='137,80,78,71,13,10,26,10'){msg('O arquivo não é um PNG válido.',true);return;}
 checkpoint();
 const path='assets/'+selection.kind+'-'+entry.id+'-'+field+'.png';
 state.images[path]=file;entry[field]=path;
 if(!state.package.assets.includes(path))state.package.assets.push(path);
 await persist();render();
}
async function persist(){
 try{
  validateContentPackage(state.package);
  for(const asset of state.package.assets)if(!(state.images[asset] instanceof Blob))throw Error('Imagem ausente: '+asset);
  state.package.revision++;
  await saveContent(state);msg('Alterações salvas neste navegador.');return true;
 }catch(error){msg(error.message,true);return false;}
}
function render(){drawList();drawForm();drawStudioPreview();updateHistory();}
$('create').onclick=()=>{
 const kind=selection.kind;
 const name=kind==='clubs'?'Novo Clube':kind==='players'?'Novo Atleta':'Novo Estádio';
 const id=distinctId(kind,name),entry={id,name};
 if(kind==='clubs')Object.assign(entry,{city:'Salvador',country:'Brasil',kits:defaultKits(),stadium_id:null,crest:null});
 if(kind==='players')Object.assign(entry,{position:'MF',shirt_number:10,overall:65,club_id:state.package.clubs[0]?.id??null});
 if(kind==='stadiums')Object.assign(entry,{layout_id:1,image:null});
 checkpoint();state.package[kind].push(entry);selection.id=id;render();persist();
};
$('export').onclick=async()=>{
 try{
  validateContentPackage(state.package);
  const files=[{name:'content-package.json',bytes:new TextEncoder().encode(JSON.stringify(state.package,null,2))}];
  for(const path of state.package.assets){
   const blob=state.images[path];if(!blob)throw Error('PNG ausente: '+path);
   files.push({name:path,bytes:new Uint8Array(await blob.arrayBuffer())});
  }
  const blob=writeContentZip(files),url=URL.createObjectURL(blob),a=document.createElement('a');
  a.href=url;a.download=state.package.package_id+'.zip';a.click();setTimeout(()=>URL.revokeObjectURL(url),3000);
  msg('Pacote ZIP exportado.');
 }catch(error){msg(error.message,true);}
};
$('import').onchange=async event=>{
 const file=event.target.files?.[0];if(!file)return;
 try{
  const files=await readContentZip(file),input=JSON.parse(new TextDecoder().decode(files.get('content-package.json')));
  validateContentPackage(input);
  const images={};
  for(const asset of input.assets){
   const bytes=files.get(asset);if(!bytes)throw Error('PNG ausente no ZIP: '+asset);
   images[asset]=new Blob([bytes],{type:'image/png'});
  }
  const incoming={package:input,images};await saveContent(incoming);checkpoint();state=incoming;selection={kind:'clubs',id:input.clubs[0]?.id??null};
  render();msg('Pacote ZIP importado e salvo.');
 }catch(error){msg(error.message,true);}
};
(async()=>{try{const data=await loadContent();if(data?.package){validateContentPackage(data.package);state=data;}selection.id=state.package.clubs[0]?.id??null;render();msg('Editor pronto. Dados salvos localmente.');}catch(e){render();msg('Armazenamento local indisponível: '+e.message,true);}})();
