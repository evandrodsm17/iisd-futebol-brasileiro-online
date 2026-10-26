# Registro de referência — futebol arcade

Este documento separa **o que foi observado** do que ainda será medido. A ROM
local é utilizada somente para observação no BizHawk; nenhuma arte, música,
texto, código ou dado da ROM entra neste repositório.

## Evidência disponível

- ROM local carregada no BizHawk com o núcleo Snes9x em 26/10/2026.
- Arquivo de referência: 2.097.152 bytes; SHA-256
  `d2fe66c1ce66c65ce14e478c94be2e616f9e2cad374b5783a6a64d3c1a99cfa9`.
- O REA identificou a integridade do arquivo, mas não oferece descompilação da
  CPU 65C816 do SNES. A mecânica será catalogada por cenários reproduzíveis.

## Matriz de observação

| Área | Cenário | Medida que falta | Status |
| --- | --- | --- | --- |
| Movimento | corrida, inversão e diagonal | velocidade e desaceleração por frame | pendente |
| Bola | condução, passe e chute | distância da bola, impulso e atrito | pendente |
| Posse | contato entre jogadores | janela de roubo e recuperação | pendente |
| Câmera | bola no centro, laterais e gols | área visível e atraso de seguimento | pendente |
| Campo | escanteio, lateral, gol | reposicionamento e reinício | pendente |
| IA | sem comando e troca de jogador | marcação, apoio e seleção | pendente |

## Implementação web — decisões originais

- O campo é uma unidade lógica independente da resolução do canvas.
- A bola possui dono, velocidade e atrito; a posse muda por proximidade quando a
  bola está lenta.
- Cada lado tem 11 jogadores e regras simples de apoio/marcação.
- A câmera será longa por padrão e depois calibrada contra as observações, sem
  copiar arte ou recursos do jogo de referência.

Próxima revisão: preencher uma linha da matriz por vez com um cenário jogável
e gravar valores em unidades lógicas, não pixels de tela.
