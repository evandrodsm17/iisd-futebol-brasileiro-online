# Servidor e multiplayer experimental

O servidor Node em `server/` entrega `dist/`, mantém salas temporárias e
encaminha comandos. A ROM original fora de `dist/` não é servida e extensões
de ROM não são aceitas. Recursos extraídos podem existir em `dist/`; antes de
publicar, é necessário preparar o conteúdo a ser distribuído. O serviço não
possui autenticação, persistência, PostgreSQL conectado ou proteção de produção.

## Executar e jogar

O passo a passo para iniciar o servidor, jogar no mesmo computador ou na rede local, configurar a sala e usar os controles está em [Como jogar o teste multiplayer online](como-jogar-multiplayer.md). O teste continua experimental e não substitui uma partida completa.

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
O teste envia direções, corrida, passe contextual e troca; o chute é aceito apenas para cobrança de lateral. Outros comandos são ignorados. O
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
partir da sala. A projeção visual medida do estádio é ativada no teste, com reserva para imagens sem mapeamento. Os recursos
de clubes e pacotes personalizados ainda não estão integrados ao online.

## Próximos passos

Aprofundar a sincronização do estado inicial e verificar sua igualdade; ampliar as interações da bola, colisões, ações, IA, goleiros, saídas e reinícios; implementar o avanço do relógio e o fluxo completo de partida; validar o comportamento contra a ROM; definir
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
à ROM; não incluem faltas ou contato com os outros atletas; X pode acionar o desarme e a reação provisórios entre os atletas controlados.

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
os dois lados na ordem provisória da versão web. `pass` atua como tentativa de desarme sem posse; com posse, usa as mesmas
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

## Recepção de lateral em voo

No teste online, os dois atletas humanos podem coletar em voo a bola de uma
cobrança lateral ao atingir a geometria de contato existente. A bola passa
imediatamente aos pés do recebedor; escala, intervalo de recuperação e
escolha de candidatos permanecem provisórios. Os demais atletas não
participam da disputa nesse teste, e a animação capturada de recepção só é acionada em dois contextos experimentais
restritos, descrito na investigação do lateral.
