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
