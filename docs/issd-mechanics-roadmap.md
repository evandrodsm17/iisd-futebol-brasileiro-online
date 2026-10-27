# Roteiro de mecânica fiel — ISS Deluxe

## Pontos de entrada confirmados

| Sistema | ROM / RAM | Papel |
| --- | --- | --- |
| Fase principal | `$7E:00C0` → `$83:CF86` | Dispatch de 15 fases da partida |
| Fase secundária | `$83:F375` | Continuação do dispatch de fase |
| Colisão/física | `$83:D77F` | Modos de colisão e bola |
| Trajetória | `$83:D9A5` | Bola, trave e rede |
| Mergulho GK | `$83:DCAA` | Defesa baixa/alta do goleiro |
| Captura GK | `$83:DDA1` | Segurar e proteger a bola |
| Sequenciador de jogador | `$84:A35F` | Seleção/composição de animação |

## Ordem de reconstrução

1. Registrar fase e registros de bola/jogador ao longo de jogo natural.
2. Substituir posse e bola livre pelo modo de colisão observado.
3. Ligar passe/chute às trajetórias observadas.
4. Integrar goleiro, rede e trave.
5. Tratar faltas, reinícios e cartão pelo dispatch de fase.

Nenhuma etapa promove uma regra do protótipo a comportamento final sem uma
rotina, tabela ou captura correspondente da ROM USA.

O código web atual mantém bola livre, posse por proximidade, atrito, quique e
reinícios apenas para que a tela de partida seja navegável. Eles não são
equivalentes à máquina da ROM e devem ser substituídos — e não ajustados por
sensação — conforme os handlers e registros forem recuperados.

## Projeção e geometria confirmadas para a próxima telemetria

O capturador passivo passa a registrar `stadium.layout` em `$7E:0086`, o
comprimento/largura nativos em `$7E:12A2/$7E:12A4` e a origem de câmera em
`$7E:13A0/$7E:13B0`. A alteração corrige a leitura anterior de câmera em
`$00A0/$00A2`, que não era a origem de visualização do jogo.

O leitor de recursos do `issd-native` confirma que os oito layouts originais
usam comprimentos `1792, 1856, 1984, 2048, 1920, 1920, 1792, 2176` e larguras
`576, 640, 704, 640, 640, 576, 704, 704`, extraídos da tabela ROM
`$81:EC47`. Esses valores serão usados apenas depois de aparecerem numa nova
telemetria; não serão aplicados retroativamente ao traço que não os registrou.

`tools/extract_issd_stadium_geometry.py` valida essa tabela diretamente na
ROM USA headerless e grava apenas os pares decodificados em
`dist/data/issd-stadium-geometry.json`. A ROM e seus bytes não entram no
repositório nem na distribuição web.

Os oito previews visuais extraídos estão em
`dist/assets/issd/stadium/layout-0.png` até `layout-7.png`, cada um com seu
manifesto de MD5/layout/dimensões. Eles ficam disponíveis para a futura
seleção de estádio validada pelo fluxo da ROM; a partida web continua usando o
layout 0 até que essa seleção esteja recuperada.
