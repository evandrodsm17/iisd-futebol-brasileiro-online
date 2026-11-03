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
uniforme/número. `98:FB86` testa os bytes `6..7` apenas como condição não
nula e usa o byte `8` como seletor, emitindo outro DMA de 32 bytes. Porém,
`98:FB34` só o agenda em seis contextos auxiliares, não nos slots principais
de jogador; ele não compõe o atleta neste projeto. A rotina
original `84:E6C7` prepara os dois registros principais de transferência, e
`issd-native/ISSDNative/issd_widescreen.c::prepare_player` valida a mesma
estrutura antes de reapresentar uma pose.

O banco dessa transferência auxiliar não é deduzido: `DATA_81:ED6D` contém 13
bases de quatro bytes, de `DATA_97:CD58` até `+$2400` em saltos de `$0300`;
`98:FB86` as seleciona pelo contexto direto `$16`; o valor dos bytes `6..7`
não é usado como endereço. O agendador `98:FB34`
percorre seis contextos (`$0AA0`, `$0AD0`, `$0BA0`, `$0BD0`, `$0CA0`, `$0CD0`).
Em cada um, a rotina evita reenfileirar o DMA se `$001E` não for zero ou se o
descritor em `$0014` não mudou. Esses fatos descrevem atualização e fonte, não
identificam ainda qual parte desenhada recebe os 32 bytes, nem autorizam
associá-los a uma parte de jogador.

Cada linha começa com uma word de tamanho. Para a composição validada, cada
tamanho precisa ser não-zero, par e no máximo `$0100`; as linhas são carregadas
nas regiões dinâmicas de VRAM `$6000` e `$6100`. A geometria não está nesses
primeiros seis bytes consumidos por `84:E6C7`: ela vem da pose e das entradas
OAM do mesmo frame. Portanto um
renderizador fiel deve receber, no mínimo, descritor, duas linhas de tiles,
peças OAM e banco de paleta; um recorte de tiles isolado nunca é suficiente.

### Tile de geometria e tile OAM

**Confirmado em `80:95E0`/`80:9663`.** Para uma pose dinâmica, a geometria
em WRAM fornece o tile relativo em `$7E:6000 + pose + parte*2`. O construtor
de OAM adiciona `object+$02` antes de escrever o byte de tile de hardware.
Logo, as capturas novas preservam `geometry_tile` e `tile`: o primeiro serve à
recomposição local das linhas carregadas por `84:E6C7`; o segundo serve à
leitura da VRAM completa. Não é permitido trocar um pelo outro sem normalizar
o contexto do ator.

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

### Três estilos no mesmo cenário de partida — 03/11/2026

Os estilos 2 e 13 foram testados em duas instâncias isoladas a partir do
mesmo savestate do estilo 1. Em ambos, além do reposicionamento sintético do
ator, o seletor do contexto auxiliar foi alterado temporariamente em RAM e o
descritor anterior foi limpo para provocar nova transferência. Não foi feita
edição de ROM, savestate ou seleção normal no menu do jogo.

Para cada estilo, `tools/summarize_issd_hair_style_trials.py` confronta os
tiles de VRAM com o atlas da ROM e compara a composição corpo+cabelo com
OAM, CGRAM e screenshot. Em cada um dos três casos houve **13 de 19 quadros
com igualdade direta**; nos demais, as cores dos pixels divergentes
coincidiram com slots OAM anteriores, sem divergências restantes após essa
classificação. Essa coincidência sugere oclusão, mas não prova todo o
comportamento de prioridade. O relatório `issd-hair-style-trials.json`
registra contagens e hashes; as capturas permanecem locais.

Os três casos usam o mesmo ator, direção observada e banco OBJ 1. As folhas
web existentes foram exportadas como imagens já compostas e centralizadas por
quadro, sem expor ainda ao renderizador os pontos de ancoragem originais da
camada auxiliar. Portanto ainda não se deve simplesmente desenhar um cabelo
por cima delas: é preciso transportar as âncoras e a geometria em conjunto,
validar outras direções/paletas e então usar cache de quadros compostos.

### Revisão das sobreposições na composição — 03/11/2026

O experimento anterior posicionou o ator perto da borda inferior direita,
sobre elementos de interface. Uma segunda posição ficou sobre o minimapa e
não gerou quadros de composição completa exatos. Na terceira execução,
`ISSD_HAIR_POSITION_DX=-50` e `ISSD_HAIR_POSITION_DY=-100` reposicionaram
temporariamente o mesmo ator acima dessa interface, somente na RAM isolada.

Na terceira captura, **13 de 19** quadros tiveram correspondência direta
completa dos pixels candidatos de corpo e cabelo. Nos outros seis houve 71
pixels divergentes no total; todos coincidiram com a cor de pixels de slots
OAM anteriores à composição candidata. Isso é consistente com oclusão por
outros sprites, mas uma correspondência de cor não prova por si só toda a
prioridade de hardware ou exclui outras causas. O resultado completo, com
hash e posição sintética, está em `issd-hair-oam-clear-comparison.json`.

`tools/analyze_issd_hair_oam.py` agora registra essa classificação; a opção
`--allow-no-exact` permite investigar uma captura sem quadros diretamente
iguais, sem apresentá-la como validada. O teste reproduz os 13 quadros e a
contagem de 71 pixels. A evidência continua limitada a um ator, estilo e
paleta: próximos passos são validar outros cabelos e paletas no mesmo quadro
e construir a montagem dinâmica com cache para a partida.

### Composição de cabelo e corpo em partida — 03/11/2026

Para tornar visível o ator `$1700`, seu posicionamento foi alterado somente
na RAM de uma instância isolada carregada do estado salvo; a captura registra
as coordenadas anteriores e as artificiais. `tools/capture_issd_hair_runtime.lua`
capturou callbacks de `80:95E3`, OAM, VRAM, CGRAM e screenshots de quadros
consecutivos. A comparação em `tools/analyze_issd_hair_oam.py` associa os
intervalos da pilha ao contexto de cabelo `$0BD0` e ao corpo `$1700`, confere
o buffer preparado com o OAM da PPU do quadro seguinte e compara os pixels.

Nos 19 quadros analisados, os pixels candidatos da camada de cabelo
coincidiram com a screenshot e usaram o banco de paleta OBJ 1. Nos passos 7
e 8, a composição conjunta de corpo e cabelo coincidiu integralmente em
341 e 356 pixels candidatos, respectivamente; nesses casos, os 6 pixels
divergentes do corpo isolado coincidem quando a camada de cabelo é incluída.
Os slots de cabelo tinham índice menor que os do corpo, portanto prevalecem
na sobreposição desses quadros. Os 17 quadros restantes apresentaram
divergências na composição conjunta; a causa ainda não foi isolada.

O relatório é `issd-hair-oam-comparison.json`; imagens e dumps permanecem
locais em `analysis/`. A captura confirma a montagem de **duas amostras
sintéticas específicas**, não de todos os quadros ou uniformes. O comparador
não prova partes ocultas nem modela completamente prioridade, clipping e
oclusão. Próximo passo: identificar as divergências restantes e validar
outros estilos/paletas antes de ativar essa composição na partida web.

### Transferência de cabelo em partida — 03/11/2026

`tools/capture_issd_hair_runtime.lua` reproduziu o estado de partida em um
emulador isolado e observou os seis contextos de `98:FB34`, a entrada em
`98:FB86` e os tiles de VRAM após os quadros. Dois contextos estavam ligados
a atores ativos; somente o contexto `$0BD0`, ligado ao ator `$1700`, forneceu
descritores de locomoção e amostras de tile utilizáveis durante a janela.
Seu seletor `$16=0` aponta para a primeira entrada de `81:ED6D` (estilo 1).

`tools/analyze_issd_hair_vram.py` calculou, para cada descritor, a origem
`atlas + (byte_8 - 1) * 32` e o endereço da VRAM a partir do slot auxiliar.
Das 117 amostras, 81 coincidiam com a ROM no mesmo passo e 36 divergiam em
mudanças de descritor. Em 78 pares consecutivos com descritor estável, a
amostra seguinte coincidiu com os 32 bytes esperados; esses pares são um
subconjunto das amostras, não observações adicionais independentes. O relatório
`issd-hair-vram-audit.json` preserva o hash do trace local e os seletores sem
incluir os tiles. O teste rejeita corrupção em quadro estável e hook ausente.

Esse resultado confirma a fonte e o destino dos tiles para um contexto e um
estilo, mas não valida ainda a atribuição dos slots OAM, a ordem sobre o corpo,
a paleta nem os outros estilos. A diferença temporal observada exige parear
descritor e VRAM corretamente; não se deve presumir que todo frame divergente
seja um novo formato. Próximo passo: capturar OAM/CGRAM e a imagem de um quadro
estável desse ator e comparar a composição completa antes de ativá-la no jogo.

### Prévia interativa de edição — 03/11/2026

O editor local de catálogo oferece uma prévia giratória de oito direções e
uma janela de seleção com 14 opções de cabelo. O extrator local
`tools/export_issd_editor_preview.py` lê a ROM USA e grava dados indexados em
`dist/assets/issd/editor-preview-local.json`, ignorado pelo Git. O navegador
combina os tiles de cabeça, o quadro de corpo e as paletas; não recebe a ROM.
O extrator utiliza as poses de editor `81:ED1D/ED3D`, OAM de prévia
`98:8472/8B61`, cabeça `98:90CC`, descritores do banco 82 e atlas apontados
em `81:ED6D`. A troca de seleção atualiza a imagem sem persistir até salvar.

O verificador opcional `tools/verify_issd_editor_preview.mjs` comparou 2688
quadros e as cores de seus pixels com `playerPreviewFrames` do Web ISSD Studio
no commit `229ec0bce3fcee580a5990cce333456f0700be99`: seis equipes, jogador
de linha/goleiro, duas variantes, 14 estilos e oito direções. A comparação é
com a implementação de referência do editor, não com screenshot do jogo em
partida; o goleiro usa o gráfico de prévia próprio. Os estilos 0–13 e as duas
variantes permanecem códigos/paletas do original, não cores RGB independentes.
O recurso não muda a aparência dos jogadores durante a partida; essa
integração requer a validação de OAM/CGRAM e dos quadros de gameplay abaixo.

### Geometria auxiliar da locomoção — 03/11/2026

A prévia do editor de referência usa `DATA_9890CC` em `$7E:412C`; as poses
de partida não podem usar essa mesma origem indiscriminadamente. No fluxo
de partida, a lista `82:8C36` carrega recursos auxiliares como
`98:9109 → $7E:4E68` e `98:91B2 → $7E:4F0C`. Os bytes 6–8 dos descritores
de corrida/caminhada apontam para essas geometrias e selecionam um bloco do
atlas de cabelo. Por exemplo, o descritor `$A749` aponta para `$4F2C` e
seleciona o bloco 3.

`tools/capture_issd_hair_geometry.lua` leu as regiões de geometria do estado
de partida em instância isolada. `tools/extract_issd_hair_geometry.py`
descomprimiu os recursos da ROM, comparou posição, tile e atributos com
**167 entradas da WRAM**, sem divergências, e relacionou os **90 descritores
únicos** dos ciclos às suas geometrias e seletores. O resultado reutilizável,
sem gráficos de ROM, está em `dist/data/issd-hair-locomotion-geometry.json`;
a captura permanece local em `analysis/`. O teste também rejeita alterações
ou ausência de entradas no snapshot.

Isso confirma os dados de geometria carregados, não a imagem composta final:
continuam pendentes a associação da camada ao ator correto, o banco de paleta,
prioridade/espelhamento finais e a comparação de pixels no mesmo frame. O
próximo passo é capturar esses atributos OAM e a transferência de VRAM para um
jogador com cabelo especial, antes de habilitar a personalização na partida.

### Aparência no editor de referência — 03/11/2026

O repositório [Web ISSD Studio](https://github.com/EstebanFuentealba/web-snes-issd-studio)
foi consultado no commit `229ec0bce3fcee580a5990cce333456f0700be99`.
`src/rom/deluxe.mjs` lê o byte 6 do registro de sete bytes: nibble baixo é
o código de cabelo e nibble alto seleciona a variante de pele; `players.mjs`
edita cada nibble preservando o outro. A auditoria
`tools/audit_issd_appearance_editor.py` comparou o catálogo com os **720**
registros da ROM USA original: 619 usam variante 0, 101 usam variante 1;
os cabelos observados estão entre 0 e 13. O resultado e os 13 ponteiros de
atlas em `81:ED6D` estão em `issd-editor-appearance-audit.json`.

Segundo `src/rom/appearance.mjs`, o cabelo 0 usa o desenho padrão, e 1–13
selecionam fontes de atlas; o seletor de pele determina quais paletas usar.
As cores alternativas de pele/cabelo são lidas de registros por equipe
apontados pelas tabelas de offsets LoROM `0x1037C` e `0x103D2`. Uma cor
editada nesses registros pode afetar vários jogadores: o nibble não é um RGB
individual. O código de prévia `src/rom/player-preview.mjs` também mostra
uma camada de cabelo independente com dados de posicionamento; essa prévia
de editor não comprova sozinha sua composição em todos os frames da partida.

O editor local do catálogo agora permite salvar código de cabelo 0–13 e
variante de pele 0/1 em overrides, preservando compatibilidade com os registros
anteriores e sem alterar a ROM. **A partida ainda não aplica esses valores ao
sprite**: as folhas de locomoção atuais são selecionadas por equipe/uniforme,
e a montagem individual de cabelo, bancos de paleta e caminhos especiais
continua pendente de validação com capturas de gameplay. O próximo passo é
reproduzir a camada auxiliar usando descritor, geometria OAM e paletas do mesmo
quadro e confrontá-la pixel a pixel antes de ligá-la ao renderizador web.

### Candidatos de aparência do elenco

`tools/analyze_issd_appearance_candidates.py` gera
`dist/data/issd-appearance-candidates.json` a partir do catálogo da ROM. Ele
lista todos os valores efetivamente usados nos nibbles alto e baixo do byte
`06` dos 720 jogadores e define a cobertura mínima para uma futura captura:
ao menos um ator de runtime por valor observado. Os nomes `skin_tone` e
`hair_style` do catálogo continuam candidatos de decodificação; a análise não
os trata como seletor visual confirmado em gameplay. A investigação posterior
acima confirma o contrato usado pelo editor de referência, mas não todas as
consequências visuais durante a partida.

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
