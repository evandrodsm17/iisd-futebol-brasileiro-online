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

## Matriz de observação

| Área | Cenário | Medida que falta | Status |
| --- | --- | --- | --- |
| Movimento | corrida, inversão e diagonal | velocidade e desaceleração por frame | pendente |
| Bola | condução, passe e chute | distância da bola, impulso e atrito | pendente |
| Posse | contato entre jogadores | janela de roubo e recuperação | pendente |
| Câmera | bola no centro, laterais e gols | área visível e atraso de seguimento | pendente |
| Campo | escanteio, lateral, gol | reposicionamento e reinício | pendente |
| IA | sem comando e troca de jogador | marcação, apoio e seleção | pendente |

## Implementação web — decisões originais

- O campo é uma unidade lógica independente da resolução do canvas.
- A bola possui dono, velocidade e atrito; a posse muda por proximidade quando a
  bola está lenta.
- Cada lado tem 11 jogadores e regras simples de apoio/marcação.
- A câmera será longa por padrão e depois calibrada contra as observações.
- As folhas de jogador em `dist/assets/issd/` são PNGs gerados dos tiles de
  corrida da ROM local. `tools/render_issd_sprites.py` registra o passo de
  conversão 4bpp para PNG. O mapa de campo externo é somente referência
  temporária: a próxima etapa usa os blocos extraídos
  `GFX_Layer2_GrassySoccerField` e `GFX_Layer3_InGame_SoccerFieldMap`.
- Um jogador não é uma imagem plana na ROM: o corpo dinâmico é carregado em
  doze tiles 8×8 organizados em 3×4, e a composição final depende de entradas
  OAM (deslocamentos X/Y, tile, prioridade, paleta e espelhamento), além das
  camadas de cabelo e detalhes de uniforme. A adaptação web não deve tratar
  esses doze tiles como uma grade 4×3 nem substituir a paleta original.

Próxima revisão: preencher uma linha da matriz por vez com um cenário jogável
e gravar valores em unidades lógicas, não pixels de tela.
