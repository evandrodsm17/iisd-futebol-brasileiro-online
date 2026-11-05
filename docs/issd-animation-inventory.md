# Inventário de animações de jogo — ISS Deluxe

Este documento é uma lista de captura e validação, não uma substituição das
sequências originais. Um estado só pode receber spritesheet quando houver
descritor, OAM e paleta observados no mesmo frame de uma partida.

| Família | Evidência estática | Estado atual |
| --- | --- | --- |
| Caminhada | script `$82:CEF8`, dez keyframes e oito ponteiros de direção | oito direções validadas |
| Corrida | script `$82:CF9F`, oito keyframes e oito ponteiros de direção | oito direções validadas |
| Parado sem bola | script `$82:D320`, quatro sequências espelhadas para oito direções lógicas | descritores, direções e execução observados; OAM/VRAM/CGRAM pendentes |
| Passe/chute baixo | assets `GFX_Sprite_Player_{Up,DiagonalUp,Side,DiagonalDown,Down}_LowKick*` | assets localizados; sequência de gameplay pendente |
| Carrinho e levantar | assets `GFX_Sprite_Player_{Up,DiagonalUp,Side,DiagonalDown,Down}_Slide*` e `Side_GetUp*` | pendente de captura |
| Parado com a bola | script `$82:D6DB`, quatro sequências espelhadas para oito direções lógicas | descritores e direções recuperados; OAM/VRAM/CGRAM pendentes |
| Outras ações com bola e cabeceio | `Side_HeadbuttBall*`, `Side_DropkickBallToSide*` | pendente de captura |
| Goleiro: chute | `GFX_Sprite_Goalie_{Up,Side,DiagonalDown,Down,DiagonalUp}_{Kick,BigKick}*` | pendente de captura |
| Goleiro: defesa | máquina `$83:DCAA` (mergulho) e `$83:DDA1` (segurar/capturar) | pendente de captura |

## Ações identificadas por captura focada

Na captura de passe, a tabela de assets confirmou duas rotinas vistas em RAM:

| Rotina | Descritores observados | Identificação confirmada |
| --- | --- | --- |
| `$82:D6DB` | `$AAC4..$AB27` | jogador parado com a bola (`IdleWithBall`) |
| `$82:D79B` | `$AB30..$ABAE` | virada durante corrida (`TurnWhileSprinting`) |

A fonte é `AssetPointersAndFiles.asm`: `$90:D6C8` inicia a sequência
`GFX_Sprite_Player_Up_TurnWhileSprinting1`, enquanto `$93:D350` está na
sequência `GFX_Sprite_Player_DiagonalUp_IdleWithBall1`. Não foi rotulada uma
rotina de passe/chute nesta sessão, porque os dados observados não apontam
inequivocamente para os assets `LowKick`.

### Pose parada com a bola — estrutura e integração parcial

`$82:D6DB` não é um frame genérico de caminhada congelado. A tabela contém
quatro descritores por direção e oito entradas lógicas: `0/4` usam `$D6FF`,
`1/3` usam `$D707`, `5/7` usam `$D6F7`, enquanto `2` usa `$D70F` e `6` usa
`$D6EF`. Os descritores cobrem `$AAC4..$AB27` e resolvem os assets
`IdleWithBall` da ROM.

Isso comprova a existência da família parada com a bola e suas direções
lógicas, mas não autoriza exportar uma spritesheet: atributos OAM, paleta e
tiles de VRAM precisam ser capturados no mesmo frame. A próxima execução de
`capture_issd_action_vram.lua` já inclui `$D6DB` e registra essas evidências
quando a pose ocorrer naturalmente. A pose parada **sem** bola permanece
distinta e agora possui identificação estática própria, descrita abaixo.

Na partida web, velocidade abaixo de `0,25` seleciona espera e preserva a
direção anterior. Desde a integração descrita abaixo, há poses paradas com e
sem bola a partir das capturas; o primeiro quadro da caminhada permanece como
fallback quando os dados locais não estiverem disponíveis.

Os chamadores estáticos localizados são `CODE_84:8DA6`, `CODE_84:8E22`,
`CODE_84:9382` e `CODE_84:A9F8`. Os três primeiros instalam `$D6DB` por
`84:E66C` ou `84:E60C`; o quarto o fornece como tabela direcional a
`84:E600`, junto de `$D6EB`. Eles provam que a rotina é selecionada em mais de
um fluxo de ator. Os predicados, os significados dos temporários (`$68/$70`) e
o rótulo de gameplay de cada chamador permanecem pendentes; não se deve
generalizar todos como espera normal.

### Pose parada sem bola — sequência estática e execução observada

`$82:D320` é a família distinta de espera sem bola. Sua tabela usa oito
direções lógicas com aliases `0/4 → $D344`, `1/3 → $D34C`, `5/7 → $D33C`,
além de `$D354` para `2` e `$D334` para `6`; ela resolve 15 descritores
únicos, de `$C2A3` a `$C38D`. Os grupos gráficos resolvidos incluem
`GFX_Sprite_Player_{Up,DiagonalUp,Side,DiagonalDown,Down}_{Idle,AltIdle}*`.

A varredura passiva de 468 poses únicas observou `$D320` 24 vezes, cobrindo as
oito direções e os 15 descritores; `$D6DB` também foi observado 24 vezes com
as oito direções e 15 descritores. Essa é evidência de execução para as duas
famílias de espera, mas ainda não inclui OAM, VRAM ou CGRAM. Nenhuma folha PNG
final deve ser emitida antes da captura gráfica desses mesmos scripts.

O artefato processável é `dist/data/issd-animation-survey.json`, gerado de
`docs/issd-animation-survey.jsonl`. A sessão encerrou no frame 29.539 (antes
do teto planejado de 36.600), portanto amplia a cobertura observada, mas não
prova que todos os eventos possíveis tenham sido encontrados.

### Captura gráfica das poses paradas — cobertura e limites

A captura disponível ao exportador local contém 24 combinações de
direção/descritor de `$D320` e 10 de `$D6DB`: as oito direções estão presentes,
mas a espera com bola não tem todos os descritores em cada direção. Ela também observou cobertura parcial de chute forte
(`$D007`, três descritores em duas direções), variante de chute (`$D100`, uma
direção) e levantar (`$DB5B`, três descritores em uma direção).

O renderizador de dump completo produz uma referência transparente de
diagnóstico para cada registro capturado. Porém a validação de reconstrução por
`descriptor + OAM + CGRAM` ainda diverge pixel a pixel do dump VRAM, embora
as caixas geométricas coincidam. A causa está parcialmente localizada:
`84:E6C7` calcula o endereço VRAM a partir da fonte gráfica do descritor, em
vez de usar uma faixa local fixa. Logo, as poses paradas estão capturadas, mas
ainda não podem virar folhas genéricas por equipe/uniforme no navegador. Os
dumps locais são evidência de trabalho e permanecem ignorados pelo Git; a ROM
e seus dumps não são distribuídos.

### Primeira espera na partida web

**Correção após inspeção visual:** a integração inicial abaixo foi desativada.
Várias poses dos dumps apresentam membros ou sombras separados. A comparação
com o renderizador Python não era independente: ambos usavam os mesmos dados
de OAM/VRAM e não comprovavam que o par correspondia ao mesmo quadro da PPU.
A partida agora usa uma pose estática extraída para a prévia do editor; os
descritores dessa prévia coincidem com o primeiro descritor de `$D320` nas oito
direções. A prévia monta o cabelo e a variante de pele e aplica a paleta do
uniforme; a sombra embutida é removida para usar a sombra desenhada na partida.
Essa é uma solução visual provisória, não a animação completa de espera nem a
pose distinta com bola. As capturas e ferramentas anteriores foram mantidas
para investigação; não se deve reativá-las sem validar o pareamento PPU.

Após relato visual de jogadores flutuando e alternando aparência, o desenho
parado passou a recortar as margens transparentes da prévia e manter duas
linhas vazias sob os pés, aproximando-os da sombra da partida. A associação
de elenco passou a usar o índice local da equipe; antes, o índice global
deslocava os jogadores da segunda equipe. Após relato de perda de animação,
o goleiro voltou a usar animação ao se deslocar. Posteriormente foi ligado o
ciclo próprio da ROM descrito abaixo. A IA para dentro de dois pontos do destino para evitar trocas
constantes de direção, e a velocidade residual baixa do jogador controlado é
zerada quando não há entrada. Esses limites são correções provisórias do
protótipo, não parâmetros comprovados da física original.

A proporção da pose parada usa a média da altura visível nos quadros de
caminhada da mesma direção, calculada dos dados locais usados pela partida.
O espaço necessário é acrescentado acima da pose e permanece a margem sob os
pés. É uma calibração para manter coerência com o protótipo, não uma medida
de proporção validada contra a PPU original.

`tools/export_issd_idle_runtime.py` reconstrói localmente os índices de pixels
das peças a partir da OAM/VRAM capturadas, sem copiar a ROM. A tentativa
desativada selecionava direção e posse da bola. Para `$D320`, usava a sequência de descritores da ROM e intervalos
`$18,$06,$18,$06` em `82:E414`, conforme o caminho `84:E60C/E641`. A fase no
navegador segue o relógio da simulação; sincronização individual permanece
pendente. Para `$D6DB`, apresenta uma pose observada por direção, sem inventar
a sequência que ainda não foi capturada.

A paleta do uniforme usa um banco único, como na locomoção provisória; cabelo
individual, bancos secundários e goleiros próprios ainda não são reconstruídos.
As capturas não foram comparadas pixel a pixel com a imagem final da PPU, logo
esta integração é provisória. O teste compara 34 poses com o renderizador dos
dumps e verifica a sequência sem bola. Para regenerar os dados locais:

```powershell
python tools/export_issd_idle_runtime.py 'International Superstar Soccer Deluxe/International Superstar Soccer Deluxe (USA).sfc' docs/issd-action-vram-trace.jsonl dist/data/issd-action-scripts.json --output dist/assets/issd/idle-runtime-local.json
python tools/export_issd_idle_test.py dist/assets/issd/idle-runtime-local.json docs/issd-action-vram-trace.jsonl --output analysis/idle-reference-hashes.json
node --test dist/test-native-idle.mjs dist/test-player-drawing.mjs
```

## Chute confirmado — captura focada

A captura focada de chute observou a rotina `$82:D007`, com descritores
`$A5E1`, `$A629` e `$A63B`. Seus fluxos gráficos resolvem, respectivamente,
endereços em `$97:8A38`, `$97:9858` e `$97:9C00`; o disassembly os identifica
como quadros `GFX_Sprite_Player_{Up,DiagonalUp,Side}_BigKick*`. Portanto há
evidência de chute forte real, não apenas espera ou virada. A sessão contém
apenas seis amostras e não cobre todos os quadros/direções: ela é suficiente
para classificar a rotina, mas ainda não para exportar uma spritesheet de
chute completa.

Uma captura longa posterior observou também `$A64D`, cujo fluxo `$97:9FA8` é
`GFX_Sprite_Player_Side_BigKick6`. A sequência ainda é incompleta e permanece
fora da exportação final.

## Chute forte — sequência estática, ainda sem composição final

Além da captura, a tabela completa de descritores do chute forte foi localizada
em `$82:D007`: são oito ponteiros de direção para `$82:D037..D073`. A rotina
`CODE_84:B9A0` seleciona essa tabela (ou `$82:D100` para a variante alternativa)
e chama `CODE_84:E600` com `$82:D017`. Os oito bytes imediatamente após os
ponteiros são `06,01,01,01,01,18,04,00`; eles pertencem ao controle dessa ação
de uso único e não foram reinterpretados como a cadência circular de corrida.

O contrato de seleção foi extraído em
`dist/data/issd-big-kick-selector.json` por
`tools/extract_issd_big_kick_selector.py`. A rotina atribui `$0008` ao timer
local `$70`, reduz o bit 0 de `$6E` a `$0000` ou `$0004` em `$2E`, e usa o
resultado em `X` de `CODE_80:DD82`: valores menores que `$0005` escolhem
`$82:D007`; os demais escolhem `$82:D100`. Isso é fluxo nativo confirmado,
mas não identifica botão, intenção de jogo nem o significado do índice em `X`.
Essas associações continuam dependentes de captura de entrada e frame pareado.

O encadeamento local de handlers também foi recuperado em
`dist/data/issd-big-kick-handler-chain.json`. `CODE_84:B951` instala o registro
`$05A0` e despacha `$82:D69A`; quando o contador de `CODE_84:B96B` vence,
`CODE_84:8548` avança um registro para `$05A8`, cuja rotina `CODE_84:B999`
entra no seletor `$D007/$D100`. Esse seletor começa chamando `CODE_84:8548`;
logo ele avança comprovadamente para `$05B0`, cujo handler é `CODE_84:B9C6`.
Depois da condição zero de `CODE_84:E5D1`, esse handler alcança a rota comum
`CODE_84:878A`. Os nomes de botão, efeitos de bola e resultado visual continuam
pendentes.

Portanto a ordem de descritores de cada direção pode ser extraída da ROM sem
input manual. Ainda não há uma folha de chute no navegador porque cada quadro
precisa da montagem OAM, paleta e instante de troca que correspondam a essa
rotina; a tabela de ponteiros isolada não prova esses três dados. Isso evita
substituir o chute original por uma sequência visual inventada.

`tools/extract_issd_action_scripts.py` publica essas tabelas em
`dist/data/issd-action-scripts.json`. Além dos dois fluxos de chute, ele inclui
as tabelas de carrinho, levantar, parado com a bola e virada na corrida. As
sequências de carrinho, recuperação, chute e virada agora usam as tabelas de
duração identificadas nas rotas correspondentes; outras rotas podem escolher
outras tabelas. O arquivo não contém composição OAM nem paleta.

`tools/resolve_issd_action_descriptors.py` faz a etapa seguinte sem ampliar a
alegação de evidência: resolve cada descritor dessas tabelas para pose, fonte
gráfica e os três bytes finais, e associa o grupo de asset quando o intervalo
do disassembly o cobre, em
`dist/data/issd-action-descriptors.json`. Fontes sem intervalo recebem
`null`, nunca um rótulo aproximado. Nenhum desses dados é convertido em PNG de
personagem até haver OAM e CGRAM correspondentes da mesma ação.

`98:FB86` já prova que os três bytes finais habilitam/selecionam um DMA auxiliar
de 32 bytes nos seis contextos de `98:FB34`; ele não é evidência de uma peça
de jogador. Sua associação à peça visual/OAM auxiliar ainda está pendente.

`tools/analyze_issd_action_dma_queue.py` também verifica esse DMA quando uma
captura contém a fila nativa para um desses contextos: reproduz a origem com
`DATA_81:ED6D`, o campo capturado do ator em `+$16` e o seletor do descritor, e exige igualdade de
origem, destino e tamanho. O resultado continua sendo evidência de upload,
nunca uma atribuição automática de papel visual.

### Transição estática para levantar

`CODE_84:B91E` é um handler com dois contadores: decrementa `$70` a cada
chamada e, enquanto ele não zera, decrementa `$72`. Ao zerar `$72`, deriva um
novo valor de `($0078 & $0003) + $0003`; ao zerar `$70`, prepara `$2E = $0004`,
chama `CODE_80:DD80` e despacha a tabela `$82:DB5B` por `CODE_84:E60C`.
`tools/extract_issd_get_up_transition.py` publica esse contrato em
`dist/data/issd-get-up-transition.json`.

O nome visual da tabela é sustentado pelos assets `Player_*_GetUp*`, mas esta
extração não afirma qual colisão, queda ou botão chega a `CODE_84:B91E`; esse
vínculo precisa de cadeia de chamadores ou captura de runtime. Também não
promove a animação ao navegador: OAM, CGRAM e todos os instantes de troca
permanecem requisitos separados.

O encadeamento de handlers estático está em
`dist/data/issd-get-up-handler-chain.json`. `CODE_84:B8F1` instala o registro
`$03B8` e inicia seus contadores; quando `$70` vence em `CODE_84:B91E`,
`CODE_84:8548` avança para `$03C0` e despacha `$82:DB5B`. O handler de `$03C0`,
`CODE_84:B947`, volta a `CODE_84:B833` somente na condição zero retornada por
`CODE_84:E5D1`; esse destino instala `$0398` e despacha `$82:D320`. A cadeia
de retorno é comprovada, mas a causa que originalmente entra em `B8F1` e o
significado humano da condição de `E5D1` continuam pendentes.

### Cadeia estática de carrinho

`tools/extract_issd_slide_handler_chain.py` recupera uma segunda rota que
confirma a ligação entre o carrinho e levantar. `CODE_84:A056` despacha
`$82:DB25` e instala o registro `$02D0`; sob a condição zero de
`CODE_84:E5D1`, o handler `CODE_84:A08D` alcança `CODE_84:9FC1`, que despacha
`$82:DB5B` e instala `$02F8`. O handler deste registro, `CODE_84:9FD7`, volta
a testar `E5D1` e então escolhe entre `CODE_84:8DD1` e `CODE_84:878A` conforme
`$00A6`.

Essa é uma cadeia de controle e tabelas, não uma alegação de que todo carrinho
sempre tem o mesmo resultado físico: o predicado de entrada, a semântica de
`$00A6`, entrada de controle, colisão e composição OAM continuam pendentes.
O artefato é `dist/data/issd-slide-handler-chain.json`.

#### Correção das sequências nas oito direções

O extrator anterior procurava o fim das listas somente no bit alto dos
descritores. Para `$DB25` e `$DB5B`, isso ultrapassava o fim real de cada
lista, incorporando dados seguintes e produzindo sequências incorretas. A
rotina `84:E60C` instala a tabela de duração em `script + $10`; no fluxo
`84:E5D1`, o zero seguinte encerra a sequência. A leitura foi corrigida em
`tools/extract_issd_action_scripts.py` e regenerada em
`dist/data/issd-action-scripts.json` e `dist/data/issd-action-descriptors.json`.

| Direção interna | Carrinho `$DB25` | Recuperação `$DB5B` |
| ---: | --- | --- |
| 0 | `$B29B $B2A4 $B2AD` | `$B2B6 $B2BF $B2C8` |
| 1 | `$B2D1 $B2DA $B2E3` | `$B2EC $B2F5 $B2FE` |
| 2 | `$B307 $B310 $B319` | `$B322 $B32B $B334` |
| 3 | `$B2D1 $B2DA $B2E3` | `$B2EC $B2F5 $B2FE` |
| 4 | `$B29B $B2A4 $B2AD` | `$B2B6 $B2BF $B2C8` |
| 5 | `$B265 $B26E $B277` | `$B280 $B289 $B292` |
| 6 | `$B22F $B238 $B241` | `$B24A $B253 $B25C` |
| 7 | `$B265 $B26E $B277` | `$B280 $B289 $B292` |

As durações nominais nessas rotas são `2, 2, 32` e `5, 5, 5` quadros;
o estado do jogo pode interromper a sequência, como aconteceu após 11 quadros
da terceira pose de carrinho no replay. Direções que compartilham descritores
podem depender de atributos de espelhamento e contexto; a tabela isolada não
valida sua composição visual. `tools/test_issd_action_scripts.py` confere as
oito listas com a ROM e a sequência da direção 0 com o replay. As listas de
chute e virada, inicialmente sujeitas ao mesmo erro de limite, também foram
corrigidas posteriormente como descrito na seção seguinte.

Outra rota de recuperação, `84:9FAF → 84:E600`, usa os mesmos descritores
`$DB5B`, mas seleciona `$DB6F` com durações `16, 16, 16`. Ela foi observada
após a queda do adversário no replay `docs/issd-defense-recovery.json`; cada
uma das três poses permaneceu 16 quadros. Portanto a duração não pode ser
determinada apenas pelo identificador `$DB5B`: depende da rota de entrada.
As duas alternativas estão registradas no manifesto e no teste
`tools/test_issd_action_scripts.py`.

#### Limites de chute e virada

Na rota `84:B9A0`, `84:E600` recebe `$D017` como tabela de duração para as
listas direcionais `$D007` ou `$D100`. Os sete valores são
`6, 1, 1, 1, 1, 24, 4`, seguidos de zero. As duas tabelas possuem sete
descritores por direção nessa rota; o extrator anterior lia além delas.

Na rota `84:8A1A`, `$D79B` é selecionado com um dos cinco registros de
`$D7AB`; cada registro tem três durações e zero. O extrator agora preserva as
cinco alternativas e limita cada direção a três descritores. O significado
da escolha de variante e as condições exatas de entrada continuam pendentes.

O cruzamento com `docs/issd-natural-play-trace.jsonl` encontrou 25 amostras
de `$D007`, 10 de `$D100` e 326 de `$D79B`, todas com descritores presentes
na lista da direção registrada. Essas são amostras, não 361 animações
independentes; o traço pula quadros e não valida duração, composição, botão
ou efeito na bola. O relatório é `docs/issd-action-table-coverage.json`,
gerado por `tools/audit_issd_action_table_coverage.py`. Os dados estáticos
corrigidos e os limites das rotas não comprovam que outras chamadas desses
mesmos scripts usem a mesma tabela de duração.

### Replay pareado de carrinho e recuperação

No replay isolado DownRight, a entrada A levou o jogador `$0F00` ao estado
`$02D0`, script `$DB25`, sem contato aceito no gate de bola. O controle com
a mesma aproximação não recebeu A; 245 amostras anteriores coincidiram nos
campos registrados e os seis quadros de entrada foram conferidos. Na direção
interna `0`, o traço por quadro registrou:

| Passos relativos | Estado / script | Descritor | Nome de asset no mapa |
| --- | --- | --- | --- |
| 480–481 | `$02D0 / $DB25` | `$B29B` | `DiagonalUp_GetUp3` |
| 482–483 | `$02D0 / $DB25` | `$B2A4` | `Side_Slide1` |
| 484–494 | `$02D0 / $DB25` | `$B2AD` | `Side_Slide2` |
| 495–499 | `$02F8 / $DB5B` | `$B2B6` | `Side_Slide3` |
| 500–504 | `$02F8 / $DB5B` | `$B2BF` | `Side_GetUp1` |
| 505–509 | `$02F8 / $DB5B` | `$B2C8` | `Side_GetUp2` |
| 510 | `$0050 / $DA56` | `$B8C2` | retorno a outro estado |

Essas durações são contagens observadas nessa execução, não tempos universais
extraídos das tabelas. Em particular, `$B29B` aparece no início apesar do nome
de asset `DiagonalUp_GetUp3`, e `$B2B6` aparece já com o script de recuperação:
não se deve renomear quadros nem presumir que nome do arquivo defina a fase.
A permanência em `$B2AD` foi interrompida pela mudança de estado; a captura
não demonstra sua duração máxima. Direção de entrada do controle e direção
interna da animação são coisas distintas.

`tools/capture_issd_slide_replay.lua` salvou, para cada um dos seis descritores,
OAM espelhada e PPU, VRAM, CGRAM e imagem no callback de fim do quadro. A
auditoria em `tools/audit_issd_slide_visual_replay.py` confere o mesmo frame,
ator, estado, script e descritor no traço, além dos tamanhos e hashes dos
arquivos locais. Resumo e ressalvas: `docs/issd-slide-visual-replay.json`.
A OAM contém todos os objetos visíveis e a correspondência do quadro gráfico
com a fase exata do ator ainda precisa ser validada; não foi gerada folha de
sprites nem implementada animação de carrinho no navegador a partir disso.
Os dados gráficos e a ROM permanecem fora da distribuição.

#### Peças OAM candidatas no replay de carrinho

**Correção de sincronização:** a comparação inicial desta seção usava a OAM
da PPU no mesmo número de frame da preparação e, portanto, não demonstrava
que aqueles pixels pertenciam ao descritor indicado. A análise posterior
abaixo comprova, para este replay, que a OAM preparada aparece na PPU no
frame seguinte. Os números de 16 divergências ficam como histórico da
investigação, não como resultado final por pose.

Uma nova execução do mesmo cenário registrou a lista de desenho em
`80:95E3` e, no fim dos quadros correspondentes, OAM e CGRAM da PPU, VRAM e
imagem da tela. A faixa da pilha da entrada do ator `$0F00` até a próxima
entrada produziu os seguintes **slots candidatos**. A comparação usa a
captura PPU no frame seguinte ao callback de desenho:

| Descritor | Slots candidatos | Pixels candidatos | Divergências RGB diretas |
| --- | --- | ---: | ---: |
| `$B29B` | 32–37 | 499 | 4 |
| `$B2A4` | 32–38 | 410 | 8 |
| `$B2AD` | 32–36 | 139 | 3 |
| `$B2B6` | 32–35 | 230 | 1 |
| `$B2BF` | 32–37 | 508 | 0 |
| `$B2C8` | 32–38 | 399 | 0 |

As duas últimas comparações são exatas para os pixels candidatos; isso não
prova que todas as peças do atleta foram incluídas. As outras quatro somam
16 pixels divergentes, nenhum explicado pela comparação simples com slots
anteriores. O resumo
e hashes estão em `docs/issd-slide-oam-replay.json`, auditados por
`tools/audit_issd_slide_oam_replay.py`.

Uma captura de controle, com a mesma aproximação mas sem o comando de ação,
mostrou o mesmo pixel branco nos mesmos 16 pontos e quadros. Todos ficam na
área do minimapa desenhado sobre o campo: há forte evidência de que uma
sobreposição comum cobre os pixels candidatos. A igualdade de RGB, sozinha,
não identifica a camada da PPU nem prova a causa em nível de hardware; os
pontos continuam explicitamente registrados em
`docs/issd-slide-overlay-control.json`. A comparação pareada e os hashes são
produzidos por `tools/audit_issd_slide_overlay_control.py`; as capturas ficam
locais e a ROM não é distribuída. Antes de exportar ou usar a animação, ainda
é necessário validar a correspondência temporal e a cobertura de todas as
peças, e repetir para as demais direções e aparências.

#### Geometria nativa e sincronização corrigida

Uma captura quadro a quadro do mesmo cenário registrou a geometria lida pela
rotina de desenho `80:95E3`. Para os seis descritores, o ponteiro da pose tem
bit alto ativo e a rotina segue o caminho `80:95F2 → 80:96DB`, lendo peças
diretamente do banco `$88` da ROM. Cada registro contém deslocamentos, tile
e atributos; o tamanho é escolhido pelo bit `$10` do atributo. A comparação
com a ROM local confirmou todos os registros capturados.

As seis poses têm respectivamente 6, 7, 5, 4, 6 e 7 peças: **35 peças** no
total. Posição, tile, atributo e tamanho de todas coincidiram tanto com a
OAM preparada no espelho ao fim do frame quanto com a OAM da PPU no frame
seguinte. Essa comparação liga a geometria do corpo à faixa de desenho do
ator nesse cenário, resolvendo a defasagem que afetava a comparação inicial.

Ao comparar a PPU sincronizada com a imagem, três poses são exatas nos pixels
de corpo candidatos; as outras três têm 9, 10 e 17 divergências RGB. As 36
coincidem em posição e cor com os pixels brancos da imagem de controle na
área do minimapa. Isso continua sendo evidência de sobreposição, sem prova da
camada PPU específica. O relatório reproduzível e hashes ficam em
`docs/issd-slide-timing-geometry.json`, gerado por
`tools/audit_issd_slide_timing_geometry.py`; a captura é feita por
`tools/capture_issd_slide_replay.lua` e os dados gráficos permanecem locais.

O resultado valida a geometria das peças de corpo neste ator, direção e
cenário; não prova que cabelo ou outros objetos auxiliares estejam incluídos,
nem generaliza temporização para outros emuladores ou direções. A próxima
etapa é relacionar eventuais partes auxiliares, validar upload e paletas e
compor uma prévia da sequência antes de integrá-la à partida.

#### Tiles de corpo e investigação de cabelo no mesmo replay

Em novo replay pareado, a geometria e o deslocamento de um quadro foram
novamente verificados para as seis poses. Todos os tiles efetivamente usados
pelas 35 peças de corpo coincidiram byte a byte com as linhas gráficas
referenciadas pelos descritores na ROM: respectivamente 12, 10, 11, 8, 10
e 10 tiles distintos. Para essas peças e esse ator, todos usam o banco OBJ
capturado 1 e o banco de paleta 0. O conjunto completo de cores desse banco
coincide com a paleta do uniforme principal do Brasil no catálogo; a
igualdade da paleta, isoladamente, não prova a identidade do ator.

Os seis descritores têm seletor de detalhe zero, e nenhum dos tiles de corpo
usados na captura foi o tile relativo 23. Isso não demonstra que o detalhe de
uniforme seja desnecessário em outras aparências ou movimentos.

O hook passivo de `98:FB86`, associado a recursos auxiliares de cabelo,
registrou 84 chamadas para outros atores na janela examinada, mas nenhuma
com referência ao ator `$0F00`. As chamadas de outros atores comprovam que
o hook recebeu eventos nessa execução. A ausência de chamada para o alvo não
prova que ele não tenha cabelo ou que não existam outros caminhos de desenho:
a relação entre aparência, cabeleira e essas poses permanece pendente. Ainda
não foi validada a troca de cabelo, pele ou uniforme nessa sequência.

O relatório com endereços, tiles e hashes está em
`docs/issd-slide-body-upload.json`, reproduzível com
`tools/audit_issd_slide_body_upload.py`. Nenhum gráfico ou ROM é incluído no
relatório. Esses resultados sustentam a próxima prévia de corpo para a pose e
paleta observadas, mas não validam ainda uma animação personalizada geral.

#### Prévia local de carrinho

O laboratório em `dist/editor/locomotion-lab.html#slide-lab` apresenta as seis
poses de corpo do replay, compostas no navegador com `composeOam`, geometria e
tiles da ROM e a paleta capturada. A prévia usa as contagens observadas nesse
replay, inclusive a interrupção pela transição de estado. Ela não cobre
aparências alternativas, cabelo auxiliar ou outras direções; tampouco é a
implementação da ação na partida.

Os dados são gerados localmente em `dist/assets/issd/slide-lab-local/`,
diretório ignorado pelo Git. Com as capturas locais disponíveis, gere e
verifique a prévia usando:

```powershell
python tools/export_issd_slide_lab.py analysis/slide-aux-replay-all analysis/slide-timing-control --rom 'International Superstar Soccer Deluxe/International Superstar Soccer Deluxe (USA).sfc' --state analysis/bsnes-shared-state/issd-auto-probe-20261102-211624-trigger.State --catalog dist/data/issd-rom-catalog.json --output dist/assets/issd/slide-lab-local/preview.json
python tools/verify_issd_slide_lab.py analysis/slide-aux-replay-all dist/assets/issd/slide-lab-local/preview.json docs/issd-slide-timing-geometry.json
```

O verificador compara os pixels das seis composições de corpo com as peças da
OAM e VRAM capturadas, reposicionadas pela origem do mesmo ator; não utiliza a
imagem do minimapa como parte do atleta. Essas verificações não demonstram
que partes auxiliares foram capturadas nem que o loop visual represente uma
ação jogável completa. A ROM e os dados gerados não são distribuídos.

### Rotas comuns de saída de ação

`CODE_84:878A` e `CODE_84:8DD1` são rotas reutilizadas por handlers de ação.
Ambas chamam `CODE_84:B9D7`; a primeira consulta `CODE_80:DF67` e, no caminho
de fallback, despacha `$82:D320` e instala o registro `$0010`. A segunda
ramifica conforme `$00A6/$00D0`: uma rota vai para `878A`; a outra chama
`CODE_83:87C8`, despacha `$82:D320` e instala `$00B8`. O extrator
`tools/extract_issd_action_exit_routes.py` grava essa estrutura em
`dist/data/issd-action-exit-routes.json`.

Essas saídas explicam como sequências de ação podem voltar a usar a tabela de
poses paradas, mas não autorizam chamar `$0010` ou `$00B8` de “estado normal”:
os helpers, guards e a aparência final ainda precisam de correlação runtime.

### Despachante nativo de sequências

`CODE_84:E600` recebe controles em `A` e `Y`, zera `$1A`, grava-os em
`$18/$1C` e entra no seletor compartilhado. `CODE_84:E641` e `CODE_84:E683`
decrementam `$16`; quando ele vence, a ROM usa `$2E << 1` para buscar uma
entrada na tabela apontada por `$1C`, usa `$1A` como cursor da sequência e
envia o resultado normalizado em `X` para `CODE_84:E6C7`. O byte baixo do
controle selecionado volta a `$16`; o caminho negativo incrementa `$1A` em
dois, enquanto o não-negativo o zera.

`tools/extract_issd_animation_dispatcher.py` publica o contrato em
`dist/data/issd-animation-dispatcher.json`. Ele explica o mecanismo que
agenda descritores de ações como chute e levantar, sem inventar FPS, botão ou
montagem visual: a saída de `E6C7` ainda precisa ser cruzada com OAM, VRAM e
CGRAM do mesmo frame para gerar uma pose exportável.

### Controles brutos da sequência `$D7AB/$D79B`

`CODE_84:8A1A` seleciona um deslocamento de quatro bytes em `$82:D7AB` a
partir do byte alto mascarado do resultado de `80:E8AD`, e despacha a tabela
`$82:D79B` por `84:E600`. A tabela possui cinco registros exatos:
`05 05 05 00`, `05 04 04 00`, `04 04 04 00`, `04 03 03 00` e
`03 03 03 00`. `tools/extract_issd_d7ab_control_table.py` os publica em
`dist/data/issd-d7ab-control-table.json`.

O caminho `84:E600 → 84:E5D1` consome esses bytes como durações de descritor
nessa rota; sua seleção específica depende de `80:E8AD`. A condição de
escolha e a composição gráfica de `$D79B` permanecem pendentes de evidência
correspondente.

As capturas existentes de chute forte, carrinho e levantar possuem OAM, mas
algumas poses também usam o tile OBJ `85`, fora das duas linhas dinâmicas que
o descritor carrega para `$6000/$6100`. Como aquela coleta não armazenou VRAM
por frame, não é possível reconstruir esse tile sem adivinhar. O utilitário
`tools/export_issd_observed_action_poses.py` produz relatórios bloqueadores em
`docs/issd-observed-*-poses.json` e deliberadamente não emite PNG parcial.
Uma captura futura dessas ações deve incluir VRAM no mesmo frame de cada
descritor para desbloquear a composição fiel.

`tools/capture_issd_action_vram.lua` prepara essa coleta sem automação de
controles: durante 300 segundos, para cada descritor novo de chute forte,
carrinho ou levantar, grava as partes OAM, a VRAM completa e a CGRAM daquele
mesmo frame. A ROM e a RAM não são alteradas. Os arquivos resultantes permitem
que até tiles fora das linhas dinâmicas sejam reconstruídos antes de qualquer
spritesheet ser distribuída.

Cada snapshot inclui também `animation_handler`, `animation_timer`,
`animation_duration` e `animation_cursor`. Esses campos distinguem uma tabela
de duração por pose de um controle/hold de ação única antes que qualquer tempo
seja atribuído aos descritores.

`tools/report_issd_action_timing.py` preserva essas observações por script,
direção e descritor em vez de as converter em FPS. Assim, uma sequência só será
promovida a animação exportável quando cursor, timer, OAM, VRAM e CGRAM forem
consistentes no mesmo conjunto de frames.

`tools/render_issd_action_vram_capture.py` consome somente esse traço e suas
capturas de VRAM/CGRAM pareadas. Ele reproduz a regra de endereçamento OBJ do
SNES para cada parte OAM, inclusive tiles como `85`; não possui caminho de
fallback para sprites parciais.

O endereço de upload das duas linhas dinâmicas depende de `$02` em
`84:E6C7`. O traço anterior não tinha esse campo; o coletor agora preserva
`actor+$02` sob o nome `object_field_02`, mas a correspondência com o contexto
direto da rotina continua pendente. Como alternativa de maior confiança, o
coletor também serializa a fila DMA de VRAM em `$7E:3200`, cuja contagem está
em `$0048`; ela contém os destinos efetivos construídos pela ROM. Até que uma
dessas fontes valide o vínculo, as imagens diretas de VRAM são referência
visual, e não uma validação da reconstrução genérica por descritor.

O procedimento delimitado para a próxima sessão está em
`issd-next-runtime-capture.md`: ele prioriza `$82:D007` (chute forte), preserva
VRAM/CGRAM por descritor e impede que uma captura incompleta seja promovida a
spritesheet.

## Carrinho e levantar confirmados — captura focada

A captura focada de carrinho identificou duas rotinas reais:

| Rotina | Descritores observados | Evidência no asset map |
| --- | --- | --- |
| `$82:DB25` | `$B22F..$B307` | `Player_*_Slide*` |
| `$82:DB5B` | `$B2B6..$B334` | `Player_*_GetUp*` |

Uma resolução estática posterior corrigiu os exemplos de quadro: `$B2AD`
resolve para `$95:90B8` (`Side_Slide2`), `$B2B6` para `$95:921C`
(`Side_Slide3`) e `$B2BF` para `$95:9320` (`Side_GetUp1`). `$B29B` é
`DiagonalUp_GetUp3`, não `Side_Slide1`; o grupo em `$95:8000` permanece sem
rótulo no mapa de assets e é preservado como não resolvido. As direções e
transições foram observadas, porém não há ainda uma sequência completa por
direção para exportação final.

## Goleiro confirmado — captura focada

### Locomoção própria na partida

A tabela `$82:E34A` contém oito direções e oito descritores por direção,
com durações `$04,$03,$03,$03,$04,$03,$03,$03` em `$82:E35A`. Os 40
descritores gráficos únicos têm cinco bytes e referenciam poses do recurso
comprimido `98:88BE`, carregado em `$7E:4988`. O traço natural
`docs/issd-natural-play-trace.jsonl` contém geometria para 61 das 64
combinações de direção/quadro; três quadros da direção 4 não foram observados.
O exportador usa apenas registros cuja pose corresponde ao descritor e
compara coordenadas, tamanhos, tiles e atributos com a geometria da ROM.

Uma tentativa automática posterior reproduziu um estado de partida isolado
por até 3.600 passos, injetando direções nos dois controles e registrando
apenas `$CAB1`, `$CAB6` e `$CABB` na direção 4. Não houve registros desses
quadros. Em outra tentativa, uma intervenção opcional forçou a direção em RAM
na entrada de `84:E68F`; até o passo 2.100 houve apenas três passagens pelo hook
e nenhum quadro-alvo. Com reposicionamento adicional dos goleiros, até o passo
2.100 não houve execução observada de `$E34A`. Os testes foram encerrados e
não comprovam impossibilidade: o cenário não provocou movimento suficiente.

`tools/capture_issd_goalkeeper_coverage.lua` permite repetir a tentativa com
outro estado de partida. `ISSD_KEEPER_FORCE_DIRECTION=1` e
`ISSD_KEEPER_DISPLACE=1` são intervenções sintéticas opcionais, registradas no
traço; a ROM não é alterada. O arquivo `.status` informa progresso e direções.
Os três quadros continuam pendentes. A próxima tentativa deve partir de um
estado em que o goleiro já esteja se deslocando ou empregar um cenário que o
faça mover-se naturalmente antes de interferir na direção.

`dist/native-goalkeeper-locomotion.mjs` monta no navegador os gráficos e a
geometria específicos do goleiro, com a paleta de goleiro extraída para a
prévia do editor. O caminho é usado na partida para deslocamento; nos três
quadros não observados, usa a pose parada do goleiro. Chute e defesa próprios
continuam pendentes. Os testes comparam 366 quadros renderizados em JavaScript
com um compositor Python, para três equipes e duas variantes de pele. Essa
comparação ainda não verifica cada quadro contra uma imagem da PPU; a paleta
de gameplay e a associação da variante de pele exigem validação adicional.

Dados e referências locais podem ser gerados com:

```powershell
python tools/export_issd_goalkeeper_locomotion.py 'International Superstar Soccer Deluxe/International Superstar Soccer Deluxe (USA).sfc' docs/issd-natural-play-trace.jsonl --output dist/assets/issd/goalkeeper-locomotion-local.json
python tools/export_issd_goalkeeper_test.py dist/assets/issd/goalkeeper-locomotion-local.json dist/assets/issd/editor-preview-local.json --output analysis/goalkeeper-locomotion-hashes.json
node --test dist/test-native-goalkeeper-locomotion.mjs dist/test-player-drawing.mjs
```

| Rotina | Descritores observados | Evidência no asset map |
| --- | --- | --- |
| `$82:E571` | `$C7BE..$C7E6` | `GFX_Sprite_Goalie_*_GetUp*` |
| `$82:E7C7` | `$CC73` | `GFX_Sprite_Goalie_DiagonalUp_CaughtBall1` |

Os endereços `$8E:B698..$8E:C138` são os grupos `Goalie_*_GetUp`, enquanto
`$AB:F960` pertence ao fluxo de bola agarrada do goleiro. A coleta ainda não
fornece ciclos completos de mergulho, defesa ou chute para exportação final.

## Cobertura de deslocamento — captura de 30 segundos

`docs/issd-match-trace-coverage.jsonl` contém 900 amostras válidas (frames
2–1800), sem linhas corrompidas. Cada uma das oito direções possui um ciclo
completo observado para os dois movimentos:

| Movimento | Direções completas |
| --- | --- |
| Corrida | `0, 1, 2, 3, 4, 5, 6, 7` |
| Caminhada | `0, 1, 2, 3, 4, 5, 6, 7` |

Essa validação se refere à sequência de descritores e à geometria OAM de cada
quadro. A exportação visual em lote continuará usando a CGRAM capturada na
mesma sessão de equipes; não serão aplicadas recolorações de navegador.

## Fontes

- `Routine_Macros_ISSD.asm` do disassembly: scripts `$82:CEF8`/`$82:CF9F` e
  referências aos conjuntos gráficos em `AsarScripts/AssetPointersAndFiles.asm`.
- `issd-native/ISSDNative/issd_animation.c`: confirma 10 poses para caminhada,
  8 para corrida e a seleção por direção.
- `issd-native/ISSDNative/issd_symbols.h`: identifica as máquinas de estado de
  mergulho e captura do goleiro.

## Ordem de captura

1. Caminhada e corrida nas direções `1..7`.
2. Passe/chute e cabeceio nas direções que a ROM realmente disponibiliza.
3. Carrinho e a transição de levantar.
4. Goleiro: chute, mergulho, defesa e retenção da bola.

As amostras devem ser gravadas em partida ativa, sem placar, replay ou tela de
estatísticas. O traço preserva descritor, pose, atributos e composição OAM;
nenhum deslocamento deve ser preenchido manualmente.

## Uniformes e paletas

O catálogo extraído preserva os dois uniformes selecionáveis de cada equipe
(`home` e `away`), incluindo sua paleta OBJ de 16 cores. A composição do
sprite não deve ser pré-colorida com a imagem de uma única partida: os índices
de paleta OAM precisam selecionar o banco ativo do uniforme escolhido, e os
bancos de pele/cabelo permanecem separados. O capturador também grava a CGRAM
no encerramento, em `docs/issd-motion-coverage-cgram.hex`, para relacionar os
bancos OBJ com uma sessão concreta de jogo.

`tools/report_issd_animation_trace.py` transforma o traço em um relatório de
rotinas, estados, direções e descritores observados. Ele permite classificar
as próximas ações por evidência antes de lhes atribuir nomes como passe,
chute, carrinho ou defesa.

`tools/capture_issd_match_trace.lua` também registra o script de animação em
`object+$1C`, direção, tipo, variante de uniforme e seletor de uniforme. O
exportador usa `--cycle walking|running --direction 0..7`; as bases das oito
direções vêm diretamente das tabelas `$82:CEF8` e `$82:CF9F` da ROM USA.

`tools/extract_issd_locomotion_scripts.py` publica as oito listas de
descritores dessas duas tabelas em `dist/data/issd-locomotion-scripts.json`.
O exportador de uniformes agora lê as mesmas listas da ROM, terminadas pelo
bit alto do último ponteiro, e não calcula mais poses por uma grade de
endereços assumida.

A rotina de caminhada `CODE_84:E66E` lê o byte em `$82:CF08` (três ticks de
SNES) após a tabela de ponteiros de `$82:CEF8`. A inicialização da corrida em
`CODE_84:E60E` instala `$82:CFAF` como tabela de duração por pose; os oito
bytes da ROM USA são `4, 3, 3, 3, 4, 3, 3, 3` ticks. O renderizador web usa
essas durações a 60 Hz para as folhas OAM de locomoção. A fase inicial de cada
atleta continua apenas como defasagem visual; ela não altera a sequência nem
a duração extraídas.

A configuração atual do traço é uma coleta passiva de 1800 frames (30
segundos) e escreve em `docs/issd-match-trace-coverage.jsonl`, sem sobrescrever
o traço que validou as direções anteriores. Ela registra um callback de fim de
frame e retorna o controle ao BizHawk: é preciso caminhar/correr nas direções
durante esses trinta segundos. Ela não injeta controles.

`tools/resolve_issd_animation_assets.py` resolve cada descritor observado para
o fluxo gráfico e o nome do grupo em `AssetPointersAndFiles.asm`. Na telemetria
natural ele já encontrou famílias `LowKick`, `BigKick`, `PivotKick`,
`JumpingHeadbutt`, `Slide`, `GetUp`, `TripSlide`, `HoldBall`, `Throw`,
`Goalie_*_Kick` e `Goalie_*_QuickLeftDive`. O resultado reproduzível está em
`docs/issd-natural-play-asset-map.json`.

## Calibração provisória do navegador

As folhas OAM exportadas não possuem largura uniforme por direção: por exemplo,
na corrida, as direções `0/4` ocupam 36×52 por quadro, `2/6` ocupam 28×52 e
as diagonais ocupam 28 ou 30×52. Essas dimensões são consequência da montagem
OAM real e de suas áreas transparentes, não uma indicação para esticar cada
folha a uma caixa fixa. O Canvas preserva agora a altura comum de 38 unidades
e calcula a largura pela proporção de cada quadro, centralizada no ator. Isso
evita alargar cima/baixo em relação às orientações laterais.

O protótipo web usa velocidade-alvo provisória de `1.25` unidades de campo por
quadro para caminhar e `2` para correr, com resposta `4.5/6`, respectivamente.
Esses números são uma calibração visual separada: serão comparados à
telemetria de posição/velocidade da partida original antes de serem
considerados física final.

`tools/report_issd_motion_kinematics.py` produz
`docs/issd-motion-kinematics.json` diretamente do traço natural. O relatório
preserva tanto deltas de posição por frame emulado quanto a magnitude bruta dos
words de velocidade para caminhada (`$CEF8`) e corrida (`$CF9F`), em todas as
oito direções. Ele não converte esses números para pixels do Canvas: a escala
do campo web ainda precisa ser validada contra a projeção da ROM. Assim, a
calibração futura poderá comparar medidas sem transformar uma aproximação visual
em regra de jogo.

Há dois escopos auditados: `issd-motion-kinematics.json` inclui todos os atores
capturáveis (inclusive IA), enquanto `issd-motion-kinematics-selected-p1.json`
mantém somente o ator indicado por `selected_p1`, que será a referência para a
calibração do controle humano. Ambos são telemetria passiva em unidade de
coordenada da ROM; os valores web `1.25/2` não são derivados deles e permanecem
provisórios até existir uma projeção campo-ROM → campo-Canvas validada.

O parâmetro `--selected-p1-only` gera uma segunda leitura do mesmo traço só
para o endereço indicado em `selected_p1`; ela exclui deslocamentos de atletas
parados e da IA antes de qualquer comparação com o controle do navegador.

`tools/report_issd_motion_timing.py` complementa essa medição com o tempo de
retenção de cada descritor validado (`base + 9 × quadro`) na telemetria. O
resultado `docs/issd-motion-timing.json` registra apenas durações efetivamente
vistas, por direção e quadro; lacunas de ator são descartadas. A troca da taxa
fixa de animação do Canvas foi feita para locomoção somente após a decodificação
da rotina estática; a telemetria continua necessária para validar eventos que
dependem de estado de partida.

Para uma próxima coleta, `tools/capture_issd_match_trace.lua` inclui também
`animation_timer` (`object+$16`), `animation_duration` (`+$18`),
`animation_cursor` (`+$1A`) e `animation_handler` (`+$92`). O código nativo
confirma caminhada em `$CEF8` com dez poses de três ticks e corrida em `$CF9F`
com oito poses. A tabela estática de corrida já foi decodificada; esses campos
de captura passam a ser a confirmação em execução, não a fonte de uma taxa
inferida pelo navegador.

O renderizador web aplica a duração confirmada de caminhada e corrida em uma
máquina de 60 Hz. Caminhada: três ticks por pose. Corrida: `4,3,3,3,4,3,3,3`
ticks por ciclo. Isso não valida física, transições de estado ou seleção de
ações; somente remove taxas de apresentação inventadas para as duas folhas de
locomoção.

`tools/validate_issd_locomotion_timing.py` é a verificação reproduzível do
manifesto: ela falha se o exportador deixar de produzir os três ticks da
caminhada ou a sequência de oito durações da corrida acima.

## Cobertura de uniformes OAM

Foram exportados e verificados 1.152 arquivos RGBA não vazios em
`dist/assets/issd/oam-teams`: as 36 seleções do catálogo, dois uniformes,
dois ciclos e oito direções (`36 × 2 × 2 × 8`). O navegador usa essas folhas
compostas por OAM para toda seleção escolhida; quando uma futura exportação
não existir, o caminho continua tendo fallback explícito, sem desenhar uma
pose ou recoloração inventada.

## Calibração de direção no navegador

As folhas OAM de caminhada e corrida usam o índice bruto do ponteiro da ROM;
ele não é a enumeração geométrica adotada pelo Canvas. A validação visual das
folhas exportadas e o teste de controle no navegador fixaram a conversão
abaixo. A coluna **Canvas** é a direção física do vetor de movimento; a coluna
**folha ROM** é o sufixo de `running-N.png`/`walking-N.png` que deve ser
desenhado.

| Canvas | Folha ROM |
| --- | ---: |
| cima | 6 |
| diagonal cima-direita | 7 |
| direita | 0 |
| diagonal baixo-direita | 1 |
| baixo | 2 |
| diagonal baixo-esquerda | 3 |
| esquerda | 4 |
| diagonal cima-esquerda | 5 |

`dist/game.js` mantém essa tabela como
`romSheetIndexByScreenDirection = [6, 7, 0, 1, 2, 3, 4, 5]`. Assim, os
vetores de movimento continuam no espaço de tela e só o renderizador converte
para a ordem da ROM. Não se deve permutar `vx`/`vy`, nem renomear/exportar os
PNGs para mascarar a diferença. `tools/validate_issd_browser_direction_map.py`
protege a conversão contra regressão.

**Fonte.** Tabelas `$82:CEF8` (caminhada) e `$82:CF9F` (corrida), folhas OAM
derivadas da ROM USA e validação visual interativa reportada em 28/10/2026.
Isso confirma apenas a associação de direção da apresentação; não prova
velocidade, aceleração ou mudança de estado de locomoção.

## Regra de implementação

O navegador não deve introduzir mecânicas autorais. Movimento, aceleração,
posse, passe, chute, carrinho, colisão, goleiro e transições de animação só
podem ser promovidos de protótipo para implementação definitiva após vínculo
com rotina, tabela ou captura da ROM USA. Valores atualmente presentes no
simulador web são provisórios e servem apenas para manter a partida navegável
durante a reconstrução.

## Próxima fronteira mecânica

A tabela `$83:CF86` (`ISSD_TBL_MATCH_PLAY_PHASE` no projeto nativo) é
consultada por `$83:CF7D` como filtro de atores condicionado por `$7E:00C0`,
não como a máquina completa de fases. As transições de kickoff, bola livre,
posse e reinícios precisam ser rastreadas separadamente antes de substituir os
atalhos do protótipo. Consulte `issd-static-mechanics.md` para o gate.

As tabelas de colisão/física da bola, trajetória, mergulho e captura do goleiro
estão respectivamente em `$83:D77F`, `$83:D9A5`, `$83:DCAA` e `$83:DDA1`.
Seus comportamentos também exigem correlação antes de uso definitivo.

`tools/build_issd_animation_manifest.py` publica essa evidência em
`dist/data/issd-animation-manifest.json`, um registro de 40 estados observados
com descritores, direções e grupos gráficos. Ele separa a descoberta da ROM da
futura seleção de paleta por equipe no renderizador web.

## Telemetria de jogo natural

A sessão `docs/issd-natural-play-trace.jsonl` foi concluída com 9.000
amostras válidas ao longo de cinco minutos, sem registros JSONL corrompidos.
Ela observou 40 rotinas de animação diferentes, incluindo movimento,
posse/virada, chute forte, carrinho/recuperação e famílias do goleiro. O
relatório agregado está em `docs/issd-natural-play-animation-report.json` e é
a fonte de priorização para mapear os assets restantes sem exigir que eventos
específicos sejam reproduzidos manualmente.

## Integridade das folhas de locomoção

`tools/validate_issd_locomotion_assets.py` verifica o conjunto usado pelo
renderizador web: 36 equipes, dois uniformes, caminhada e corrida nas oito
direções, totalizando 1.152 PNGs RGBA derivados da extração. A verificação
também exige que a largura de caminhada seja divisível por 10 poses e a de
corrida por 8 poses. Assim, uma extração ausente ou uma folha incompatível não
faz o navegador cair silenciosamente em um sprite genérico.

### Goleiro: mergulho e reposição com as mãos

A revisão da captura natural `docs/issd-natural-play-trace.jsonl` encontrou
76 amostras distribuídas em nove combinações de script, descritor e direção de
goleiro. O extrator `tools/extract_issd_goalkeeper_action_evidence.py` cruza
a pose registrada com o descritor na ROM USA e resolve seu ponteiro gráfico
contra os rótulos do disassembly. A evidência detalhada, incluindo todos os
quadros observados e hashes das fontes, está em
[issd-goalkeeper-action-evidence.json](issd-goalkeeper-action-evidence.json).

Um exemplo é o ator `$0500`: na captura, os quadros amostrados 3648–3650
usam script `$82:E9CD`, descritor `$82:CBB0` e fonte `$8F:BE78`; 3652–3654
usam o mesmo script, descritor `$82:CBB5` e fonte `$8F:C140`; 3656–3670
usam script `$82:EA18`, descritor `$82:CBBA` e fonte `$8F:C3C8`. Os nomes
correspondentes no disassembly contêm `QuickLeftDive1`, `QuickLeftDive2` e
`EndOfQuickLeftDive`. A bola também aparece nos registros, mas isso por si só
não prova se houve defesa, retenção ou desvio. As amostras são espaçadas por
dois quadros e não determinam as durações exatas.

Na análise estática, os nomes do disassembly também identificam nove recursos
`LowThrow` e doze `CaughtBall`, além de cem com `Dive` no nome. Essa contagem
é de arquivos nomeados, não de movimentos confirmados nem de sequências. A
reposição manual continua pendente de correlação entre entrada, posse, saída
da bola e frames reais. Antes de integrar essas ações ao laboratório ou ao
jogo, é necessário capturar OAM, VRAM, CGRAM e imagem da PPU no mesmo quadro,
incluindo a transição da bola, e comprovar composição, paleta e temporização.
Nenhum gráfico ou byte da ROM foi incluído na evidência versionada.

### Tabela de lançamento baixo e amostras de bola agarrada

A rotina `CODE_84:ECEF` seleciona a tabela `$82:E80A` por meio de
`CODE_84:E60C`. A tabela possui oito entradas de direção que apontam para três
listas de três descritores. Os índices 0 e 4 compartilham os descritores
`$CD5E/$CD63/$CD68`, os índices 1–3 compartilham `$CD6D/$CD72/$CD77` e os
índices 5–7 compartilham `$CD4F/$CD54/$CD59`. As fontes apontadas pelos nove
descritores correspondem aos nove arquivos nomeados `Goalie_*_LowThrow` no
disassembly. Após os ponteiros há os bytes `$04,$04,$14,$00`; sua interpretação
como temporização completa ainda requer confirmação em execução, assim como o
espelhamento e a relação dos índices com a tela.

A captura `docs/issd-focus-goalkeeper.jsonl` contém nove amostras do goleiro
`$0500` nos quadros 2774–2790, espaçadas de dois quadros, com estado `$0640`,
script `$E7C7` e descritor solicitado `$CC73`, cuja fonte gráfica é `$AB:F960`,
identificada no disassembly como `Goalie_DiagonalUp_CaughtBall1`. A captura
não comprova que esse gráfico já estivesse exibido. O registro de bola e o campo
`carrier` não demonstram, sozinhos, que a posse esteja validada. A pose
registrada pelo traço é `$41F2`, enquanto a word inicial do descritor na ROM
é `$D71A`: não se deve tratá-las como a mesma geometria sem explicar o
carregamento. A captura não contém os dados sincronizados necessários para
validar pixels, temporização completa ou o lançamento posterior.

`tools/extract_issd_goalkeeper_lowthrow.py` valida os ponteiros e fontes contra
a ROM USA local e gera [issd-goalkeeper-lowthrow-table.json](issd-goalkeeper-lowthrow-table.json),
com hashes e metadados das amostras, sem distribuir gráficos ou ROM. Próximo
passo: obter uma captura contínua da retenção e da reposição com controle
registrado, incluindo geometria e dados gráficos do mesmo quadro, e comparar
as transições da bola antes de disponibilizar a ação no laboratório.

### Ordem de atualização de descritor e pose do goleiro

A divergência da captura tem uma explicação possível no próprio código, mas
não uma causa observada: `CODE_84:E6C7` grava o descritor no campo local `$14`
antes de testar `$1E`, `$14E4` e a comparação `$11E0 >= $11E2`. Caso algum
desses ramos impeça a transferência, a rotina retorna antes de gravar a word
da nova pose no campo local `$00`. Assim, uma amostra que combine descritor e
pose diferentes não autoriza afirmar que os pixels do descritor solicitado
estão visíveis. A captura antiga não registrou esses guardas; não é possível
atribuir o caso específico a um deles apenas com os dados disponíveis.

Há também viés na captura: `tools/capture_issd_match_trace.lua` só registra
atores cuja pose seja menor que `$A000`, pois interpreta a geometria como
WRAM. Portanto ela exclui a pose direta de ROM `$88:D71A` esperada pelo
descritor `$CC73`. As nove amostras representam uma solicitação do descritor
com geometria anterior observada, não validação visual de `CaughtBall1`.
O próximo capturador deve observar o desenho quando a pose estiver em ROM
e registrar a transferência e os guardas junto dos dados gráficos e da bola.
O extrator da tabela valida a ordem estática no disassembly e documenta esse
limite em [issd-goalkeeper-lowthrow-table.json](issd-goalkeeper-lowthrow-table.json).

### Observador da transferência de poses de goleiro

`tools/capture_issd_goalkeeper_transfers.lua` acompanha a entrada de
`$84:E6C7` para atores do tipo goleiro em um replay isolado. Registra o
registrador X solicitado, descritor e pose anteriores, os três guardas e o
quadro; também amostra a cada frame os dois goleiros, a bola e os controles.
A entrada da função é anterior à execução da transferência: o registro não
prova por si só que a cópia foi concluída. Os campos de bola são valores
brutos de 16 bits, e as amostras de fim de frame não são uma imagem da PPU.
O observador não escreve na memória do jogo.

Foi executado um replay de partida usando o estado local
`analysis/bsnes-shared-state/issd-auto-probe-20261102-211624-trigger.State` e
um controle sem o observador. Os 381 registros comuns de estado e entradas,
com cobertura idêntica, coincidiram nos campos comparados; isso não prova a
igualdade de estados internos não registrados. O observador registrou 1.302
amostras de goleiro e 44 entradas em `$84:E6C7`. Em todas, o guarda do ator
`$1E` era não zero; uma também tinha `$11E0 >= $11E2`. A ordem dos testes
na ROM impede inferir que o segundo guarda foi alcançado nessa chamada. Não
houve amostras dos scripts `$E7C7`, `$E7E3` ou `$E80A` nesse cenário, logo o
teste verifica o instrumento e não valida defesa ou reposição. A auditoria e
os hashes constam em [issd-goalkeeper-transfer-audit.json](issd-goalkeeper-transfer-audit.json).

Para repetir, configure `ISSD_AUTO_OUTPUT_DIR`, `ISSD_AUTO_REPLAY_STATE` e
`ISSD_AUTO_PROBE_SCRIPT`, inicie o BizHawk isolado com
`tools/capture_issd_goalkeeper_transfers.lua` e use o mesmo estado e comandos
em outro replay com `tools/automate_issd_probe.lua` como controle. O opcional
`ISSD_KEEPER_TRACE_ACTOR` limita a observação a um endereço de ator. A
comparação é feita com `tools/audit_issd_goalkeeper_transfers.py`. O próximo
passo é alcançar naturalmente uma situação de posse pelo goleiro e registrar
as mesmas variáveis junto a OAM/VRAM/CGRAM e imagem da PPU para os quadros
relevantes, antes de implementar a animação na web.

### Pose de goleiro validada no laboratório

Um replay automático iniciado do jogo, registrado em instância isolada, fez o
ator `$0500` entrar no script `$E7C7` durante 26 quadros. No quadro preparado
4435, o descritor `$CC7D` aponta para a pose direta `$88:D740` e para a fonte
gráfica `$AB:FCC8`; a imagem exibida correspondente foi capturada no quadro
4436. O replay com captura gráfica produziu exatamente o mesmo JSONL do replay
sem essa captura, mas ambos utilizaram o observador de transferências; isso
não é uma comparação sem instrumentação de qualquer tipo.

A auditoria confronta as seis peças com a geometria da ROM e com espelho OAM
e OAM da PPU, confere 12 tiles da ROM com a VRAM e compara a composição com a
imagem capturada: **359 de 359 pixels candidatos iguais**. O resultado está
em [issd-goalkeeper-catch-pose-audit.json](issd-goalkeeper-catch-pose-audit.json).
O PNG transparente local é gerado somente depois dessas verificações e fica
em `dist/assets/issd/goalkeeper-catch-local.png`, ignorado pelo Git. Ele é
visível no laboratório, seção `#goalkeeper-lab`, e usa a paleta capturada.

Para reproduzir com os artefatos locais:

```powershell
python tools/export_issd_goalkeeper_catch_pose.py analysis/keeper-catch-graphics analysis/keeper-boot-fast --rom 'International Superstar Soccer Deluxe/International Superstar Soccer Deluxe (USA).sfc' --preview dist/assets/issd/goalkeeper-catch-local.png --evidence docs/issd-goalkeeper-catch-pose-audit.json
```

É uma pose estática em uma direção, não uma sequência completa. O vínculo
com posse efetiva, liberação da bola, outras direções e uniformes ainda exige
investigação. A imagem representa apenas o corpo OAM atribuído ao goleiro;
a bola e outros objetos independentes não foram validados como parte dela.

### Reposição do goleiro: comparação de comandos

A partir de um estado salvo no quadro 4443 do replay automático, foram
comparados quatro botões (`A`, `B`, `X`, `Y`) com um controle neutro. Cada
entrada foi aplicada por seis quadros nos passos relativos 3, 20 e 70: 12
experimentos, todos com o goleiro `$0500` selecionado, controle confirmado e
campos registrados iguais ao controle antes da entrada. Nenhum dos botões no
passo 3 alterou os campos observados. Nos passos 20 e 70, `X` e `Y` também não
alteraram esses campos, enquanto `A` e `B` produziram transições diferentes.
Isso descreve apenas as janelas e o estado testados.

Com `B` no passo 20, o estado passa a `$0708` no passo 21, `$0710` no passo 25
e `$0718` no passo 26. Os descritores `$C89A`, `$C89F`, `$C8A4`, `$C8A9` e
`$C8AE` apontam para arquivos do disassembly denominados
`Goalie_Side_HighThrow2..6`. A bola também muda em relação ao controle, mas
os registros disponíveis ainda não definem toda a física nem as condições de
posse. Com `A`, o ator entra em `$0728` e `$0730`, usando recursos nomeados
`BigKick` e `Kick`. A auditoria das 12 comparações está em
[issd-goalkeeper-input-audit.json](issd-goalkeeper-input-audit.json).

A captura de `B` reproduziu exatamente o JSONL da execução pareada anterior.
Um quadro final da sequência, preparado em 4476 e exibido em 4477, foi
validado contra seis peças de geometria da ROM, OAM, VRAM e CGRAM: 435 de
435 pixels candidatos coincidiram com a imagem do jogo. A auditoria está em
[issd-goalkeeper-throw-pose-audit.json](issd-goalkeeper-throw-pose-audit.json).
A pose estática foi adicionada ao laboratório; os demais quadros ainda não
foram validados, portanto não se apresenta a sequência como uma animação
completa. O PNG gerado é local e ignorado pelo Git.

Para regenerar a pose validada a partir dos artefatos locais:

```powershell
python tools/export_issd_goalkeeper_throw_pose.py analysis/keeper-throw-graphics analysis/keeper-action-timing/20-B --rom 'International Superstar Soccer Deluxe/International Superstar Soccer Deluxe (USA).sfc' --preview dist/assets/issd/goalkeeper-throw-local.png --evidence docs/issd-goalkeeper-throw-pose-audit.json
```

### Sequência observada do lançamento alto

Cinco poses consecutivas associadas aos descritores `$C89A`, `$C89F`, `$C8A4`,
`$C8A9` e `$C8AE` foram reconstruídas a partir da ROM e comparadas com OAM,
VRAM, CGRAM e capturas da PPU. O tempo da prévia é extraído de um único replay
com `B`: 1, 2, 2, 3 e 20 quadros respectivamente, a 60 Hz. Os 20 quadros da
última pose são o trecho observado, não prova de que a ação inteira termine ali.

Para obter referências visuais sem mudar a memória, foram usados replays
separados do mesmo estado, com `B` aplicado nos passos 20, 21 ou 23; cada um
foi comparado ao controle neutro antes do comando. As poses usam a mesma
aparência e direção, mas não são cinco capturas extraídas do mesmo replay.
Em duas poses, respectivamente 2 e 4 pixels diferem da imagem e coincidem com
pixels de OAM anteriores: isso é compatível com sobreposição, mas a identidade
do objeto que cobre esses pixels não foi comprovada. O restante dos pixels,
geometria e tiles coincide. Os quadros preparados e exibidos exatos, hashes e
limitações estão em [issd-goalkeeper-throw-sequence-audit.json](issd-goalkeeper-throw-sequence-audit.json).

A sequência pode ser reproduzida e inspecionada quadro a quadro na seção
`#goalkeeper-lab` do laboratório. Ela cobre uma direção e uma paleta, sem
validar a continuação, outras aparências ou a física de lançamento da bola. A
folha PNG derivada permanece local e ignorada pelo Git. Para gerá-la novamente:

```powershell
python tools/export_issd_goalkeeper_throw_sequence.py --rom 'International Superstar Soccer Deluxe/International Superstar Soccer Deluxe (USA).sfc' --state analysis/keeper-save-before-control/keeper-start.State --sheet dist/assets/issd/slide-lab-local/goalkeeper-throw-sheet.png --evidence docs/issd-goalkeeper-throw-sequence-audit.json
```
