# Captura de OAM final para chute e passe

A amostra `docs.rar` de 30/10/2026 apresentou 41 snapshots, dos quais 34 poses paradas foram recompostas. As 7 amostras `$D007`, `$D100` e `$DB5B` utilizam geometria estática/compactada (ponteiros `$80E4`, `$81F8`, `$8AD2`, `$89EC`, `$96A2`), interpretada indevidamente como os planos dinâmicos de WRAM. Elas possuem VRAM e CGRAM, mas o OAM relativo de ator NÃO está correto.

## Nova estratégia

`tools/capture_issd_native_action_oam.lua` grava, no callback do mesmo frame, os 544 bytes **brutos** do espelho OAM `$7E:01E0`, os 64 KiB de VRAM, CGRAM, registrador OBJSEL, dados do ator, e, se disponível, OAM do domínio PPU e screenshot. A ferramenta não reproduz a leitura errada `pose + índice` em `$2000/$4000/$6000`. Registros OAM abrangem TODO o quadro (bola, jogadores, etc.): ainda é preciso associar OAM ao ator em uma análise posterior. Cada pose pode ser amostrada duas vezes, para ajudar a verificar a temporização. É uma coleta passiva, sem alterar input, ROM ou RAM.

## Execução no BizHawk

1. Salve seus resultados anteriores antes de repetir a captura e ajuste `root` no início do script, garantindo que o caminho exista.
2. Entre em uma partida e carregue **somente** `tools/capture_issd_native_action_oam.lua` no Lua Console. Não use simultaneamente o capturador antigo.
3. Execute chutes baixos, chutes fortes, carrinhos e levantamentos em direções diferentes. O coletor termina em 18.000 frames (~5 minutos em 60 fps) ou 160 snapshots, o que acontecer primeiro.
4. Aguarde no console `ISSD native action OAM written` e compactar `issd-native-action-oam.jsonl` com todos os arquivos `issd-native-oam-*`.
5. Execute o validador (com Python): `python tools/validate_issd_native_action_oam.py docs/issd-native-action-oam.jsonl --output analysis/issd-native-oam-validation.json`.

## Limites importantes

- OAM final fornece o desenho efetivo, mas não identifica automaticamente a lista de peças de cada ator. É necessário conferir a posição do ator na tela e agrupar as peças após a captura.
- Ainda não é correto chamar `$D100` de passe: apenas há associação de descritores com assets `LowKick`.
- A screenshot usa a API do BizHawk; sua disponibilidade é registrada, sem invalidar o dump se a imagem não puder ser salva.
- O script verifica a disponibilidade do domínio `OAM` e preserva o espelho mesmo quando o domínio não existe.
- O dump binário serve para a etapa de análise; **não** é uma spritesheet HD ainda.
