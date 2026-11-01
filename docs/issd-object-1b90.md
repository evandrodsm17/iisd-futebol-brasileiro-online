# Correção da hipótese de posse em $1B90 — 01/11/2026

## Resultado

O campo antes chamado `carrier`/`carrier_candidate` nos coletores não pode
ser usado como ponteiro de posse. `$1B90` é usado como base fixa de um registro;
a palavra armazenada nessa base recebe valores literais/de tabela que não
pertencem aos slots de jogadores. O portador real continua não identificado.

## Evidência estática

Fonte: `YFs_InternationalSuperstarSoccerDeluxe_Disassembly/International_Superstar_Soccer_Deluxe/Routine_Macros_ISSD.asm`.

| Rótulo | Operação comprovada | Consequência |
| --- | --- | --- |
| `83:9BBE` | Consulta `DATA_81A7B3` por `$0430`; no caminho não zero e diferente de 1, grava literal `$5588` em `$1B90` | Explica exatamente o valor 21896 da captura antiga; não é identidade de jogador |
| `83:B6CF` | Grava `DATA_81ABAD,Y` em `$1B90`, `$0400` em `$1B92` e `$B000` em `$1B94` | Inicializa vários campos do registro |
| `81:ABAD` | Palavras `$56F8,$5704` | Outros valores possíveis não são slots de jogadores |
| `80:D953` | `LDY #$1B90`, depois compara `+$2A,Y` e `+$2C,Y` pelo caminho `D95B` | Usa o endereço como base de objeto, não o conteúdo como ponteiro |
| `80:E1DF/E1EA` | Testa `$1B90` contra zero; se ativo, carrega `$1B98/$1B9C` em `$40/$42` | A palavra habilita o uso de coordenadas do registro |
| `83:9B3F/9B83` | Calcula coordenadas a partir de posição e incrementos e grava `$1B98/$1B9C` | Há cálculo de posição associada ao registro; não prova posse |

É plausível que o registro represente uma posição antecipada da bola ou um
marcador associado. Essa interpretação visual **não está confirmada**. Não
denominar o valor como portador, receptor ou jogador selecionado.

## Correções dos instrumentos

- Relatório de condução v3 remove associação de `$1B90` a atores e velocidades
  filtradas por esse suposto portador. Preserva histograma bruto como
  `object_1b90_values_top`; aceita o nome legado `carrier` apenas na entrada.
- Relatório ofensivo v2 remove `carrier_matches_actor`, preserva a palavra
  como `object_1b90_word` e calcula proximidade somente com `world_x/world_y`
  dos jogadores e `x/y` da bola, todos vindos de `+$08/+$0C`.
- Coletor ofensivo v2 exporta essas coordenadas adicionais e o nome corrigido.
  O coletor natural mantém a chave legada por compatibilidade; seu conteúdo
  é somente a palavra bruta de `$1B90`, não posse.
- Nenhuma constante da física ou IA web foi alterada.

## Validação e limites

`python tools/verify_issd_object_1b90.py` verifica sete trechos contra o assembly.
`python -m unittest discover -s tools -p test_native_dribble.py -v` e
`python -m unittest discover -s tools -p test_cpu_offense_report.py -v`
validam rejeição de coordenadas incompatíveis, ausência de inferência de posse
e distância sintética 3–4–5. O resumo da captura existente foi regenerado.
O coletor Lua ainda não foi executado no emulador nesta etapa.

## Retomada

Investigar os escritores do estado da bola e os vínculos com atores sem
substituir `$1B90` por outro ponteiro apenas por proximidade ou nome presumido.
`$11E8` já é documentado como ponteiro ativo em fases específicas; isso não
prova posse. Confirmar um vínculo por escrita/leitura e geometria compatível
antes de conectar a lógica ao motor web.
