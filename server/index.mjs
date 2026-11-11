import {fileURLToPath} from 'node:url';
import {createGameServer} from './app.mjs';
import {attachLobby} from './lobby.mjs';

const port=Number(process.env.PORT??4173),host=process.env.HOST??'127.0.0.1';
if(!Number.isInteger(port)||port<1||port>65535)throw new RangeError('PORT deve estar entre 1 e 65535');
const server=await createGameServer({root:fileURLToPath(new URL('../dist/',import.meta.url))});
await attachLobby(server);
server.on('error',error=>{console.error('Não foi possível iniciar o servidor:',error.message);process.exitCode=1;});
server.listen(port,host,()=>console.log(`Nostalgia Soccer HD: http://${host}:${port}/`));
for(const signal of ['SIGINT','SIGTERM'])process.on(signal,()=>server.close());
