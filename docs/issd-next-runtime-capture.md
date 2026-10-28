# Próxima captura passiva — chute forte e composição completa

## Objetivo

Completar a evidência da rotina de chute forte já identificada como
`$82:D007`. A sequência estática e alguns descritores existem, mas uma folha
fiel ainda exige que cada pose tenha OAM, VRAM e CGRAM do **mesmo frame**. O
primeiro alvo é o chute forte; passe, carrinho e goleiro permanecem fora desta
sessão para manter a análise delimitada.

## Procedimento manual no BizHawk

1. Preserve/renomeie manualmente qualquer
   `docs/issd-action-vram-trace.jsonl` que queira guardar: o coletor inicia um
   novo arquivo nesse caminho.
2. Abra uma partida real e deixe o jogo em campo. Não é necessário pausar ou
   abrir ferramentas de memória.
3. No Lua Console, carregue
   `tools/capture_issd_action_vram.lua` e execute-o uma única vez.
4. Jogue normalmente por até 300 segundos, priorizando vários chutes fortes
   com direções diferentes. O script não injeta controles, não escreve na ROM
   e não escreve na RAM.
5. Ao término, aguarde a mensagem `ISSD action VRAM trace written` no console.
   Não reinicie o script durante a mesma sessão: ele deduplica por
   `script-direção-descritor`.

## Dados esperados

O script somente grava uma captura nova quando encontra scripts alvo
`$D007/$D100/$DB25/$DB5B`. Para cada descritor novo, salva:

- ator, script, direção, cursor, timer e duração de animação;
- partes OAM já resolvidas (`x`, `y`, tile, tamanho e atributo);
- VRAM completa e CGRAM do mesmo frame;
- `OBJSEL` capturado para interpretar tamanho e base de tile.

Para esta etapa, os registros de `$D007` são a evidência de sucesso. Registros
de carrinho/levantar podem ser preservados, mas não serão promovidos a folha
final neste passe.

## Validação posterior

Depois que a captura estiver salva, o repositório deve:

1. verificar JSONL e pareamento de arquivos VRAM/CGRAM;
2. agrupar por `script + direção + descritor`;
3. usar `tools/render_issd_action_vram_capture.py` sem fallback de tiles;
4. comparar a cobertura observada com a tabela `$82:D007` antes de exportar
   qualquer spritesheet.

Ausência de uma pose, direção ou tile não é preenchida manualmente. Ela fica
marcada como pendente para a próxima sessão.
