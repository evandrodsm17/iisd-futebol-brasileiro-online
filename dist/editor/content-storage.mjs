/* One IndexedDB transaction stores a versioned package and its local PNG Blobs. */
const DATABASE='campo-longo-editor',STORE='content',VERSION=1;
function openDatabase(){
  return new Promise((resolve,reject)=>{
    const request=indexedDB.open(DATABASE,VERSION);
    request.onupgradeneeded=()=>{const db=request.result;if(!db.objectStoreNames.contains(STORE))db.createObjectStore(STORE);};
    request.onsuccess=()=>resolve(request.result);
    request.onerror=()=>reject(request.error);
    request.onblocked=()=>reject(new Error('Feche outras abas para atualizar os dados locais.'));
  });
}
async function transaction(mode,callback){
  const db=await openDatabase();
  try{return await new Promise((resolve,reject)=>{
    const tx=db.transaction(STORE,mode),request=callback(tx.objectStore(STORE));
    request.onsuccess=()=>resolve(request.result??null);
    request.onerror=()=>reject(request.error);
    tx.onabort=()=>reject(tx.error??new Error('Operação local cancelada'));
    tx.onerror=()=>reject(tx.error??new Error('Falha ao gravar dados'));
  });}finally{db.close();}
}
export async function saveContent(content){
  await transaction('readwrite',store=>store.put(content,'active'));
}
export async function loadContent(){
  return transaction('readonly',store=>store.get('active'));
}
export async function clearContent(){
  await transaction('readwrite',store=>store.delete('active'));
}
