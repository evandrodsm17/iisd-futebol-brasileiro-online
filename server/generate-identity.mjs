import {writeFile} from 'node:fs/promises';
import {gameBuildIdentity,distRoot} from './build-identity.mjs';
import path from 'node:path';
const identity=await gameBuildIdentity();
await writeFile(path.join(distRoot,'online-build.mjs'),`// Gerado por npm run build:identity. Não editar manualmente.\nexport const ONLINE_BUILD = '${identity}';\n`);
console.log(`Identidade online: ${identity}`);
