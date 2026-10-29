# Acumulação fracionária dos jogadores

`dist/fixed-motion.mjs` reproduz a soma de dois words com carry de
`80:D2B3`: soma word baixo, propaga carry, soma word alto, com wrap de 32 bits.
O controlador e o deslocamento dos demais jogadores em `dist/game.js` usam
esse acumulador. A bola continua no integrador provisório anterior.

O adaptador converte posição e delta Canvas para 16.16 por arredondamento.
Isso preserva passos fracionários, mas não prova equivalência de escala com
a ROM: aceleração, velocidade, coordenadas Canvas e limites continuam
provisórios. A projeção Mode 7 ainda não alimenta esse caminho. Reposições e
trocas de estádio são convertidas no próximo movimento; o desenho lê as
coordenadas decodificadas. Valores inválidos ou fora do domínio são rejeitados
antes de alterar os dois eixos.

`node tools/test_fixed_motion.mjs` cobre carry, subtração por complemento de
dois, wrap, soma de 256 frações, movimento negativo e falha sem escrita parcial.
Os testes de relógio/entrada e a verificação de sintaxe permanecem aplicáveis.
Ainda falta validação visual no navegador e comparação quantitativa com
deslocamentos capturados da ROM; esta mudança não calibra a velocidade.
