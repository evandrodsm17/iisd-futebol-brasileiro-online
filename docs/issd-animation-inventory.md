# Inventário de animações de jogo — ISS Deluxe

Este documento é uma lista de captura e validação, não uma substituição das
sequências originais. Um estado só pode receber spritesheet quando houver
descritor, OAM e paleta observados no mesmo frame de uma partida.

| Família | Evidência estática | Estado atual |
| --- | --- | --- |
| Caminhada | script `$82:CEF8`, dez keyframes e oito ponteiros de direção | oito direções validadas |
| Corrida | script `$82:CF9F`, oito keyframes e oito ponteiros de direção | oito direções validadas |
| Passe/chute baixo | assets `GFX_Sprite_Player_{Up,DiagonalUp,Side,DiagonalDown,Down}_LowKick*` | assets localizados; sequência de gameplay pendente |
| Carrinho e levantar | assets `GFX_Sprite_Player_{Up,DiagonalUp,Side,DiagonalDown,Down}_Slide*` e `Side_GetUp*` | pendente de captura |
| Ações com bola e cabeceio | `Side_IdleWithBall*`, `Side_HeadbuttBall*`, `Side_DropkickBallToSide*` | pendente de captura |
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
alegação de evidência: resolve cada descritor dessas tabelas para pose e fonte
gráfica e associa o grupo de asset quando o intervalo do disassembly o cobre,
em `dist/data/issd-action-descriptors.json`. Fontes sem intervalo recebem
`null`, nunca um rótulo aproximado. Nenhum desses dados é convertido em PNG de
personagem até haver OAM e CGRAM correspondentes da mesma ação.

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

O protótipo web usa velocidade máxima de `2.6` unidades de campo por quadro
para o atleta controlado, com aproximação de velocidade suavizada por um fator
de aceleração `7`. O valor anterior (`4.8`, depois `3.6`) deixava o deslocamento
mais rápido que a leitura visual do campo atual. Esta calibração é provisória:
será comparada à telemetria de posição/velocidade da partida original antes de
ser considerada física final.

`tools/report_issd_motion_kinematics.py` produz
`docs/issd-motion-kinematics.json` diretamente do traço natural. O relatório
preserva tanto deltas de posição por frame emulado quanto a magnitude bruta dos
words de velocidade para caminhada (`$CEF8`) e corrida (`$CF9F`), em todas as
oito direções. Ele não converte esses números para pixels do Canvas: a escala
do campo web ainda precisa ser validada contra a projeção da ROM. Assim, a
calibração futura poderá comparar medidas sem transformar uma aproximação visual
em regra de jogo.

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
