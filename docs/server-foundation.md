# Servidor e multiplayer experimental

O servidor Node em `server/` entrega `dist/`, mantém salas temporárias e
encaminha comandos. A ROM original fora de `dist/` não é servida e extensões
de ROM não são aceitas. Recursos extraídos podem existir em `dist/`; antes de
publicar, é necessário preparar o conteúdo a ser distribuído. O serviço não
possui autenticação, persistência, PostgreSQL conectado ou proteção de produção.

## Executar e testar

Com Node.js 20 ou superior, na raiz do projeto:

```powershell
npm install
npm start
```

O endereço padrão é `http://127.0.0.1:4173/`, restrito a este computador.
Para usar outra porta, defina `$env:PORT=4175` antes de executar `npm start`.
`HOST` configura a interface de escuta. A implantação pública exige trabalho
adicional de segurança, HTTPS/WSS, autenticação e infraestrutura.

Para experimentar a movimentação, abra o mesmo servidor em **duas janelas**
de navegador, escolha **Sala online · experimental**, crie a sala na primeira
e entre com o código na segunda. Cada participante escolhe **Escolher equipe
e uniforme**, navega pelas mesmas páginas com bandeiras do modo local e
seleciona sua equipe. Quando ambos escolherem, avance para os uniformes: as
duas prévias são atualizadas em tempo real e cada pessoa altera apenas seu
próprio uniforme. Confirme para voltar à sala e marque que está pronto. Após a verificação de dados e da troca de comandos, o
anfitrião seleciona **Iniciar teste online**. WASD movimenta, Shift permite correr, X executa passe rasteiro e Q troca
o atleta controlado. Ambas as janelas devem permanecer visíveis: navegadores podem
suspender a execução de abas em segundo plano.

Esse teste sincroniza o movimento de um atleta por equipe e a condução
provisória da bola, o passe rasteiro e a troca do atleta controlado. Os outros
atletas ficam parados; chute, carrinho, contato com os demais atletas, saídas
de campo, placar e relógio estão desativados durante o teste.
Os dois atletas controlados usam o contato provisório do modo local para
separação corporal. O adversário inicia com o atleta elegível mais próximo
da bola, usando o mesmo critério provisório de seleção já existente. A saída ou perda
da conexão de um participante interrompe o outro. O modo local mantém sua
simulação existente. A física do protótipo é provisória, não uma reprodução
validada da ROM. O endpoint `/api/v1/status` continua reportando
`online_multiplayer: false` porque uma partida completa ainda não é jogável.

## Validação

`npm run test:server` cobre salas, escolhas, preparo, identificação da versão,
sequência de entrada e desconexão. Os testes `dist/test-*.mjs` cobrem o motor
local e seus componentes. `npm run test:online-browser` abre dois navegadores
**ocultos**, cria uma sala, confirma que o adversário inicia próximo da bola, movimenta
ambos os jogadores, verifica contato corporal, compara posições e verifica a
interrupção ao sair. No Windows usa o Chrome instalado em
`C:/Program Files/Google/Chrome/Application/chrome.exe`; outra localização
pode ser informada em `PLAYWRIGHT_CHROME_PATH`. Em outros sistemas, instale um
navegador compatível com Playwright ou defina essa variável. O teste usa um
servidor isolado em porta temporária e não altera as janelas do usuário.

## Sala e protocolo

`/api/v1/lobby` usa WebSocket e protocolo 2. Criação e entrada exigem a
identidade da versão; a sala admite dois participantes e um anfitrião.
Equipes, uniformes, estádio e relógio inicial são validados pelo servidor.
Mudanças invalidam as confirmações. Se o anfitrião sair, o participante
restante assume a função. As salas existem apenas na memória do processo.

Quando ambos confirmam, cada navegador verifica o catálogo-base e o estádio
e informa `prepared`. Essa confirmação é declarada pelo cliente, não uma
prova de integridade. A sala envia um ciclo neutro como diagnóstico; o início
experimental usa outra época e outra fila, para que o teste não consuma o
primeiro ciclo de movimentação. A época é invalidada em mudanças de sala.

Comandos codificados possuem ciclo, máscara de direções e ações. O servidor
reúne o mesmo ciclo de ambos na ordem 1P/2P e limita o avanço a oito ciclos.
O teste envia direções, corrida e as ações de passe e troca; outras ações
são ignoradas. O
cliente valida épocas, ordem e seu próprio comando retornado. O servidor não
executa a física, portanto não é autoritativo nem detecta divergências.
Não há compensação de atraso, reconexão ou recuperação de estado. Pings
verificam a conexão; limites de mensagem não substituem segurança de produção.

## Identidade e preparação

`npm run build:identity` gera `dist/online-build.mjs` com SHA-256 dos módulos
JavaScript em `dist/` (exceto testes e o arquivo gerado) e do catálogo-base.
CRLF é normalizado para LF. Após alterar esses arquivos, gere a identidade,
registre-a com o código e reinicie o servidor. A verificação não cobre todos
os JSONs, imagens, áudio, alterações locais do editor ou conteúdo personalizado;
o valor declarado pelo cliente não protege contra adulteração.

O teste usa o catálogo original, sem alterações locais do editor. Equipes,
uniformes, escalações, estádio e valor inicial do relógio são preparados a
partir da sala. A projeção experimental é desativada para o teste. Os recursos
de clubes e pacotes personalizados ainda não estão integrados ao online.

## Próximos passos

Sincronizar o estado inicial completo e verificar sua igualdade; integrar a
bola e suas interações, colisões, ações, IA, goleiros, saídas e reinícios;
implementar relógio e placar; validar o comportamento contra a ROM; definir
tratamento de atraso, pausa, desconexão, divergência, segurança e persistência.
A ordem de processamento dos times no protótipo é uma escolha da versão web,
não uma regra confirmada na ROM. O núcleo continua acoplado ao navegador.

## Seleção online de equipes e uniformes

A sala reutiliza as telas de grupos, bandeiras e prévias de uniforme do modo
local. Cada participante controla somente seu lado e as escolhas chegam pelo
servidor; o avanço aos uniformes aguarda duas equipes selecionadas. O catálogo
base é carregado temporariamente e o estado local anterior é restaurado ao
sair da seleção ou iniciar o teste. O teste de navegador percorre as páginas,
valida as restrições de lado, compara a alteração visual da prévia e verifica
a propagação das escolhas entre os dois clientes. Clubes personalizados e
editores locais ainda não participam desse fluxo online.

## Seleção inicial e contato entre os dois atletas

O atleta controlado pelo time 2 é escolhido após posicionar a bola no centro,
por `chooseControlledNearBall`, desconsiderando atletas caídos e mantendo a
ordem da equipe em caso de empate. O teste em dois navegadores compara a
distância com todos os atletas adversários na posição inicial. Durante o
teste online, `resolvePlayerContacts` aplica a mesma separação provisória do
modo local somente aos dois atletas humanos, na ordem de equipe. O teste
mede que a separação se mantém durante o encontro e compara os dois clientes.
A geometria e a resposta do contato ainda não foram validadas como idênticas
à ROM; não incluem carrinho, faltas ou contato com os outros atletas.

## Bola e condução no teste online

A posse começa com o atleta do time 0 e a bola no centro. Após cada par de
comandos, o teste atualiza orientação dos atletas no ciclo fixo e aplica
`advanceOnlineBall` e `settleDribble`, com os mesmos parâmetros provisórios do jogo local. Se a
posse se perder por distância, a bola desacelera com o mesmo atrito provisório
e os dois atletas humanos podem recuperá-la pelo contato existente. O teste
de dois navegadores compara posição e posse da bola durante a condução e após
o contato entre atletas. Os demais atletas não disputam a bola; saídas de
campo e reposições são tratados conforme descrito abaixo; chute ainda não está implementado nesse modo.
Esses parâmetros ainda não são física validada como idêntica à ROM.

## Passe e troca no teste online

O teste envia os comandos `pass` e `switch` junto aos movimentos e executa
os dois lados na ordem provisória da versão web. `pass` usa as mesmas
funções de direção, escolha de alvo e velocidade do jogo local; a bola solta
usa `PASS_FRICTION` e o intervalo provisório de recuperação. `switch` escolhe
o atleta elegível mais próximo da bola. Apenas os dois atletas controlados
podem recolher a bola nesse teste; os demais permanecem parados, inclusive
quando escolhidos como alvo de um passe. O teste com dois navegadores valida
direção do passe, posição e posse coerentes e troca de atleta. A física e a
assistência de passe ainda não foram validadas como idênticas à ROM.

## Saídas e reinícios no teste online

O ciclo online usa a posição anterior e a atual da bola com as regras já
existentes do jogo local para classificar gol, lateral, escanteio e tiro de
meta. Após gol, o reinício escolhe o atleta humano do time 2 mais próximo
da bola central. Um teste em dois navegadores produz uma saída lateral
com comandos reais e verifica classificação e reposição sincronizadas.
Essas regras e a física ainda são provisórias. O lateral agora aguarda
a direção e o comando do cobrador, e os dois navegadores sincronizam o
arremesso. Um trecho de corpo capturado é composto quando os recursos locais
estão disponíveis; cabelo, outras orientações e física fiel ainda estão pendentes.

A investigação específica da cobrança original está em
[issd-throw-in-research.md](issd-throw-in-research.md).
