import {networkInterfaces} from 'node:os';
import {spawnSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';

const port=Number(process.env.PORT??4173);
if(!Number.isInteger(port)||port<1||port>65535){
 console.error('Porta inválida. Defina PORT entre 1 e 65535.');
 process.exit(1);
}

// A fresh checkout can be started with the same command as an existing one.
try { await import('ws'); }
catch(error){
 if(error.code!=='ERR_MODULE_NOT_FOUND')throw error;
 console.log('Preparando as dependências do jogo...');
 const npm=process.platform==='win32'?'npm.cmd':'npm';
 const install=spawnSync(npm,['ci'],{cwd:fileURLToPath(new URL('../',import.meta.url)),stdio:'inherit',shell:process.platform==='win32'});
 if(install.error||install.status!==0){
  console.error('Não foi possível instalar as dependências. Verifique sua conexão e a instalação do Node.js.');
  process.exit(1);
 }
}

// Both players must receive the identity for the current local game files.
await import('./generate-identity.mjs');
const {createGameServer}=await import('./app.mjs');
const {attachLobby}=await import('./lobby.mjs');
const server=await createGameServer({root:fileURLToPath(new URL('../dist/',import.meta.url))});
const lobby=await attachLobby(server);
// The WebSocket server forwards HTTP listen errors; the HTTP listener below
// reports them once with an actionable message.
lobby.on('error',()=>{});
server.on('error',error=>{
 if(error.code==='EADDRINUSE')console.error(`A porta ${port} já está em uso. Feche o servidor que a utiliza ou defina outra porta em PORT.`);
 else console.error('Não foi possível iniciar o servidor:',error.message);
 process.exitCode=1;
});
server.listen(port,'0.0.0.0',()=>{
 console.log('\nNostalgia Soccer HD — multiplayer em rede local');
 console.log(`Neste computador: http://127.0.0.1:${port}/`);
 let count=0;
 for(const [name,entries] of Object.entries(networkInterfaces()))for(const entry of entries??[]){
  if(entry.family!=='IPv4'||entry.internal)continue;
  console.log(`Na rede (${name}): http://${entry.address}:${port}/`);count++;
 }
 if(!count)console.log('Nenhum endereço IPv4 de rede encontrado. Verifique a conexão Wi-Fi ou Ethernet.');
 console.log('Abra o mesmo endereço de rede nos dois computadores e escolha MULTIPLAYER ONLINE.');
 console.log('Mantenha esta janela aberta. Para encerrar, pressione Ctrl+C.\n');
});
for(const signal of ['SIGINT','SIGTERM'])process.on(signal,()=>{
 for(const socket of lobby.clients)socket.terminate();
 lobby.close();server.close();
});
