# Sprites HD próprios — importação JSON/PNG v1

Este recurso substitui apenas o desenho dos jogadores: não altera física, hitboxes, controles ou dados da ROM. Os arquivos importados ficam na aba atual e não são enviados ao servidor.

## Como testar

1. Sirva a pasta dist por HTTP, por exemplo: python -m http.server 8000 -d dist
2. Abra a aplicação, escolha a equipe no painel IMPORTAR SPRITES HD e selecione um JSON e os PNGs citados nele.
3. Clique APLICAR SPRITES. Inicie a partida para visualizar o resultado. Clique RESTAURAR ORIGINAIS para reverter.

## Formato

Cada animação possui seu próprio PNG, organizado em 8 linhas e N colunas. Cada célula é um frame transparente de dimensões frame_width × frame_height.
Ordem padrão das linhas: N, NE, E, SE, S, SW, W, NW. A propriedade direction_rows permite mapear a direção de tela para outra linha do PNG sem alterar a física.
animations aceita idle, walking e running, individualmente; ausências usam os sprites antigos. ticks_per_frame define duração em ticks de 60 Hz e pode ser um número inteiro ou lista com uma duração por quadro.
render.world_height define a altura visual do personagem; anchor_x e anchor_y alinham o quadro (incluindo os pés); offset_x e offset_y alteram só o desenho.

Modelo: dist/data/hd-sprite-pack.example.json. Com frames de 64×96, esse modelo espera idle.png com 64×768, walking.png com 640×768 e running.png com 512×768 pixels.

Os arquivos são carregados apenas no navegador, não persistem após recarregar e aplicam o mesmo personagem visual a todos os jogadores da equipe selecionada. Sprites por jogador e animações de ações são trabalhos futuros.

## Testes

node tools/test_hd_sprites.mjs
node tools/test_simulation_clock.mjs
node tools/test_native_field.mjs
node --check dist/game.js
