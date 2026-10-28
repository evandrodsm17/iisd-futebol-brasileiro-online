# Registro de engenharia reversa — ISS Deluxe

Este é o índice humano das descobertas usadas na reconstrução web. Todo dado
novo extraído da ROM, do disassembly ou de uma captura deve ter uma entrada em
Markdown aqui ou no documento temático correspondente, além do artefato
estruturado que o acompanha. A ROM USA permanece local e não é versionada.

Para desenvolver o motor a partir das descobertas, consulte a especificação
consolidada [`issd-reconstruction-spec.md`](issd-reconstruction-spec.md).

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
- O relógio usa BCD; `CODE_A4:9401` só avança após 60 frames elegíveis.
  `CODE_83:B02C` zera `$00A8`, selecionando inicialmente `$81:E893`.
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
- Caminhada e corrida usam durações da ROM: caminhada com 10 poses de 3 ticks
  e corrida com 8 poses de durações `4,3,3,3,4,3,3,3`.
- A camada web converte a direção de tela para o índice das folhas OAM da ROM:
  `cima,NE,direita,SE,baixo,SO,esquerda,NO → 6,7,0,1,2,3,4,5`. A conversão
  foi isolada no renderizador e validada contra as folhas exportadas; ela não
  altera `vx`/`vy` nem constitui evidência da física.

## Ponto de retomada

**Base revisada:** commit `498ef95` (cadeia de trajetória, colisão, atores,
faltas/cartões e arrays de equipe em runtime). A revisão documental confirmou
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

**Próximo passo ao retomar:** correlacionar por captura passiva os pares de
seleção já recuperados de `CODE_83:C74F` com eventos e atores em cena. A cadeia
estática até os consumidores `83:C7CB/C870` está documentada; só a correlação
visual pode classificar passe/chute ou substituir bola/posse provisórias do
navegador. A etapa exigirá coordenadas, velocidades e efeito visual por frame.

## Atualização obrigatória

Ao concluir uma nova investigação, registrar:

1. fonte exata: ROM/endereço, rótulo do disassembly ou captura;
2. o que foi comprovado e o que continua pendente;
3. artefato gerado e comando/teste usado;
4. efeito aplicado — ou explicitamente não aplicado — no navegador.

O resumo desta página não substitui os documentos temáticos: eles preservam o
contexto e as limitações necessárias para implementar a mecânica com fidelidade.

## Verificação

Execute `python tools/verify_issd_documentation.py` após alterar extratores,
artefatos de mecânica ou esta documentação. O verificador garante a presença
do índice, dos documentos mecânicos, dos metadados de fonte/limitação e dos
artefatos essenciais de configuração e relógio; ele não substitui a revisão
humana da evidência.
