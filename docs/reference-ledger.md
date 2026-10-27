# Registro de referência — futebol arcade

Este documento separa **o que foi observado** do que ainda será medido. A ROM
local é utilizada para observação no BizHawk e para extrair, localmente, os
tiles visuais necessários ao protótipo privado. O build não contém ROM nem
emulador.

## Evidência disponível

- ROM local carregada no BizHawk com o núcleo Snes9x em 26/10/2026.
- Arquivo de referência: 2.097.152 bytes; SHA-256
  `d2fe66c1ce66c65ce14e478c94be2e616f9e2cad374b5783a6a64d3c1a99cfa9`.
- O REA identificou a integridade do arquivo, mas não oferece descompilação da
  CPU 65C816 do SNES. A mecânica será catalogada por cenários reproduzíveis.
- O catálogo `issd-rom-catalog.json` foi extraído da mesma ROM validada: 36
  seleções, 720 jogadores, atributos brutos/decodificados e formações. Os
  offsets foram conferidos contra a recompilação `issd-native`: nomes em
  `0x03818E`, atributos em `0x050000` e ponteiros de formação em `0x05EF48`.
- As bandeiras das 36 seleções foram extraídas dos streams comprimidos de
  `0xA7:E4B6–0xA7:EC14`; cada uma usa duas metades 24×8 e sua paleta original
  de quatro cores. `tools/extract_issd_flags.py` exporta o PNG composto 24×16
  e um manifesto com os endereços de origem, sem incluir a ROM no build.
- Cada registro de formação tem 31 bytes: rótulo, dez pares assinados de
  profundidade/largura e dez papéis. Os papéis 1/5 são defensor/defensor que
  apoia, 2/6 meia/meia que apoia e 3 atacante; o goleiro é posicionado pelo
  motor. A web usa esses valores para as casas iniciais, projetados para a
  câmera longa (a escala visual não é uma coordenada de tela da ROM).
- A paleta de cada uniforme tem 16 cores de OBJ. Ela contém as cores de
  pele/cabelo compartilhadas, três tons de camisa, três de calção, dois de
  meia e cores auxiliares. As folhas de corrida agora são renderizadas uma vez
  por seleção e por uniforme com essa paleta real. O nibble alto do registro
  individual seleciona uma das variações de cabelo; sua composição final ainda
  depende da captura OAM, então não será simulada por uma imagem inventada.
- O estádio-base foi reconstruído da ROM por `tools/extract_issd_stadium.py`.
  O processo reconstitui os recursos de VRAM, paleta e mapas do layout 0 e
  produz uma cena original de 2816×1280; o canvas a projeta para a câmera
  ampla. O antigo `Field.png` deixa de ser a fonte visual da partida.
- A referência de câmera passou a ser a janela clássica da partida: o motor
  nativo trabalha com buffer 256×224 e o build web o apresenta no quadro 4:3
  central. O perfil widescreen continua separado e não altera física, regras
  nem coordenadas do mundo. O seguimento da bola e os limites do campo são
  provisórios até a captura de uma partida; a textura usa somente o retângulo
  não transparente do estádio extraído, em vez de reduzir a cena inteira com
  sua margem vazia.

## Matriz de observação

| Área | Cenário | Medida que falta | Status |
| --- | --- | --- | --- |
| Movimento | corrida, inversão e diagonal | velocidade e desaceleração por frame | pendente |
| Bola | condução, passe e chute | distância da bola, impulso e atrito | pendente |
| Posse | contato entre jogadores | janela de roubo e recuperação | pendente |
| Câmera | bola no centro, laterais e gols | área visível e atraso de seguimento da janela clássica 256×224 | pendente |
| Campo | escanteio, lateral, gol | reposicionamento e reinício | pendente |
| IA | sem comando e troca de jogador | marcação, apoio e seleção | pendente |
| Dados | 36 seleções e 720 jogadores | catálogo exportado com hash e bytes brutos | concluído |
| Identidade | bandeiras das 36 seleções | streams, paletas e composição 24×16 exportados | concluído |
| Formação | posições iniciais das 36 seleções | registros de 31 bytes projetados para a câmera longa | concluído |
| Campo | layout-base, gramado, redes e arquibancada | cena de 2816×1280 reconstruída de tilemaps/paletas da ROM | concluído |

## Próxima captura de física

`tools/capture_issd_match_trace.lua` registra, em uma partida já iniciada, os
valores de mundo da bola (posição, velocidade e altura), portador, câmera e
atores ativos. A captura é somente de leitura e permite calibrar a versão web
em unidades da ROM: coordenadas 16-bit, 60 quadros por segundo e estado de
posse independente da posição visual do jogador.

## Implementação web — decisões originais

- O campo é uma unidade lógica independente da resolução do canvas.
- A bola é uma entidade física independente: a posse é uma condição de
  proximidade e os toques a impulsionam à frente, sem colá-la ao jogador. O
  protótipo agora usa atrito de rolagem fixo (`0,03125` por quadro), altura
  negativa em voo, gravidade e restituição seca de `0,75`; a escala final será
  confrontada com a captura de partida.
- Cada lado tem 11 jogadores e regras simples de apoio/marcação.
- A câmera de referência usa a janela clássica 4:3; a ampliação horizontal é
  uma melhoria posterior e isolada. O zoom e a curva de seguimento só serão
  considerados fiéis após confronto com a captura de partida.
- As folhas de jogador em `dist/assets/issd/` são PNGs gerados dos tiles de
  corrida da ROM local. `tools/render_issd_sprites.py` registra o passo de
  conversão 4bpp para PNG e, com o catálogo, gera as folhas de cada uniforme
  original em `dist/assets/issd/teams/`. O mapa de campo externo é somente referência
  temporária: a próxima etapa usa os blocos extraídos
  `GFX_Layer2_GrassySoccerField` e `GFX_Layer3_InGame_SoccerFieldMap`.
- Um jogador não é uma imagem plana na ROM: o corpo dinâmico é carregado em
  doze tiles 8×8 organizados em 3×4, e a composição final depende de entradas
  OAM (deslocamentos X/Y, tile, prioridade, paleta e espelhamento), além das
  camadas de cabelo e detalhes de uniforme. A adaptação web não deve tratar
  esses doze tiles como uma grade 4×3 nem substituir a paleta original.

Próxima revisão: preencher uma linha da matriz por vez com um cenário jogável
e gravar valores em unidades lógicas, não pixels de tela.
