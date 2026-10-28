# Próxima captura passiva — chute forte e composição completa

## Objetivo

Completar a evidência da rotina de chute forte já identificada como
`$82:D007` e das poses paradas `$82:D320/$82:D6DB`. As sequências estáticas e
alguns descritores existem, mas uma folha fiel ainda exige que cada pose tenha
OAM, VRAM e CGRAM do **mesmo frame**. Passe, carrinho e goleiro permanecem
fora da validação final desta sessão.

## Procedimento manual no BizHawk

1. Preserve/renomeie manualmente qualquer
   `docs/issd-action-vram-trace.jsonl` que queira guardar: o coletor inicia um
   novo arquivo nesse caminho.
2. Abra uma partida real e deixe o jogo em campo. Não é necessário pausar ou
   abrir ferramentas de memória.
3. No Lua Console, carregue
   `tools/capture_issd_action_vram.lua` e execute-o uma única vez.
4. Jogue normalmente por até 300 segundos, priorizando vários chutes fortes
   com direções diferentes. Quando estiver com a bola, pare brevemente nas
   direções que o jogo permitir; isso coleta `$D320/$D6DB` sem injetar
   controles. O script não escreve na ROM nem na RAM.
5. Ao término, aguarde a mensagem `ISSD action VRAM trace written` no console.
   Não reinicie o script durante a mesma sessão: ele deduplica por
   `script-direção-descritor`.

## Dados esperados

O script somente grava uma captura nova quando encontra scripts alvo
`$D007/$D100/$D320/$D6DB/$DB25/$DB5B`. Para cada descritor novo, salva:

- ator, `object_field_02`, script, direção, cursor, timer e duração de animação;
- partes OAM já resolvidas (`x`, `y`, tile, tamanho e atributo);
- VRAM completa e CGRAM do mesmo frame;
- `OBJSEL` capturado para interpretar tamanho e base de tile.
- fila DMA de VRAM nativa (`$7E:3200`, tamanho corrente em `$0048`), contendo
  fonte, destino em palavras, tamanho e parâmetros de cada registro pendente.

`object_field_02` é uma leitura crua de `ator+$02`. Ela foi acrescentada pois
`CODE_84:E6C7` usa `$02` ao formar o destino de VRAM das linhas dinâmicas. A
equivalência entre os dois contextos **ainda não foi observada**; portanto esse
campo não autoriza um renderizador a derivar offsets. A fila DMA é a fonte
preferencial para validar o endereço efetivo, pois é escrita pela rotina
nativa imediatamente antes do upload.

Como hipótese corroborada por uma implementação independente, o diagnóstico
também testará `($6000 + ((object_field_02 & $01FF) << 4))` em **palavras de
VRAM**. O resultado somente vira fato se houver igualdade byte a byte contra o
dump de VRAM da ROM local.

Para esta etapa, os registros de `$D007`, `$D320` e `$D6DB` são evidência de sucesso.
Registros de carrinho/levantar podem ser preservados, mas não serão promovidos
a folha final neste passe.

## Validação posterior

Depois que a captura estiver salva, o repositório deve:

1. verificar JSONL e pareamento de arquivos VRAM/CGRAM;
2. agrupar por `script + direção + descritor`;
3. usar `tools/render_issd_action_vram_capture.py` sem fallback de tiles;
4. comparar a cobertura observada com a tabela `$82:D007` antes de exportar
   qualquer spritesheet.

Para correlacionar as linhas gráficas com os registros DMA sem inferir offsets,
use também:

```powershell
python tools/analyze_issd_action_dma_queue.py <ROM.sfc> docs/issd-action-vram-trace.jsonl analysis/issd-action-dma-queue.json
```

O relatório só declara igualdade entre o endereço-fonte da linha do descritor
e uma entrada da fila. Fila vazia é resultado inconclusivo, pois pode ter sido
consumida pela NMI antes da leitura.

Ausência de uma pose, direção ou tile não é preenchida manualmente. Ela fica
marcada como pendente para a próxima sessão.

## Captura seguinte — controles e locomoção

Para relacionar controles à física, use separadamente
`tools/capture_issd_input_motion.lua`. O script espera 10 segundos sem gravar
e depois coleta 60 segundos do jogador selecionado, incluindo `joypad1`,
`held_p1`, `pressed_p1`, direção, script, estado, posição, velocidade e temporizadores.
Ele é somente leitura.

Durante os 60 segundos úteis, caminhe e corra nas oito direções, solte os
botões entre tentativas e execute alguns passes/chutes se ocorrerem
naturalmente. O objetivo primário é correlação de input e locomoção; ações
eventuais são apenas contexto. A saída é
`docs/issd-input-motion-trace.jsonl` e não substitui a captura VRAM de chute.

Após a captura, gere somente o relatório factual com:

```powershell
python tools/analyze_issd_input_motion.py docs/issd-input-motion-trace.jsonl dist/data/issd-input-motion-analysis.json
```

O relatório agrupa máscaras observadas e os valores de ator coexistentes; não
nomeia botões físicos ou ações por inferência. As direções candidatas são
expressas como valores internos da ROM e precisam manter sua proporção de
frames observados no artefato antes de orientar qualquer implementação.

## Varredura ampla — eventos que surgem naturalmente

Para descobrir o que pode ocorrer sem tentar encenar cada evento, carregue
`tools/capture_issd_animation_survey.lua` durante uma partida real. Ele espera
10 segundos e observa os 10 minutos seguintes. Para cada combinação inédita
de `script + direção + descritor` dos atores em campo, grava apenas metadados
em `docs/issd-animation-survey.jsonl`: fase, ator, posição, controles,
temporizadores, uniforme e pose.

O coletor não registra VRAM, CGRAM ou OAM e, portanto, não gera uma
spritesheet por si só. Sua função é listar a cobertura real e revelar scripts
que aparecem naturalmente — inclusive poses paradas com ou sem bola — para
que a próxima captura gráfica seja dirigida por evidência, não por tentativa
manual. Ele não injeta controles e não escreve em ROM/RAM.

Depois da mensagem de término, não sobrescreva o arquivo antes da análise. Os
scripts conhecidos de composição completa (`capture_issd_action_vram.lua`)
continuam sendo usados em uma segunda sessão para os scripts selecionados pela
varredura.

Gere o inventário factual com:

```powershell
python tools/analyze_issd_animation_survey.py docs/issd-animation-survey.jsonl dist/data/issd-animation-survey.json
```

Scripts sem correspondência estática permanecem sem nome no relatório. Eles
são candidatos para a captura de composição, não ações automaticamente
identificadas.
