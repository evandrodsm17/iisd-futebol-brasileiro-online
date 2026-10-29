# Registro de engenharia reversa — ISS Deluxe

Este é o índice humano das descobertas usadas na reconstrução web. Todo dado
novo extraído da ROM, do disassembly ou de uma captura deve ter uma entrada em
Markdown aqui ou no documento temático correspondente, além do artefato
estruturado que o acompanha. A ROM USA permanece local e não é versionada.

Para desenvolver o motor a partir das descobertas, consulte a especificação
consolidada [`issd-reconstruction-spec.md`](issd-reconstruction-spec.md).

## Requisito de produto — editor

O escopo final inclui um editor de conteúdo para clubes, jogadores, uniformes,
estádios, escalações, competições e temporadas. Ele usa dados próprios
versionados e validados; não altera nem distribui a ROM. A especificação de
produto está em `product-vision.md` e deve guiar futuras implementações de
catálogo, saves e compatibilidade determinística do multiplayer.

O produto também prevê persistência em dois contextos: backend/local store para
offline e backend de serviço com banco central para online (PostgreSQL é uma
opção inicial). Essa é uma decisão de arquitetura futura; nesta fase ela não
altera a prioridade de extração da ROM nem a fonte de verdade da simulação.

## Regra de evidência

| Estado | Critério | Uso permitido no navegador |
| --- | --- | --- |
| Confirmado estaticamente | rotina, tabela ou acesso RAM localizado no disassembly/ROM | dados, limites e fluxo explicitamente observados |
| Confirmado em execução | captura passiva associa o dado a um frame/estado real | composição visual e sequência que a captura cobre |
| Pendente | falta consumidor, polaridade, captura ou transição | não implementar como mecânica final |

Um valor estático não autoriza por si só uma regra jogável. O código web deve
declarar quando mantém um comportamento provisório.

## Índice por sistema

| Sistema | Estado atual | Documento | Dados e ferramentas |
| --- | --- | --- | --- |
| Fluxo, colisão, trajetória e regras | dispatches, gates de regra e fluxo de impedimento parcialmente recuperados; máquinas de trajetória e colisão validadas estaticamente | `issd-static-mechanics.md`, `issd-mechanics-roadmap.md` | `issd-dispatch-targets.json`, `issd-dispatch-graph.json`, `issd-handler-flow.json`, `issd-handler-ram.json`, `issd-ball-trajectory.json`, `issd-trajectory-activation.json`, `issd-trajectory-script-buffer.json`, `issd-team-runtime-slots.json`, `issd-collision-machine.json`, `issd-collision-target-selection.json`, `issd-actor-collision-fields.json`, `issd-foul-gates.json`, `issd-phase-actor-gate.json`, `issd-active-actor-selection.json` e os extratores homônimos em `tools/` |
| Goleiro | seletor de mergulho, dispatch de retenção, contexto e registros de controle recuperados | `issd-static-mechanics.md` | `dist/data/issd-goalkeeper-context-writes.json`, `dist/data/issd-goalkeeper-catch-records.json`, extratores de contexto/retenção |
| Configuração de partida | normalização e transferência de 12 opções de menu confirmadas | `issd-mechanics-roadmap.md` | `dist/data/issd-match-settings.json`, `dist/data/issd-match-setting-transfer.json`, `dist/data/issd-match-setting-consumers.json`, extratores `extract_issd_match_setting_*.py` |
| Relógio | BCD, tick de 60 frames, offsets, tabelas iniciais e inicialização em `$00A8 = 0` confirmados | `issd-mechanics-roadmap.md` | `dist/data/issd-match-clock.json`, `extract_issd_match_clock.py` |
| Jogadores e animações | ciclos de caminhada/corrida, OAM e descritores parciais recuperados; ações aguardam composição VRAM completa | `issd-animation-inventory.md`, `issd-player-sprite-research.md` | `dist/data/issd-action-*.json`, `extract_issd_locomotion_scripts.py`, `validate_issd_locomotion_assets.py`, `capture_issd_action_vram.lua`, renderizadores OAM/VRAM |
| Estádios e câmera | oito layouts e geometria extraídos; câmera nativa ampla separada como extensão | `issd-mechanics-roadmap.md` | `dist/data/issd-stadium-*.json`, `dist/data/issd-camera-profiles.json`, extratores de estádio |
| Elencos, equipes e uniformes | catálogo USA, formações, paletas e duas opções de uniforme por equipe | `reference-ledger.md` | `docs/issd-rom-catalog.json`, `tools/extract_issd_catalog.py`, ativos em `dist/assets/issd/` |

## Descobertas mecânicas recentes

- `CODE_85:A456` transfere configurações de menu para registros de partida;
  estádio selecionado termina em `$7E:0086`.
- O impedimento lê `$7E:1E4A`, passa por `CODE_80:D627`, recalcula uma linha
  de referência em `CODE_A4:A442` a partir de 11 slots de ator e confirma o
  resultado uma segunda vez. A transição global posterior ainda é pendente.
- O predicado direcional de `80:D627` foi isolado: o bit 0 de `$6E` espelha a
  comparação, os limites são `$12F2/$042A` e a margem nativa é `12` ou `24`.
  O carry permanece somente um resultado de fronteira até correlação com uma
  marcação real e seu reinício.
- `$7E:19D2` é um word de eventos compartilhado: recebe o bit `$0400` após a
  confirmação de limite, mas também é alterado por falta/cartão e por escritas
  integrais. Sem consumidor estático localizado, ele não foi convertido em
  fase nem em regra do navegador.
- O relógio usa BCD; `CODE_A4:9401` só avança após 60 frames elegíveis.
  `CODE_83:B02C` zera `$00A8`, selecionando inicialmente `$81:E893`.
- A elegibilidade do tick foi delimitada: `A4:9401` faz OR de
  `$11FA/$00C0/$00B8/$00B6/$00BA` e só incrementa o contador se todos forem
  zero. Os campos ainda não receberam semântica de pausa ou reinício.
- `A4:93CC` decrementa o relógio BCD por um segundo e faz a troca
  `05:00 → 04:59`. A primeira etapa já usa a tabela `$81:E893`; o navegador
  aplica essa apresentação regressiva, mas não simula o intervalo ao zerar.
- O caminho nativo de zero (`A4:92CF`) apenas atualiza sinais de exibição e
  não escreve diretamente o índice de etapa `$00A8`; a transição de período
  deve ser investigada em outro fluxo.
- A tabela visual do relógio separa as fases `$00A8` em `0/1` e `2/3`, com
  deslocamento de três no segundo grupo. Isso prova uma fronteira de dados,
  não o nome ou a transição entre períodos.
- O goleiro possui um seletor de mergulho (`$14A8`, três entradas) e uma
  tabela de nove handlers de retenção indexada por `A`; `$1500` é contexto em
  `Y`, não o seletor da tabela. A tabela altera `$B2/$B6` e temporizadores;
  ambos usam os blocos `$0D00/$0E00`.
- A bola possui dois blocos de trajetória (`$08A0/$08D0`) com seis handlers
  temporizados e índices observáveis em `$7E:08CE/$7E:08FE`.
- O extrator de trajetória valida os destinos e as transições em `D9B1..DAED`
  contra o assembly; o JSON resultante preserva limites explícitos para que o
  Canvas não transforme estados de controle em física suposta.
- A máquina de colisão em `DATA_83:D77F` tem oito entradas de controle; duas
  são retornos diretos e as demais manipulam limites, campos do ator e o
  contador `$32`, sem semântica futebolística ainda atribuída.
- O driver `84:A69A` chama essa máquina somente com `$76` local não-zero. Seis
  avanços de `$32` foram ligados às condições que os habilitam; não há ciclo
  linear assumido e o estado inicial continua pendente.
- As cinco tabelas consultadas por esses handlers foram incluídas no artefato:
  quatro grupos de ponteiros em banco `$88` e a sequência numérica
  `0000/FFF0/FFF8/0000/FFF8/FFF0` usada na escrita de offset `$10` do ator.
- Os 16 destinos únicos desses ponteiros possuem formato confirmado de
  `contagem + registros de quatro bytes`; os quartetos foram extraídos crus,
  sem atribuir prematuramente semântica de OAM, posição ou tile.
- Os auxiliares `DC1C/DC5D` filtram 11 slots de ator para a colisão com base
  nos offsets `$001E/$0030`; o segundo exclui ainda o slot local `$3E`.
- A inicialização de ator em `86:8000` escreve `Y` em `$001E` e `0910` em
  `$0030`; as rotinas de grupos posteriores reatribuem `$001E` a partir de
  `$22`, sem nome semântico promovido para esses campos.
- As três portas de falta e duas de cartão foram indexadas por seus ramos
  literais; as configurações dependem de flags/contexto e ainda não se tornam
  regras jogáveis no navegador.
- O destino comum `80:F125` das supressões de cartão prepara `$00BA/$00C4`,
  zera `$00C6` e retorna com carry; os valores internos ainda não receberam
  rótulos de fase.
- O gate de fase `83:CF7D` filtra atores por `$30 = 1`, com uma exceção no
  índice 3 que também consulta `$11E8`; a tabela continua sem rótulos de
  kickoff, falta ou reinício.
- `83:C532` atualiza o ponteiro ativo `$11E8` e busca um slot com `$0030`
  não-zero quando necessário; a ligação desse ponteiro ao controle humano
  continua pendente de evidência em execução.
- A ativação de trajetória foi ligada ao escritor `86:9E48`: `$F4 → $D0 →`
  `$1E6C + ($22 << 1)`, seguido do carregador `83:D920`; os comandos de script
  que fornecem `$F4` ainda não foram nomeados como passe ou chute.
- `86:AADB` transfere para trajetória os 5 bits baixos de bytes de script
  quando exatamente um índice atravessa o limiar 11; `AB0F` trata o marcador
  de bit `20`. Os valores continuam sem classificação de evento.
- O buffer indireto de script `$28` tem 20 bytes, recebe uma de duas fontes de
  memória de trabalho nos offsets `146E/1482` e é consumido pelos índices
  `$48/$4A` com limiar 11.
- `86:A4A4` preenche as duas metades do buffer com uma cópia de 40 bytes de
  `$7E:3F90`; a procedência é dinâmica e não deve ser distribuída como ROM.
- `83:C6E6/C94F/C9C5` define arrays de runtime de 20 entradas por equipe e
  popula 11 atores por lado, com bases `$0500/$1000`; a formação final segue
  dinâmica e não é congelada como catálogo estático.
- O byte `06` desses registros coincide com os candidatos de aparência do
  catálogo, mas em runtime só há prova de que seu nibble alto compõe o campo
  de ator `+03`. Cabelo, pele, paleta e sprite ainda não foram inferidos.
- A distribuição dos dois nibbles de aparência foi extraída dos 720 jogadores
  para orientar captura futura por variantes reais, sem transformar seus
  rótulos de catálogo em semântica gráfica confirmada.
- `86:CA23` liga/desliga o bit de atividade `20` nas entradas após o primeiro
  byte conforme a quantidade configurada em campo. Sob a guarda de configuração
  abaixo de quatro jogadores, `83:C71D/C74F` compara as listas atuais com
  snapshots e escreve pares de seleção em `$1E6C/$1E6E`; os blocos de estado
  da trajetória são `$08A0/$08D0`. Os pares são consumidos por `83:C7CB/C870`;
  seus eventos ainda não têm nome de gameplay.
- `83:C704` cria os snapshots com cópia de 40 bytes de `$3F90` para `$D864`
  (metades `$D864/$D878`). O consumidor baixo indexa o array atual e deriva
  flags em `$19D4`; o consumidor alto troca bytes e resolve dados de ator.
- A população de ator lê registros de 10 bytes pelo índice de runtime. Os
  offsets efetivamente usados e suas transformações/destinos internos estão
  em `issd-runtime-player-record.json`, sem apelidar campos como atributos de
  jogo antes de prova adicional.
- O caminho padrão de gráfico de um ator foi ligado a
  `83:C943 → 84:F80F → 84:F813`: ele seleciona corrida `$82:CF9F`, a tabela
  direcional/temporal `$82:E34A` e prepara transferências a partir de
  `DATA_82:A3D7`. Aliases de direção continuam dados brutos, não flips
  presumidos.
- A documentação de sprites foi reconciliada: as 1.152 folhas OAM de
  caminhada/corrida para oito direções já são evidência validada e podem ser
  usadas pelo navegador; passe, chute, carrinho e defesas continuam bloqueados
  até terem sequência temporal e correlação de gameplay.
- A apresentação web de locomoção passou a carregar a cadência da ROM pelo
  manifesto validado: caminhada com 10 quadros de 3 ticks e corrida com 8
  durações `4,3,3,3,4,3,3,3`. Isso não promove velocidades ou física Canvas a
  comportamento nativo.
- O contrato visual do descritor de jogador foi corrigido: `DATA_82:A3D7` usa
  registros de nove bytes. `84:E6C7` consome os seis iniciais para pose, duas
  linhas dinâmicas de tile e detalhe de uniforme; `98:FB86` usa os bytes
  `6..7` como habilitação não nula e o byte `8` como seletor para preparar um
  DMA auxiliar de 32 bytes nos seis contextos auxiliares de `98:FB34`, não em
  slots de atleta. OAM/paleta do mesmo frame ainda precisa associar essa
  transferência à peça visual auxiliar final. Isso impede
  tratar um atlas ou uma grade fixa como sprite final.
- A cadeia auxiliar agora está delimitada: `DATA_81:ED6D` oferece 13 bases de
  quatro bytes a partir de `DATA_97:CD58`, separadas por `$0300`; `$16`
  seleciona a base e o byte `8` do descritor seleciona um bloco de 32 bytes.
  O word dos bytes `6..7` é uma guarda não nula, não um endereço de fonte.
  `98:FB34` agenda seis contextos de ator e `98:FB86` só reenfileira quando
  `$001E` é zero e `$0014` mudou. A função visual continua deliberadamente
  pendente até correlacionar OAM do mesmo quadro. Ela não é usada para
  completar o sprite do jogador.
- O correlacionador de fila DMA passou a verificar o upload auxiliar sem
  depender de uma leitura visual: para cada captura, reconstrói a origem a
  partir de `81:ED6D`, do campo de ator `+$16` e do seletor, e exige igualdade
  de origem, destino e 32 bytes na fila. Só os seis contextos auxiliares são
  avaliados. Uma correspondência prova o staging, não o tile OAM que o consome.
- O construtor OAM `80:95E0`/`80:9663` foi rastreado: para geometria dinâmica,
  soma o tile relativo em `$7E:6000` a `object+$02` antes de gravar o tile de
  hardware. As capturas passam a guardar ambos como `geometry_tile` e `tile`,
  impedindo que a recomposição de descritor use, por engano, o índice já
  deslocado da OAM.
- O contrato completo de composição OAM passou a ser extraído em
  `issd-oam-composition-contract.json`: lista em `$7E:1D40`, origem de objeto,
  base de tile, combinação de atributos e separação entre geometria dinâmica e
  compactada. Ele registra mecânica de emissão, não inventa papéis semânticos
  para cada objeto ou uma política alternativa de clipping web.
- Capturas OAM novas agora têm uma porta de validação: o utilitário
  `validate_issd_oam_capture_schema.py` exige a soma nativa entre
  `geometry_tile`, `object_field_02` e `tile`. Traços anteriores continuam
  classificados como legados, sem reescrever a evidência histórica.
- A inicialização dos blocos de trajetória foi delimitada em `83:D92D`:
  tabelas de seleção, offsets locais `$08/$0C`, exceção de estádio para ids 5/7
  e estado inicial `$22/$26/$2E/$11FA`. O artefato de trajetória preserva esse
  fato, mas continua sem atribuir semântica de posição ou velocidade a esses
  campos.
- O despacho de goleiro foi publicado como contrato estático: `$14A8` escolhe
  três modos em `83:DCAA`, enquanto A seleciona nove entradas em `83:DDA1` e
  `$1500` permanece contexto. O artefato não nomeia movimentos antes de uma
  captura que associe estados a animação e posse.
- Os modos de goleiro `1` e `2` agora têm seus próprios agendadores de 13
  entradas registrados. O primeiro é selecionado por `$22`; o segundo recebe
  `X` por helpers distintos. Ambos permanecem estados de controle sem rótulo
  visual até captura correlacionada.
- Os relatórios de cinemática de locomoção passaram a ser artefatos auditados,
  separados entre todos os atores e `selected_p1`. Eles preservam unidades
  nativas e ainda não autorizam converter a velocidade provisória do Canvas em
  física final.
- Caminhada e corrida usam durações da ROM: caminhada com 10 poses de 3 ticks
  e corrida com 8 poses de durações `4,3,3,3,4,3,3,3`.
- A camada web converte a direção de tela para o índice das folhas OAM da ROM:
  `cima,NE,direita,SE,baixo,SO,esquerda,NO → 6,7,0,1,2,3,4,5`. A conversão
  foi isolada no renderizador e validada contra as folhas exportadas; ela não
  altera `vx`/`vy` nem constitui evidência da física.
- A rotina `80:8604` atualiza `$0010` com a palavra de joypad, mantém `$0020`
  como estado sustentado e calcula `$0028` como borda `atual & ~anterior`.
  O tratamento especial dos quatro bits baixos foi preservado como evidência
  de leitura, sem atribuir ainda máscaras a botões ou ações de partida.
- A captura passiva de 3.600 frames confirmou oito combinações direcionais:
  `$0100→0`, `$0200→4`, `$0400→2`, `$0800→6`, `$0500→1`, `$0600→3`,
  `$0900→7` e `$0A00→5`, com proporção documentada na especificação.
  O bit `$4000` sustentado coincide em 1.633 de 1.659 frames com o script de
  corrida `$CF9F`; sem ele, o script de caminhada `$CEF8` predomina fora das
  transições/eventos. Isso confirma um modificador de locomoção, não sua
  identidade física nem comandos de passe/chute.
- A pose parada com a bola foi separada da caminhada: `$82:D6DB` contém oito
  direções lógicas e descritores `$AAC4..$AB27`, com aliases de ponteiro para
  as orientações simétricas. Sua composição visual ainda depende da próxima
  captura OAM/VRAM/CGRAM.
- Quatro chamadores estáticos (`84:8DA6`, `84:8E22`, `84:9382`, `84:A9F8`)
  instalam `$D6DB` por caminhos distintos. Isso amplia a evidência estrutural,
  mas não recebe rótulos de fase/posse até correlacionar cada caminho em
  execução.
- A varredura passiva registrou 468 poses únicas em 34 fontes de animação e
  separou a espera sem bola `$82:D320` da espera com bola `$82:D6DB`: ambas
  apareceram com os oito índices de direção e 15 descritores. `$D320` resolve
  grupos ROM `Idle/AltIdle`; `$D6DB`, `IdleWithBall`. A sessão terminou no
  frame 29.539, antes do teto de 36.600, logo a lista não é exaustiva.
- A captura gráfica seguinte completou `$D320` e `$D6DB`: 24 registros por
  família, 15 descritores e oito direções, cada um com OAM/VRAM/CGRAM. A
  composição direta do dump serve como referência, mas a reconstrução genérica
  por descritor ainda diverge nos pixels; nenhum PNG de equipe foi promovido ao
  navegador antes de resolver essa equivalência.
- `84:E6C7` explicou parte da divergência: as duas linhas de gráfico dinâmico
  são DMA para `$6000 + ((source_low & $01FF) << 4)` e para esse endereço mais
  `$0100` em palavras de VRAM. A normalização local de tiles não equivale ao
  endereço bruto do dump; o contrato foi extraído em
  `issd-dynamic-vram-upload.json`.
- A revisão da rotina mostrou que o deslocamento usado nesse cálculo vem de
  `$02` do contexto direto do ator, não dos bytes `2..3` do descritor. A
  captura antiga não preserva esse contexto, logo sua divergência de pixels
  não refuta nem valida o upload. `capture_issd_action_vram.lua` passou a
  registrar `object_field_02` como evidência candidata, sem alegar ainda que
  ele seja o mesmo `$02`. Como caminho direto de validação, o coletor também
  passou a registrar a fila de DMA em `$7E:3200` (contagem em `$0048`), onde
  `84:E6C7` grava destino, fonte e tamanho efetivos antes da VBlank.
  `analyze_issd_action_dma_queue.py` compara a fonte dessas entradas com as
  duas linhas do descritor, sem inferir que fila vazia seja ausência de arte.
- A revisão externa de `sergiomanzur/issd-native` encontrou uma fórmula
  compatível em `ISSDNative/issd_running.c`: `object+2` mascara `$01FF`,
  desloca quatro bits e soma `$6000` para formar a base em palavras. Ela
  corrobora a leitura de `84:E6C7`, mas é evidência comparativa; a fórmula só
  será marcada como confirmada para a ROM local quando o diagnóstico encontrar
  equivalência byte a byte em uma captura nova.

## Ponto de retomada

**Base revisada:** commit `298dd2a` (limite de evidência dos candidatos de
 aparência do elenco, cadeia de trajetória, colisão, atores, faltas/cartões e
 arrays de equipe em runtime). A revisão documental confirmou
que cada descoberta recente possui fonte no disassembly, artefato JSON com
`source` e `limitations`, explicação temática em
`issd-static-mechanics.md` e verificação automática.

**O que está pronto para usar como evidência:**

- trajetória: ativação `$F4 → $D0 → $1E6C/$1E6E`, seis estados e transferidor
  de 5 bits; os buffers que a alimentam são RAM dinâmica, não assets ROM;
- equipes/atores: arrays `$3F90/$3FA4` de 20 entradas, população de 11 atores
  por lado e filtros estáticos de colisão/fase;
- colisão e arbitragem: dispatches, seletores e portas de configuração
  extraídos, ainda sem equivalência completa para a física web.
- chute forte: `CODE_84:B9A0` confirma o seletor estático entre `$82:D007` e
  `$82:D100`, incluindo timer local, variante por bit de orientação e limiar de
  `X`; ainda não há vínculo de botão/intenção sem captura de input.
- levantar: `CODE_84:B91E` confirma a transição temporizada para `$82:DB5B`,
  mas o evento que entra nesse handler segue sem classificação semântica.
- programa de handlers: `DATA_81:BD58` tem 242 registros de oito bytes;
  `CODE_84:8548/854E` avança e carrega as três rotas de handler e a
  configuração para o ator. Os índices seguem sem nomes especulativos.

**Próximo passo ao retomar:** usar a fila DMA capturada para associar cada
descritor aos destinos reais de `84:E6C7`; somente se ela estiver vazia ou
ambígua será necessário estabelecer a ligação entre `object_field_02` e `$02`
por depurador. Depois, reconciliar a reconstrução por descritor com os dumps
VRAM de `$82:D320/$82:D6DB`. Geometria e captura estão completas, mas a
equivalência de pixels ainda não; nenhuma variante por equipe/uniforme pode ser
exportada antes disso. A captura passiva deve preservar os pares de seleção de
`CODE_83:C74F` em paralelo, pois somente a correlação visual pode classificar
posse, passe/chute ou substituir bola/posse provisórias do navegador.

Em paralelo, a próxima captura de arte de ação está pronta e delimitada em
`issd-next-runtime-capture.md`: chute forte `$82:D007`, com OAM, VRAM e CGRAM
pareados por descritor. Ela é necessária para avançar a renderização de ação
sem criar tiles ou tempos manualmente.

A mesma página também descreve a captura passiva de input/locomoção. Ela é a
próxima evidência para mapear máscaras de controle a direção, velocidade e
estado do ator antes de substituir a resposta provisória dos controles web.

## Atualização obrigatória

Ao concluir uma nova investigação, registrar:

1. fonte exata: ROM/endereço, rótulo do disassembly ou captura;
2. o que foi comprovado e o que continua pendente;
3. artefato gerado e comando/teste usado;
4. efeito aplicado — ou explicitamente não aplicado — no navegador.

O resumo desta página não substitui os documentos temáticos: eles preservam o
contexto e as limitações necessárias para implementar a mecânica com fidelidade.

## Contexto de produto

O destino do núcleo reconstruído está em `product-vision.md`: modo local e multiplayer online, clubes, temporadas, competições nacionais e sul-americanas, calendário e promoção/rebaixamento. Essas extensões não mudam o status de evidência das mecânicas da ROM e precisam de regulamentos versionados próprios.

## Verificação

Execute `python tools/verify_issd_documentation.py` após alterar extratores,
artefatos de mecânica ou esta documentação. O verificador garante a presença
do índice, dos documentos mecânicos, dos metadados de fonte/limitação e dos
artefatos essenciais de configuração e relógio; ele não substitui a revisão
humana da evidência.
