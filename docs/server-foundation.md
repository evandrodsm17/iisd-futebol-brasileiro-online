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
`{"type":"connected","protocol":2,"teams":[...]}` com os IDs e nomes do catálogo original do servidor. As mensagens são JSON:

- `{"type":"create","protocol":2}` cria uma sala temporária com código aleatório.
- `{"type":"join","protocol":2,"code":"XXXXXXXX"}` entra pelo código hexadecimal.
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
  `seat` (1 ou 2), `participants` com `{seat, ready, team, kit}` e
  `phase`: `waiting` (falta participante), `selection` (escolhas ou
  confirmações pendentes) ou `ready` (dois participantes selecionaram e
  confirmaram). O estado `ready` não inicia uma partida. As posições
  permanecem estáveis enquanto conectados; entrada ou saída de um participante
  cancela as confirmações existentes. Pronto não inicia uma partida.
- Erros têm a forma `{"type":"error","code":"..."}`. Uma sala admite
  duas conexões e é removida quando vazia. Desconectar equivale a sair.

As salas só existem na memória de um processo, desaparecem ao reiniciar e não
representam identidade, autenticação ou autorização. O menu principal inclui **Sala online · experimental**, com criação, entrada
por código, escolha de seleções e uniformes, contagem e confirmação de preparação dos participantes. Os dois navegadores precisam acessar o
mesmo servidor; o endereço padrão 127.0.0.1 funciona apenas na própria máquina.
Há um canal experimental de teste de comandos, ainda não ligado ao jogo; não há sincronização, reconexão ou simulação de partida. O limite de mensagem é 1024 bytes e cada conexão aceita
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

O servidor verifica conexões WebSocket a cada 15 segundos por ping/pong e
remove conexões que deixam de responder, liberando sua posição e cancelando
as confirmações restantes. Isso não oferece reconexão automática ou garantia
de sessão persistente. A semelhança de cores dos uniformes ainda não é
verificada; e ainda não há validação do conteúdo personalizado ou garantia de integridade do cliente.

A versão 2 do protocolo é obrigatória ao criar ou entrar em salas; versões
ausentes ou diferentes recebem `protocol_mismatch`. A interface também recusa
um servidor com versão diferente e orienta a atualizar. Esta verificação cobre
apenas o formato da comunicação da sala: não verifica a versão da simulação,
a integridade do cliente, as edições locais ou o hash do pacote de conteúdo.

## Identidade da versão do jogo

`npm run build:identity` gera `dist/online-build.mjs` com um SHA-256 dos
arquivos JavaScript em `dist/` (exceto testes e o próprio arquivo gerado) e do
catálogo `dist/data/issd-rom-catalog.json`. A ordem é estável e finais de linha
CRLF são normalizados para LF. Após alterar esses arquivos, gere novamente a
identidade, registre-a junto às alterações e reinicie o servidor. O navegador
envia a identidade gerada ao criar ou entrar; o servidor calcula a sua ao
iniciar e recusa valores diferentes. Os clientes devem recarregar a página.

O valor é declarado pelo cliente e não é uma prova contra adulteração. A
identidade não cobre imagens, áudio, outros JSONs, edições locais do navegador,
conteúdo personalizado ou arquivos alterados depois da inicialização do servidor.
Ela não garante que simulações sejam determinísticas nem habilita partidas.

## Comandos por ciclo

`dist/input-frame.mjs` captura as direções, o botão de corrida e os eventos
pontuais em cada atualização fixa do jogo local. Direções permanecem ativas
enquanto seguradas; eventos são consumidos uma vez e mantêm sua ordem. O jogo
usa esse retrato para movimentação e para distribuir os eventos de ação.
Passe, chute e carrinho também recebem direção e modificador de corrida desse
mesmo retrato, sem consultar o teclado diretamente. A simulação ainda está
acoplada à interface e controla apenas o time local. O jogo não transmite esse retrato e ele ainda não permite reproduzir ou sincronizar uma partida.

## Formato experimental de entrada online

`dist/online-input.mjs` codifica um ciclo como `{tick, held, actions}`. `tick`
é inteiro seguro não negativo; `held` é uma máscara de 0 a 31 (cima=1,
baixo=2, esquerda=4, direita=8, corrida=16); `actions` mantém a ordem e admite
até 32 eventos entre `switch`, `shot`, `pass` e `press`. Comandos opostos
podem coexistir e seguem a regra local de cancelamento. A ação local `reset`
não faz parte desse formato. Mensagens inválidas são rejeitadas, e os arrays
são copiados na codificação e decodificação.

O WebSocket aceita `{"type":"input-test","epoch":"<inputEpoch>","input":{"tick":0,"held":1,"actions":[]}}`
apenas em sala com dois jogadores prontos e encaminha ao outro participante
com o `seat` atribuído pelo servidor. Os ciclos começam em zero e são aceitos
em ordem estrita e independente por jogador; mudanças de preparação, escolha
ou participantes reiniciam a sequência e geram um novo `inputEpoch` aleatório
de 128 bits, informado nos estados da sala. Um pacote precisa carregar a
época atual; a resposta encaminhada inclui essa mesma época. Pacotes de uma
época anterior, malformados, repetidos ou fora de ordem são recusados. O limite experimental é 900 comandos por 10
segundos por conexão, separado do limite de mensagens de controle.

Nenhuma interface ou partida usa esse canal. Ele não define sincronização,
janela de ciclos, atraso, repetição,
autoridade do servidor, proteção contra trapaça ou reconexão. A física e as
ações permanecem as implementações atuais, não validadas como idênticas à ROM
por esta mudança.
