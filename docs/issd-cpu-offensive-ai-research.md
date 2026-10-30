# Investigação da IA ofensiva original do ISS Deluxe

## Conclusões sustentadas por código

- O nível de jogo é armazenado em `$7E:1E54` (`CurrentGameLevel`), com cinco escolhas `0..4`. Isso **não demonstra** que o nível altera a precisão de chutes ou a frequência de passes; exige identificar consumidores do setting.
- `CODE_80:F46D`, tabelas `81:9B3B/81:9B3F`, converte diferenças de coordenadas em índice angular de seis bits. É uma ferramenta de direção de alvo, **não** prova ainda da rotina de escolha do melhor companheiro.
- `CODE_84:B9A0` usa o índice retornado por `CODE_80:DD82` para escolher animação `D007` ou `D100`. Essas são ações visuais, não decisões ofensivas nomeadas por comando.
- `CODE_83:D980` e `DATA_83:D9A5` gerenciam até dois blocos de trajetória com seis estados nativos; não classificamos os índices como chute, passe ou cruzamento.
- `docs/issd-natural-play-animation-report.json` registra `D007` em 25 amostras e `D100` em 10 amostras, mas não verifica qual ator é CPU nem o destino da bola. O `focus-pass` observou 1 amostra D100; `focus-shot` observou 6 D007 e 3 D100. Esses nomes representam cenários de captura, não identificação automática das ações.
- Em `Misc_Defines_ISSD.asm`, `AnnouncerVoiceID_GreatCross = $000D` e `HeShoots1 = $002C`/`HeShoots2 = $0040` confirmam eventos de narração nomeados, mas não localizam as funções de decisão da CPU.

## O que permanece sem prova

Nenhum predicado original confirmado para: quando cruzar, qual jogador receberá o passe, quando arrematar, como o CPU avalia distância até o gol ou vantagem numérica, nem quais probabilidades variam por dificuldade. Não implementar heurística web como se fosse regra original da ROM.

## Novo experimento sem modificar a ROM

1. Abra o ISS Deluxe USA no BizHawk e selecione **CPU vs CPU** (`NumOfPlayers_CPU_VS_CPU = $0008`). Registre qual dificuldade foi escolhida e execute `tools/capture_issd_cpu_offense.lua` durante a partida.
2. Repita em diferentes dificuldades e, separadamente, em situações de ataque perto das laterais e do meio. Cada execução deve ter um nome de arquivo `output_path` diferente.
3. O capturador grava até **7.200 frames** em JSONL, todos os atores ativos, `$0408/$040C/$0410` para bola, `$0424/$0428/$0436` para velocidade, `$1B90` para possível portador, `$1ACC` para seleção P1, scripts/animações e fase de partida. Ele não injeta inputs.
4. Analise cada arquivo:
   `python tools/report_issd_cpu_offense.py issd-cpu-offense-trace.jsonl docs/issd-cpu-offense-observations.json`
5. Compare eventos `D007/D100` com mudanças de velocidade/posição no frame da ação. **Somente** depois associe um roteiro a passe rasteiro, bola aérea, cruzamento ou chute; a evidência visual deve coincidir.
6. Investigar os chamadores de `84:B9A0` e `80:DD82` e os consumidores de `1E54` na disassembly local para recuperar os limiares e tabelas decisórias reais.

## Importante

O trace natural arquivado de 78 MB não foi lido integralmente nesta execução via conector GitHub. A PR adiciona instrumentos para o experimento; **não afirma ter isolado uma decisão completa da CPU**. Não modifica IA da partida nem traz código de outros projetos.
