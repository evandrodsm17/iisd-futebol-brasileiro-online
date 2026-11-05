# Comparação da condução: navegador vs ISS Deluxe nativo (2026-10-30)

## Teste reproduzido

`tools/compare_browser_dribble.mjs` simula exatamente 150 frames em unidades do motor Canvas: 60 para direita (velocidade 2), 30 para cima, 30 para esquerda e 30 parado. Reconstrói o algoritmo **anterior** à PR #18 e usa o módulo `dist/dribble-contact.mjs` da PR #18 no teste **atual**.

| Medida | Modelo antigo | Modelo atual |
| --- | ---: | ---: |
| Perda de posse no teste | frame 11 | não ocorreu |
| Distância no frame 30 | 44,513 | 9,941 |
| Distância no frame 60 | 48,782 | 9,941 |
| Distância no frame 120 | 166,583 | 9,941 |
| Distância no frame 150 | 166,583 | 11,424 |

O ganho é **interno ao protótipo web**. A versão atual não precisa ser redefinida para reproduzir velocidades não validadas.

## Referência nativa existente

`docs/issd-natural-play-trace.jsonl` tem cerca de 78 MB (9000 amostras), e `tools/capture_issd_match_trace.lua` mostra os campos da coleta: `ball.x/y/z` em `$0408/$040C/$0410`, `carrier` em `$1B90`, atores `$0500..$1A00` e `selected_p1` em `$1ACC`. O conector GitHub atual não retornou o conteúdo desse arquivo grande. **Não foi calculada distância nativa real nesta etapa.**

`tools/analyze_issd_native_dribble.py` lê o JSONL progressivamente, associa os endereços do possível portador aos atores, calcula distâncias sem conversão e informa proporção de amostras sem correspondência. Seu campo `carrier` é um candidato a ponteiro; sua semântica de posse ainda precisa de confirmação.

### Executar

```bash
node tools/compare_browser_dribble.mjs
python tools/analyze_issd_native_dribble.py docs/issd-natural-play-trace.jsonl --output docs/issd-native-dribble-summary.json
```

Depois de obter o resumo, validar que `carrier` corresponde à posse real, distinguir dribles de chutes e bolas aéreas, e recuperar um fator geométrico de conversão ROM→Canvas antes de qualquer tentativa de calibrar os offsets do pé.

**Nenhuma constante de física da partida foi alterada nesta PR.**

## Auditoria local — 01/11/2026

**Complemento posterior:** a hipótese de portador foi refutada estaticamente;
ver [issd-object-1b90.md](issd-object-1b90.md). O resumo agora usa schema v3,
sem associação de `$1B90` a um jogador. O registro abaixo preserva a sequência
da auditoria de coordenadas, mas não valida essa hipótese antiga.

A captura foi agora processada localmente: 78.026.699 bytes, 9.000 amostras,
último frame 18.000. O resumo reproduzível está em
`docs/issd-native-dribble-summary.json`, com SHA-256 e caminho da entrada.
`carrier` contém somente 0 (6.980 amostras) e 21896 / `$5588`
(2.020 amostras). Nenhum desses valores identifica um slot de jogador
`$0500..$1A00`, passo `$100`. Portanto esta coleta não confirma posse.

Foi encontrado também um erro no comparador recém-adicionado: o coletor grava
`ball.x/y` de `$0408/$040C`, mas `actors[].x/y` de `+$2A/+$2C`.
Esses últimos são coordenadas derivadas: `80:D31A` calcula
`2C = 009A + 0C` e `2A = 0098 + 08 - 2C` (ver
`docs/issd-static-mechanics.md` e `tools/capture_issd_match_trace.lua`).
Subtraí-las diretamente das coordenadas da bola produz uma distância sem
significado geométrico. A mediana 243,526 obtida antes da correção é inválida
para calibrar condução e não deve ser usada.

O analisador v2 exige `world_x/world_y` dos jogadores, lidos de `+$08/+$0C`.
O coletor passou a exportar esses campos adicionais, preservando `x/y` para
os consumidores gráficos. Na captura antiga há 8.894 amostras com atores,
mas nenhuma com esses novos campos; as estatísticas de distância ficam vazias,
explicitamente, sem reconstrução inventada. O script Lua foi alterado no código,
mas ainda não executado no BizHawk nesta etapa.

Validação: quatro testes em `tools/test_native_dribble.py` cobrem rejeição de
coordenadas antigas, distância 3–4–5 usando coordenadas originais, exclusão de
NaN e rejeição de frames repetidos. Também passaram
`node tools/test_dribble_contact.mjs` e `node dist/test-gameplay-actions.mjs`.
Nenhuma constante do motor web foi alterada.

Próxima etapa: localizar estaticamente a referência real de posse e procurar
outras capturas existentes com `+$08/+$0C` de bola e jogador no mesmo frame.
Só depois comparar geometria e converter unidades para o Canvas. Não é
necessário solicitar outra sessão manual antes dessa investigação.


## Medições em replays controlados — novembro de 2026

Os replays locais usados na captura de chutes também contêm movimento anterior ao comando. `tools/audit_issd_dribble_replays.py` lê a bola em `$0408/$040C` e o ator em `+$08/+$0C`, na mesma representação nativa; calcula diferenças com wrap de 16 bits. Foram incluídas amostras com bola em altura zero, `$00A6=$1900` e ator `$1900` associado ao segundo controle, durante entrada direcional. A relação de `$00A6` com posse continua sujeita ao contexto; o filtro é uma evidência operacional, não uma prova de todas as regras de condução.

O relatório [issd-dribble-replay-offsets.json](issd-dribble-replay-offsets.json) inclui hashes e estatísticas por entrada. Nas amostras para direita, a distância inteira do centro do ator à bola teve mediana 13 e percentis 10/90 de 10 e 15 unidades nativas; para baixo, mediana 8,485 e percentis 7,071/11,314. O conjunto da diagonal superior direita contém apenas duas amostras. As medições mostram variação na posição relativa, mas incluem aceleração, mudanças de direção e replays que compartilham a mesma trajetória inicial; não são amostras independentes nem distinguem caminhada de corrida. São distâncias entre origens lógicas, não necessariamente entre o pé visível e o centro da bola.

Os campos fracionários da bola não foram registrados neste trace, e as unidades e eixos ainda não foram calibrados contra o Canvas. Não é seguro transferir esses valores diretamente nem concluir que a distância web deva aumentar. A condução da web permanece provisória; o próximo passo é capturar posição fracionária da bola e do ator, velocidade e fase de animação por quadro, em sequências isoladas de caminhada e corrida, seguidas de comparação visual e geométrica. Teste do analisador: `python tools/test_issd_dribble_replays.py`.

O coletor `tools/automate_issd_probe.lua` agora inclui os words fracionários `$0406/$040A/$040E` da bola e aceita `ISSD_AUTO_DRIBBLE_EVERY_FRAME=1` somente em replay isolado. Um replay de validação gerou 120 amostras consecutivas de entrada para direita com os três campos presentes. Isso verifica a coleta, não valida sozinho a conversão geométrica, as unidades ou a equivalência de física. A opção não escreve na memória emulada; o arquivo de ROM permanece intacto.
