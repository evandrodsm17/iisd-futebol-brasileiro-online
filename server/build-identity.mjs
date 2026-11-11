import {createHash} from 'node:crypto';
import {readdir,readFile} from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

export const distRoot=fileURLToPath(new URL('../dist/',import.meta.url));
// Covers JavaScript modules and the committed base catalog, excluding tests and the generated identity.
export async function gameBuildIdentity(root=distRoot){
 const files=[];
 async function visit(dir,relative=''){
  for(const entry of await readdir(dir,{withFileTypes:true})){
   const rel=relative?`${relative}/${entry.name}`:entry.name;
   if(entry.isDirectory())await visit(path.join(dir,entry.name),rel);
   else if(entry.isFile() && (/\.m?js$/.test(entry.name)||rel==='data/issd-rom-catalog.json') && !entry.name.startsWith('test-') && rel!=='online-build.mjs')files.push(rel);
  }
 }
 await visit(root);files.sort();
 const hash=createHash('sha256');
 for(const file of files){const source=await readFile(path.join(root,...file.split('/')),'utf8');const bytes=Buffer.from(source.replace(/\r\n/g,'\n'));hash.update(file+'\0'+bytes.length+'\0');hash.update(bytes);}
 return hash.digest('hex');
}
