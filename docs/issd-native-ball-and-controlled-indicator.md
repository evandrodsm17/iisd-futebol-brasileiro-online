# Sprite da bola e seta do jogador controlado

## Arte comprovada
A tela da partida não precisa mais representar a bola com dois círculos de Canvas. O arquivo `dist/assets/issd/ball/ball-original-8x8.png` foi extraído do tile nativo 4bpp da VRAM em `0xF0A0` (tile `0x785`), observado em `docs2.zip`. Nas 135 capturas OAM nativas os 32 bytes do tile são idênticos: `00000042007e0018007e00e700c30000000000662418003c24c3810000000000`.

Na captura `issd-native-oam-D007-0-A63B-0C00-114-screen.png`, na posição (202,133) da tela 256×224, os **32 pixels opacos** do PNG decodificado coincidem com o frame renderizado. Paleta utilizada do frame: índice 2 `#313031`, 6 `#B5B29C`, 8 `#EFE3CE`, 10 `#FF FBEF` (sem espaço: `#FFFBEF`). A fonte e o arquivo estão sujeitos à revisão dos direitos de distribuição dos assets da ROM.

A bola no Canvas continua usando o tamanho/posição visual provisórios e a física existente. A imagem nativa é exibida com nearest-neighbor, sem alteração do sistema de colisão ou do eixo vertical. Se a imagem não carregar, o desenho antigo permanece como fallback.

## Indicador do jogador
`drawPlayerIndicator` usa o próprio objeto `controlled` e a propriedade `roster.name`, que já recebem os nomes editados, as escalações e as transferências. Uma seta amarela e etiqueta acompanham o atleta durante o jogo. A opção `SETA + NOME / APENAS SETA / DESLIGADO` fica em `localStorage` `issd-controlled-player-indicator-v1`. É somente apresentação, sem introduzir um novo mecanismo de seleção.

## Testes
```bash
node tools/test_ball_indicator.mjs
node --check dist/game.js
```
É necessário confirmar a aparência no Chrome com bola no ar, troca de jogador, nomes longos e câmera em movimento. A identificação de sprite é baseada na captura gráfica e deve ser cruzada com a origem estática do tile na ROM em pesquisa posterior.
