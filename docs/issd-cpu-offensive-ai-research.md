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


## Nova descoberta estática: roteamento da dificuldade para equipes

Acesso realizado diretamente ao blob completo da disassembly (3.164.510 bytes) e à tabela de modos. Em `CODE_83:C3C3`, o valor de `NumberOfPlayersSetting` seleciona dois bytes adjacentes de `DATA_81:AEEF`. Cada byte vale `$00` (modo humano) ou `$02` (modo CPU). Após atualizar o bit 1 do campo local `$A4`, `CODE_83:C431` escolhe entre `LDX #$0002` e `LDX CurrentGameLevel`; o valor é escrito em `$CC` do registro direto da equipe (`$0D00/$0E00`).

| Modos numéricos | Lado 0 | Lado 1 |
|---|---|---|
| 0–3, humanos contra CPU | `$CC=2` | `$CC=CurrentGameLevel` |
| 4–7, humanos contra humanos | `$CC=2` | `$CC=2` |
| 8, CPU contra CPU | `$CC=CurrentGameLevel` | `$CC=CurrentGameLevel` |

Isto demonstra **roteamento de parâmetros** para os dois lados, mas `$CC` não pode ainda ser promovido a “agressividade” ou “precisão de chute”. Há pelo menos uma leitura do `$CC` em `CODE_85:B18B`, mas o contexto e seus efeitos precisam de inspeção adicional.

## Gerador pseudoaleatório

`CODE_85:83F3` opera sobre `$1FEA/$1FEC` com `ROR`, `ADC` e troca de estado. Os wrappers `85:8409/8411/8419/8421` mascaram a saída com `1,3,7,15`, respectivamente. A varredura estática localizou **55 chamadas diretas** à rotina central: 20 em banco `85`, 15 no `8A`, 11 no `8C` e 9 em `A4`. O índice está em `dist/data/issd-offense-callsite-index.json`.

**Não significa que as 55 chamadas pertençam à IA ofensiva.** O índice registra endereços de chamada, não atribui intenções. Foi encontrado também um conjunto de 22 chamadas diretas ao cálculo angular `CODE_80:F46D`, dos bancos `80`, `84` e `98`.

## Correção de interpretação de D007/D100

`CODE_84:B9A0` extrai o bit 0 de `$6E`, desloca-o duas vezes para `$2E` e invoca `CODE_80:DD82`. Este calcula `X` a partir do deslocamento de `$2E` e do campo `$5A`. O teste `CPX #$0005` seleciona `DATA_82:D007` para valores menores e `DATA_82:D100` para valores maiores/iguais. Este é um **seletor de script de animação**: não identifica por si só botão de passe, tipo de chute ou decisão da CPU. Nosso uso visual de D100 para passe permanece provisório.

## Verificação e próxima captura

```bash
python tools/verify_issd_cpu_difficulty_routing.py
```

O verificador relê o assembly local, compara a tabela de nove modos, os blocos de atribuição de dificuldade, o PRNG e o limiar do seletor com `dist/data/issd-cpu-difficulty-routing.json`. Ele falha se uma dessas evidências mudar.

`tools/capture_issd_cpu_offense.lua` foi ampliado com `side_flags_a4`, `team_CC` e `prng_words`; `tools/report_issd_cpu_offense.py` agora preserva esses valores nos eventos. Executar com **CPU × CPU** em diferentes dificuldades, repetindo o mesmo cenário quando possível. Comparar mudanças de rota da bola e visualização no BizHawk antes de vincular ações a decisões.

Nenhuma constante de IA do navegador foi alterada nesta PR; o experimento continua pendente de execução no emulador.
