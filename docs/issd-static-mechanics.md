# Mecânica estática confirmada — ISS Deluxe

Esta referência foi extraída sem executar a ROM: usa `Routine_Macros_ISSD.asm`
e `issd_symbols.h` do disassembly/nativo local.

## Dispatch de fase

`CODE_83CF7D` lê `$7E:00C0`, desloca o índice uma vez (`ASL`) e salta por
`DATA_83CF86`. A tabela possui 15 entradas (`0..14`). Na versão examinada,
o estado `3` aponta para `CODE_83CFA4`; os demais apontam para
`CODE_83CFAA`. Esses destinos são portas de guarda que retornam `carry`, não
uma descrição semântica suficiente para nomear cada fase. Portanto os nomes de
kickoff, lateral, falta etc. permanecem pendentes de correlação de fluxo.

## Dispatches físicos

| Sistema | Tabela | Quantidade confirmada | Função de dispatch |
| --- | --- | ---: | --- |
| Colisão/modo da bola | `$83:D77F` | 8 | índice dobrado e salto indireto |
| Trajetória/rede/trave | `$83:D9A5` | 6 | índice dobrado e salto indireto |
| Mergulho de goleiro | `$83:DCAA` | 3 | índice dobrado e salto indireto |
| Captura de goleiro | `$83:DDA1` | 9 | índice dobrado e salto indireto |

As contagens acima são estruturais; não atribuem nomes humanos aos subestados
sem uma referência adicional. Elas delimitam, porém, cada máquina finita que
o navegador precisará reproduzir para substituir a física provisória.

## Próximo trabalho offline

1. Percorrer chamadas e gravações do índice de cada dispatch.
2. Extrair constantes e registros RAM usados por cada handler.
3. Cruzar descritores de animação já resolvidos com os handlers, quando ambos
   coexistirem na telemetria natural arquivada.
