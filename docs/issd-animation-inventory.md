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

### Pose parada com a bola — estrutura confirmada, composição pendente

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

No navegador, velocidade abaixo de `0,25` agora interrompe o ciclo de
locomoção e preserva a direção anterior. Enquanto não há folha `idle`
validada, a apresentação congela o primeiro quadro da caminhada somente como
fallback técnico. Esse quadro não é rotulado como arte original de espera e
deve ser substituído pela composição `$D6DB` — ou pela futura pose sem bola —
quando a captura correspondente existir.

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

### Captura gráfica das poses paradas — completa, exportação genérica bloqueada

A captura OAM/VRAM/CGRAM subsequente registrou 24 poses de `$D320` e 24 de
`$D6DB`: em ambos os casos são 15 descritores nas oito direções e todos os
dumps pareados existem. Ela também observou cobertura parcial de chute forte
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
as tabelas já confirmadas de carrinho, levantar, parado com a bola e virada na
corrida. O arquivo declara explicitamente que não contém composição OAM,
paleta ou interpretação de tempo.

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

Esses bytes são controles nativos, não FPS ou duração de pose comprovados. A
função de `80:E8AD`, a condição de escolha e a composição gráfica de `$D79B`
permanecem pendentes de evidência correspondente.

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

O disassembly/nativo já identifica a máquina de fases da partida em
`$83:CF86` (`ISSD_TBL_MATCH_PLAY_PHASE`). A próxima implementação substitui
gradualmente os atalhos do protótipo por transições extraídas dessa máquina e
pelos registros de bola/jogador observados na telemetria, começando por
kickoff, bola livre, posse e reinício.

O dispatch primário lê `$7E:00C0`, dobra o índice e salta pela tabela
`$83:CF86`; a tabela de colisão/física da bola está em `$83:D77F`, trajetória
em `$83:D9A5`, mergulho do goleiro em `$83:DCAA` e captura em `$83:DDA1`.
Esses endereços são os pontos de entrada para substituir cada atalho do
protótipo por comportamento recuperado, mantendo estados ainda não resolvidos
fora da implementação definitiva.

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
