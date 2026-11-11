# Base do servidor e salas online

O servidor Node em `server/` entrega o conteúdo de `dist/` e expõe `GET` e
`HEAD /api/v1/status`. O status informa `online_multiplayer: false` porque
partidas online ainda não são jogáveis; não há banco configurado. O motor da
partida continua no navegador e o editor local usa IndexedDB.

## Executar

Com Node.js 20 ou mais recente, execute `npm install` e `npm start`. O endereço
padrão é `http://127.0.0.1:4173/`. `PORT` escolhe outra porta e `HOST` altera
a interface de escuta. O padrão restringe o acesso ao próprio computador.
Execute `npm run test:server` para testar arquivos estáticos e ciclo de salas.

## Protocolo experimental de salas

Conecte por WebSocket a `/api/v1/lobby`. O servidor envia
`{"type":"connected","protocol":1,"teams":[...]}` com os IDs e nomes do catálogo original do servidor. As mensagens são JSON:

- `{"type":"create"}` cria uma sala temporária com código aleatório.
- `{"type":"join","code":"XXXXXXXX"}` entra pelo código hexadecimal.
- `{"type":"leave"}` sai da sala; a confirmação é `{"type":"left"}`.
- `{"type":"selection","team":0,"kit":0}` escolhe uma equipe pelo ID
  anunciado pelo servidor e uniforme `0` ou `1`. Cada participante altera
  apenas sua própria escolha; mudar qualquer escolha cancela as confirmações.
- `{"type":"ready","ready":true}` confirma preparação; `false` cancela.
  Apenas participantes da sala podem alterar sua própria confirmação, e é
  necessário selecionar uma equipe antes de confirmar.
- Ao criar, entrar ou quando o outro participante sai, os participantes recebem
  `{"type":"room","code":"XXXXXXXX","players":1,"capacity":2}`;
  `players` reflete o número atual de conexões. Cada participante recebe ainda
  `seat` (1 ou 2) e `participants` com `{seat, ready, team, kit}`. As posições
  permanecem estáveis enquanto conectados; entrada ou saída de um participante
  cancela as confirmações existentes. Pronto não inicia uma partida.
- Erros têm a forma `{"type":"error","code":"..."}`. Uma sala admite
  duas conexões e é removida quando vazia. Desconectar equivale a sair.

As salas só existem na memória de um processo, desaparecem ao reiniciar e não
representam identidade, autenticação ou autorização. O menu principal inclui **Sala online · experimental**, com criação, entrada
por código, escolha de seleções e uniformes, contagem e confirmação de preparação dos participantes. Os dois navegadores precisam acessar o
mesmo servidor; o endereço padrão 127.0.0.1 funciona apenas na própria máquina.
Ainda não há troca de comandos, sincronização, reconexão ou simulação de partida. O limite de mensagem é 1024 bytes e cada conexão aceita
até 30 mensagens em 10 segundos; isso não substitui proteção de produção.

## Próximas etapas

Separar o núcleo da simulação da interface, definir sincronização, versão e
compatibilidade dos dados, autenticação, reconexão e proteção contra abuso;
integrar PostgreSQL com migrações e testes em banco. O esquema SQL existente em
`database/migrations/` não foi executado nesta etapa. A implantação pública
exige configuração e validação adicionais, incluindo HTTPS/WSS e segurança.

A ROM fora de `dist/` não é servida; extensões de ROM também não são aceitas
pelo servidor estático. Recursos extraídos localmente podem estar em `dist/`;
antes de publicar, é necessário preparar o conteúdo a ser distribuído.

O teste `server/test-lobby-ui.mjs` conecta dois clientes da interface ao servidor
real e verifica criação, entrada e atualização após saída. Ele não valida o
layout visual nem uma partida online, que ainda não existe.

As escolhas usam exclusivamente o catálogo original enviado pelo servidor;
conteúdo personalizado, nomes editados localmente, prévia visual dos uniformes
e verificação de compatibilidade dos pacotes ainda não estão integrados.
