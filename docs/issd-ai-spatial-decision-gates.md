# Banco 84 — decisões espaciais e estado da bola no ISS Deluxe

## Descobertas verificadas pela disassembly

Foi inspecionado `Routine_Macros_ISSD.asm` (assembly 65C816) nos rótulos `CODE_84:C85D` a `CODE_84:CA54`, `CODE_84:E925` e nas tabelas da ROM.

### Três blocos de limites geométricos

A rotina `CODE_84:E925` compara valores de coordenadas com quatro palavras consecutivas carregadas de um bloco `DATA_81:CFxx`. Há um caminho que tenta três alternativas:

| Etapa | Chamada da rotina | Primeiras quatro palavras do bloco |
|---|---|---|
| 1 | `CODE_84:C8D1 → 84:E925` com `DATA_81:CFBF` | `000C,0018,000C,0018` |
| 2 | `CODE_84:C8F0 → 84:E925` com `DATA_81:CFE3` | `0020,0040,0020,0040` |
| 3 | `CODE_84:C918 → 84:E925` com `DATA_81:CFEF` | `0030,0060,0030,0060` |

Os pares formam parâmetros de comparação dos eixos, mas ainda não temos a transformação exata entre coordenadas do ator e coordenadas de tela. Não denominar os três caminhos como **passe/chute/cruzamento**. A rotina também consulta `CODE_80:F46D` (direção de alvo), `CODE_80:D058` e `CODE_80:D047`, altera campos `$6C/$6E` e retorna pelo roteador `CODE_84:C800`.

### Cinco entradas de parâmetros contextuais

No caminho `CODE_84:C868`, o valor `$00CC,Y` é duplicado para indexar **cinco entradas** das tabelas `DATA_81:C99D`, `DATA_81:CD40` e `DATA_81:CD4A`, com valores brutos registrados em `dist/data/issd-cpu-spatial-branches.json`. O significado do seletor ainda precisa de teste dinâmico.

**Atenção à ambiguidade de contexto:** `$00CC,Y` nesta rotina **não deve ser confundido** com `$0DCC/$0ECC`, cujo valor foi comprovadamente atribuído na inicialização de equipes conforme a dificuldade. A existência de `ADC.b $CC` em `CODE_85:B18B`, citada na investigação anterior, **não basta para atribuir esse uso ao campo de dificuldade** sem verificar o registrador Direct Page e o fluxo de chamada.

### Condições explícitas para altura da bola

No caminho `CODE_84:C950–CA50`, o código consulta `$0410` (posição vertical da bola) e faz comparações assinadas com `$FFC0` (-64) e `$FFA0` (-96). Essas condições contribuem para escolher entre estados e direções associados a `$1000`, `$2000` e `$4000` antes do roteador `CODE_84:C800`.

**O significado semântico das saídas segue desconhecido**: podem se referir a ações diferentes sobre a bola, e não necessariamente a cruzamentos ou arremates.

## Artefatos e verificação

- `dist/data/issd-cpu-spatial-branches.json`: tabelas exatas, rótulos, limites e cautelas.
- `tools/verify_issd_cpu_spatial_branches.py`: valida os blocos do assembly e o manifesto contra alterações futuras.
- `tools/capture_issd_cpu_offense.lua`: agora registra `spatial_tier_candidate`, `progress_candidate`, `state_flags_6e`, `v19c0`, `v19c4`, `v11f9` e `v1bac`, além das informações originais.
- `tools/report_issd_cpu_offense.py`: inclui os valores adicionais em cada evento e um histograma bruto da altura da bola.

Executar:

```bash
python tools/verify_issd_cpu_spatial_branches.py
# no BizHawk: executar tools/capture_issd_cpu_offense.lua em jogo CPU vs CPU
python tools/report_issd_cpu_offense.py issd-cpu-offense-trace.jsonl docs/issd-cpu-spatial-observations.json
```

As novas chaves não exigem alteração do motor de jogo e o trace permanece **somente leitura**. Executar partidas CPU contra CPU com diferentes dificuldades e correlacionar vídeo, trace e estados para distinguir passe, cruzamento, finalização, interceptação e reposicionamento.

## Próxima análise prioritária

Rastrear a origem das chamadas a `CODE_84:C85D` e `CODE_84:C950` e acompanhar o fluxo até o *script de animação efetivamente disparado*. Não modificar as heurísticas da IA do navegador antes de fechar esses caminhos com evidência de execução.
