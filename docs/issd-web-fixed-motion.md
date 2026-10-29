# Acumulação fracionária dos jogadores

## Paridade entre controle humano e IA

`movement-profile.mjs` centraliza caminhada (1,25; resposta 4,5) e corrida
(2,0; resposta 6). Tanto o jogador controlado quanto `steer` usam o mesmo
cálculo normalizado de aceleração. A IA seleciona corrida ao perseguir a
bola e caminhada nos demais deslocamentos; o humano seleciona corrida com
Shift. Os antigos valores exclusivos da IA (2,4/1,7) foram removidos.
São calibrações provisórias de Canvas, não velocidades recuperadas da ROM.
`node tools/test_movement_profile.mjs` verifica igualdade de deslocamento e
aceleração por 600 ticks nos dois modos, incluindo deslocamento diagonal.

## Comparação com a captura de 29/10/2026

`tools/compare_captured_motion.py` comparou 395.978 pares consecutivos de
ator/frame da sessão `113515`. Destes, 43.315 não mudaram de posição e foram
excluídos da contagem de coincidências. Nos 352.663 pares com movimento,
31.757 coincidem nos dois eixos com posição anterior + delta anterior;
29.999 coincidem usando o delta do frame atual. Essas contagens podem se
sobrepor e não devem ser somadas como cobertura independente.

O resultado está em `issd-motion-arithmetic-comparison.json`. A maioria dos
pares difere da soma isolada; snapshots ao fim do frame não determinam a
ordem interna, colisões, transformações ou mudanças de estado. Portanto este
teste não valida a equivalência física do navegador, nem autoriza calibrar
sua velocidade por uma razão global. A próxima investigação precisa
particionar as divergências por estado e cadência de atualização antes de
substituir os deltas provisórios.

Reprodução: `python tools/compare_captured_motion.py docs/issd-motion-constraints-20261029-113515.jsonl docs/issd-motion-arithmetic-comparison.json`.

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
