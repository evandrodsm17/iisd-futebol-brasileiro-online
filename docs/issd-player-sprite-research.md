# Pesquisa de sprite de jogador — ISS Deluxe

## Fatos observados

- `web-snes-issd-studio/src/rom/graphics.mjs`, função `spriteResource`, já
  documenta que o jogo envia duas linhas dinâmicas a VRAM e que OAM carrega
  posição assinada, tamanho 8/16 e espelhamento horizontal. Sua composição
  conserva a precedência da primeira entrada OAM.
- A mesma fonte identifica os índices cumulativos de sprite em WRAM `$40E0` e
  `$4958`; a implementação não usa uma grade fixa de doze tiles.
- O repositório de disassembly lista os binários
  `GFX_Sprite_Player_Side_Running1..10.bin` e suas tabelas de ponteiros em
  `AssetPointersAndFiles.asm` (linhas 5752–5801). Os tamanhos variam de 384 a
  512 bytes, o que por si só invalida a hipótese de doze tiles fixos.
- `issd-native/ISSDNative/issd_animation.c` identifica a rotina de corrida:
  script `$CF9F`, oito keyframes e ponteiros por direção em banco `$82`.
  Na ROM USA local, os oito scripts resolvem para descritores reais
  `$A6B9..$A818`, conforme a direção. A associação de cada índice de direção
  com o rótulo humano “lateral” ainda exige captura de RAM durante a partida.
- `issd-native/ISSDNative/issd_widescreen.c`, função `prepare_player`, mostra
  que cada descritor contém pose, fonte de duas linhas de gráficos e detalhe de
  uniforme. Para corrida, a pose aponta para geometria dinâmica em WRAM;
  portanto os deslocamentos X/Y não podem ser deduzidos fielmente apenas da ROM.

## Rotas de dados confirmadas

| Etapa | Fonte | Evidência |
| --- | --- | --- |
| Script de corrida | banco `$82`, `$CF9F` | `issd_animation_running_pair` |
| Descritor atual | `object+$14` | `prepare_player` |
| Gráficos dinâmicos | duas linhas prefixadas por tamanho | `prepare_player`, destinos relativos `$6000` e `$6100` |
| Geometria OAM dinâmica | WRAM `$2000/$4000/$6000` | `camera_piece` / `issd_running.c` |
| OAM final | buffer `$7E01E0`, 128 entradas + high OAM | `RAM_Map_ISSD.asm` |

## Formato do descritor de jogador

O valor de 16 bits em `object+$14` indexa um registro de **nove bytes** em
`DATA_82:A3D7`, no banco `$82`. Os bytes `0..1` formam o ponteiro da
pose/geometria; os bytes `2..4` são uma fonte de 24 bits para duas linhas de
gráficos prefixadas por tamanho; o byte `5` seleciona o caminho de detalhe de
uniforme/número. Os bytes `6..7` e `8` fazem parte do registro, mas não têm
semântica final atribuída neste projeto. A rotina original `84:E6C7` prepara
os registros de transferência, e
`issd-native/ISSDNative/issd_widescreen.c::prepare_player` valida a mesma
estrutura antes de reapresentar uma pose.

Cada linha começa com uma word de tamanho. Para a composição validada, cada
tamanho precisa ser não-zero, par e no máximo `$0100`; as linhas são carregadas
nas regiões dinâmicas de VRAM `$6000` e `$6100`. A geometria não está nesses
primeiros seis bytes consumidos por `84:E6C7`: ela vem da pose e das entradas
OAM do mesmo frame. Portanto um
renderizador fiel deve receber, no mínimo, descritor, duas linhas de tiles,
peças OAM e banco de paleta; um recorte de tiles isolado nunca é suficiente.

O byte de detalhe é dependente de campos do ator (tipo, seletor de uniforme,
variante e flags). `render_issd_descriptor_sprite.py` replica somente os
caminhos já observados e mantém o caminho especial de cabelo tipo 8 bloqueado
até haver captura correspondente. Não substituir esse detalhe por recoloração
CSS ou por um número desenhado pelo navegador.

## Renderizador estrito

`tools/render_issd_descriptor_sprite.py` monta uma pose usando:

1. o descritor real da ROM para reconstruir as duas linhas de tiles;
2. partes OAM observadas (`x`, `y`, `tile`, `size` e `attr`, ou campos
   separados de paleta, prioridade e espelhamentos);
3. a paleta de uniforme de 16 cores já extraída da ROM.

Ele exige `"evidence": "runtime-oam-capture"` no JSON e falha se uma parte
usar tile fora das faixas dinâmicas `0..7` e `16..23`. Isso impede a criação de
coordenadas ou animações inventadas.

## Captura de partida — 2026-10-27

Foi capturado um frame de uma partida real em
`docs/issd-runtime-player-compositions.json`. A captura contém 16 atores,
cada um com partes OAM, atributos finais, paleta, prioridade e espelhamentos
já resolvidos pelo jogo. As entradas não seguem uma grade 3×4: há poses com
4, 5, 6 ou 7 partes, com peças de 8×8 e 16×16.

Entre os descritores observados estão `$A749`, `$A752` e `$A77F`, que
pertencem à sequência de corrida documentada no script `$CF9F`. Isso confirma
que a ferramenta lê descritores e geometria reais, em vez de coordenadas
inventadas. A amostra, porém, contém apenas um instante de cada ator; não é
uma sequência temporal validada de oito poses laterais.

Teste executado: todos os 16 descritores capturados foram lidos da ROM USA
local pelo `tools/render_issd_descriptor_sprite.py`; cada um apresentou duas
linhas de dados válidas, entre 192 e 256 bytes. O teste deliberadamente não
emitiu PNG final, pois o ciclo lateral completo e sua validação visual ainda
não foram capturados.

## Ciclo lateral validado — direção observada `0`

O traço posterior, `docs/issd-match-trace.jsonl`, registrou 60 amostras de
partida, com 17–19 atores ativos por amostra. Para o ator `$0F00`, ele contém
os oito descritores em ordem: `$A749`, `$A752`, `$A75B`, `$A764`, `$A76D`,
`$A776`, `$A77F` e `$A788`, nos frames 56, 60, 64, 66, 70, 74, 76 e 80.
Essa é uma sequência temporal completa do script `$CF9F`, não uma animação
inferida.

`tools/export_issd_running_cycle.py` reproduz a exportação transparente a
partir da ROM local, do traço OAM e da CGRAM capturada no mesmo jogo. O PNG
`docs/issd-running-side-runtime-preview.png` foi gerado por essa ferramenta;
seu JSON irmão preserva o descritor, pose, paleta e partes de cada quadro.
O renderizador usa o banco de paleta indicado por cada atributo OAM, portanto
cabelo/detalhes não recebem uma recoloração de navegador.

## Caminhada validada — direção observada `0`

O mesmo traço contém um ciclo completo de caminhada, distinto da corrida:
`$A48B`, `$A494`, `$A49D`, `$A4A6`, `$A4AF`, `$A4B8`, `$A4C1`, `$A4CA`,
`$A4D3` e `$A4DC`. O ator `$0C00` forneceu os dez keyframes observados. A
prévia transparente correspondente está em
`docs/issd-walking-side-runtime-preview.png`. O exportador aceita agora
`--cycle running` ou `--cycle walking`; em ambos os casos a lista vem da ROM e
a montagem vem da captura OAM, sem preencher poses ausentes.

## Corrida validada — direção observada `6`

O ator `$0E00` também percorreu os oito descritores de corrida da entrada de
direção `6`: `$A6B9..$A6F8`. A montagem resultante está em
`docs/issd-running-direction-6-runtime-preview.png`. Ela usa composição
própria de direção (não é uma imagem espelhada da direção `0`).

## Corrida validada — direção observada `7`

O ator `$1700` forneceu o ciclo completo da direção `7`, descritores
`$A701..$A740`, exportado em
`docs/issd-running-direction-7-runtime-preview.png`. O exportador agora exige
que `actor.direction` coincida com `--direction`; direções que compartilham
uma tabela de descritores continuam separadas até que sua geometria OAM tenha
sido observada.

## Corrida validada — direção observada `1`

A coleta passiva de 600 frames forneceu o ciclo de oito poses da direção `1`
para o ator `$0E00`, exportado em
`docs/issd-running-direction-1-runtime-preview.png`. A coleta contém uma
linha JSONL interrompida; o exportador registra e ignora explicitamente essa
linha, mantendo as 300 amostras íntegras como evidência.

## Cobertura concluída de locomoção

O estado acima foi superado pelas coletas posteriores e pela exportação em
lote. `tools/validate_issd_locomotion_assets.py` valida 1.152 folhas RGBA
derivadas da ROM: 36 equipes × 2 uniformes × caminhada/corrida × 8 direções.
Cada folha é composta por descritor real, linhas de tile carregadas da ROM,
partes OAM e banco de paleta, não por uma grade fixa. O navegador pode usar
essas folhas somente para locomoção; a conversão entre vetor de tela e índice
da folha ROM está documentada em `issd-animation-inventory.md`.

O repositório de referência `web-snes-issd-studio`, em
`src/rom/graphics.mjs`, confirma a mesma estrutura no `spriteResource`:
duas linhas dinâmicas são enviadas a VRAM `$6000/$6100`; OAM fornece posição
assinada, tamanho 8/16, atributo/paleta e flips, preservando a precedência da
primeira entrada. Isso é compatível com o renderizador estrito local, mas não
substitui a evidência de cada ação.

## Pendente de captura

- Composição temporal completa e validada para passe, chute, cabeceio,
  carrinho/levantar e todas as defesas do goleiro.
- Correlação de cada ação com as transições de gameplay, bola e regras; uma
  imagem isolada não autoriza uma animação jogável.
- Qualquer gráfico de cabelo/detalhe que siga caminho alternativo não coberto
  pela composição observada deve permanecer bloqueado até haver OAM e paleta
  do mesmo frame.

## Estado do renderizador antigo

`tools/render_issd_sprites.py` desenha os primeiros doze tiles em grade 3×4.
Ele é útil como diagnóstico de planos 4bpp, mas não é uma composição fiel de
OAM e não deve ser usado como fonte de folhas de locomoção ou ações finais.
