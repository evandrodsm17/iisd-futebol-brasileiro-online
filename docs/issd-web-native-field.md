# Dimensões nativas na versão web

O módulo `dist/native-field.mjs` usa os oito pares de `81:EC47`, já
comparados com a ROM local. A escolha do estádio altera largura e altura
do campo proporcionalmente ao par nativo. O estádio USA conserva 1150×523
unidades Canvas como referência de compatibilidade. Essa escala e a projeção
visual permanecem provisórias; não são medidas em metros ou pixels SNES.

Ao trocar o estádio, jogador, bola, câmera e posições-base preservam sua
posição relativa no campo. O centro é recalculado. A textura selecionada
continua usando o recorte existente. Velocidades, tamanho dos jogadores,
gols, IA e regras não foram recalibrados nesta etapa.

Verificação: `node tools/test_native_field.mjs` testa a referência USA,
proporção de outro estádio, índice inválido, posição central e ida/volta
da troca. `node --check dist/game.js` verifica sintaxe. A inspeção visual no
navegador ainda está pendente. A integração de movimento fracionário e
projeção vetorial nativa ainda não foi implementada.
