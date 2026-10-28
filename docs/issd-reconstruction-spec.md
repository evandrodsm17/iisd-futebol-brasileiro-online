# Especificação de reconstrução fiel — ISS Deluxe

Este documento é o contrato de implementação do jogo web. Ele consolida o que
um desenvolvedor pode reproduzir agora, o que deve permanecer isolado e a
evidência que falta para cada subsistema. O diário
[`issd-reverse-engineering-log.md`](issd-reverse-engineering-log.md) mantém a
cronologia; os JSONs em `dist/data/` são os contratos processáveis.

## Regra de implementação

1. Implementar somente comportamentos marcados **confirmados** e preservar a
   fonte indicada.
2. Para comportamento **parcial**, criar uma interface/estado explícito, mas
   não inventar transições, polaridades ou física.
3. Para comportamento **pendente**, manter o protótipo isolado e documentado;
   não usar como referência de fidelidade.
4. Câmera ampla, widescreen e multiplayer são extensões web. Elas não podem
   alterar a simulação de referência sem uma camada de adaptação explícita.
5. Clubes, temporadas, competições nacionais/sul-americanas e promoção/rebaixamento são extensões de produto guiadas por regulamentos versionados; elas usam o mesmo núcleo de partida, mas não são dados da ROM.

O escopo de produto completo está em `product-vision.md`.

## Fonte e regeneração

- ROM USA local: `International Superstar Soccer Deluxe/`; ignorada pelo Git e
  nunca distribuída.
- Disassembly de referência local:
  `C:\Users\evandro.mota\Documents\issd-disassembly-inspect\International_Superstar_Soccer_Deluxe\Routine_Macros_ISSD.asm`.
- Após editar um extrator, execute-o contra esse assembly, depois execute:

```powershell
python tools/verify_issd_documentation.py
```

Os dados de RAM em `7E:` são estado de execução. Eles não são assets da ROM e
não devem ser incluídos em distribuição.

## Contrato de estado da partida

| Subsistema | Estado/entrada confirmado | Contrato web permitido | Evidência principal |
| --- | --- | --- | --- |
| Configuração | 12 transferências de `85:A456` | armazenar as opções; aplicar somente estádio até recuperar consumidores | `issd-match-setting-transfer.json` |
| Relógio | BCD, tick de 60 frames; nova partida zera contador | iniciar em zero; não implementar término/intervalo sem fluxo | `issd-match-clock.json` |
| Equipes | 36 seleções, 20 jogadores por seleção, formações e dois uniformes | catálogo, seleção e apresentação | `issd-rom-catalog.json` |
| Estádio | 8 índices, dimensões nativas e layout selecionado | geometria/cenário por índice; câmera ampla é extensão | `issd-stadium-*.json` |
| Locomoção | caminhada: 10 poses de 3 ticks; corrida: 8 poses `4,3,3,3,4,3,3,3` | reproduzir temporização e folhas OAM validadas | `issd-animation-inventory.md` |
| Jogadores | caminhada/corrida: OAM/VRAM validado nas 8 direções; ações: cobertura parcial | usar folhas OAM para locomoção; bloquear ações sem composição temporal | `issd-player-sprite-research.md` |

As medições de caminhada/corrida estão em `issd-motion-kinematics.json` e
`issd-motion-kinematics-selected-p1.json`. Elas são referência nativa para
calibração futura, não constantes Canvas prontas para copiar.

### Conversão de direção de renderização

**Confirmado para apresentação.** A ordem de folhas de locomoção da ROM não é
a ordem geométrica do Canvas. Para o vetor de tela ordenado como cima,
cima-direita, direita, baixo-direita, baixo, baixo-esquerda, esquerda,
cima-esquerda, selecionar respectivamente as folhas ROM
`[6, 7, 0, 1, 2, 3, 4, 5]`. A conversão fica exclusivamente no adaptador de
renderização; simulação e vetor de movimento não são permutados.

**Limite.** Esta calibração corrige a pose visível e não transforma a física
provisória do navegador em física fiel. Consulte a tabela e a fonte de
validação em `issd-animation-inventory.md`.

## Atores e escalação dinâmica

**Confirmado.** `83:C6E6` inicializa arrays `$7E:3F90` e `$7E:3FA4` com 20
entradas (`00..13`). `83:C94F/C9C5` percorre 11 entradas por equipe e preenche
atores nas bases `$0500/$1000`, em passo `$0100`; a leitura de dados por ator
avança em `$20`. Entradas com bit `20` são ignoradas e os 5 bits baixos seguem
para o caminho de dados da equipe.

`86:CA23` aplica o bit `20` às entradas inativas conforme a quantidade de
jogadores em campo. Em configuração menor que quatro jogadores, `83:C71D`
compara 11 bytes das listas atuais com snapshots `$7E:D864/$7E:D878` e escreve
uma dupla de seleção em `$1E6C/$1E6E`; esses são seletores, enquanto os blocos
de estado da trajetória são `$08A0/$08D0`. `83:C7CB` e `83:C870` consomem,
respectivamente, o byte baixo e o byte alto da dupla para resolver dados de
ator. O snapshot é uma cópia de 40 bytes de `$7E:3F90` para `$7E:D864`, feita
por `83:C704`; não é um asset persistente de equipe.

**Implementação.** Tratar esses arrays como escalação/seleção de runtime, não
como catálogo permanente. O catálogo da ROM é a fonte de dados de elenco; os
arrays devem ser reconstruídos pelo fluxo da partida quando a semântica de
cada campo for confirmada.

**Artefato.** `dist/data/issd-team-runtime-slots.json`.

### Registro-base de jogador

**Confirmado.** A população dos 11 atores seleciona registros de 10 bytes por
índice de runtime. As leituras de offsets `00, 02, 04, 05, 06, 07, 08` e seus
destinos internos estão registradas em `issd-runtime-player-record.json`.

**Limite.** Esses campos não são ainda atributos nomeados de jogador; não
expor, por exemplo, `record[0]` como velocidade, visual ou posição no catálogo
web até haver evidência que associe o byte à semântica correspondente.

### Inicialização gráfica padrão

**Confirmado.** Depois de popular o ator, a ROM segue
`83:C943 → 84:F80F → 84:F813 → 83:F222` e inicializa corrida com
`DATA_82:CF9F` e `DATA_82:E34A`. O caminho de descritor chega a `84:E6C7`,
que prepara registros de transferência derivados de `DATA_82:A3D7`.

**Implementação.** Usar a temporização e os descritores exportados da ROM;
não assumir que aliases da tabela direcional são frames idênticos ou que
representam flip sem validar atributos de composição.

**Artefato.** `issd-default-locomotion-pipeline.json`.

### Contrato de descritor visual

**Confirmado.** `object+$14` identifica um descritor de seis bytes no banco
`$82`: pose (word), fonte de 24 bits para duas linhas gráficas e seletor de
detalhe de uniforme. As linhas são prefixadas por tamanho e carregadas nas
regiões dinâmicas de VRAM `$6000/$6100`; OAM separado fornece posição, tamanho,
paleta, prioridade e flips.

**Implementação.** O contrato mínimo de um renderizador de jogador é
`descriptor + tile rows + same-frame OAM + palette bank`. O detalhe de uniforme
deve ser escolhido pelos dados do ator, não por recoloração web. Consulte
`issd-player-sprite-research.md` e
`tools/render_issd_descriptor_sprite.py`.

**Limite.** Pose, gráficos e OAM precisam ser do mesmo frame. Não reutilizar
geometria de uma pose com tiles de outra, inclusive em animações ainda
pendentes.

## Seleção de ator e fases

**Confirmado.** A fase global usa `$7E:00C0` e 15 entradas em `83:CF86`.
Quatorze entradas aplicam o teste local `$30 == 1`; o índice 3 possui a
exceção `CFA4`, que também compara o acumulador/direct page a `$11E8`.
`83:C532` atualiza `$11E8` e procura slots com `$0030 != 0`.

**Limite.** Os índices de fase e `$11E8` não têm rótulo humano confirmado.
Não chamar o índice 3 de kickoff/falta nem tratar `$11E8` como jogador humano
controlado sem evidência em execução.

**Artefatos.** `issd-phase-actor-gate.json`,
`issd-active-actor-selection.json`.

## Bola, colisão e trajetória

### Colisão

**Confirmado.** `83:D774` despacha oito estados via `83:D77F`. Os índices 3 e
7 retornam imediatamente; os demais atualizam campos locais, limites e campos
de ator. `DC1C/DC5D` analisam 11 slots de ator, rejeitando `$001E != 0` ou
`$0030 == 0`; o segundo também exclui o slot local `$3E`.

**Implementação.** O motor web não pode substituir a posse por proximidade,
atrito ou quique provisórios alegando fidelidade. Até recuperar os
inicializadores e valores de coordenada, essas regras devem ficar encapsuladas
como protótipo.

**Artefatos.** `issd-collision-machine.json`,
`issd-collision-target-selection.json`,
`issd-actor-collision-fields.json`.

### Trajetória

**Confirmado.** Há dois blocos ativos: `$1E6C → $08A0` e `$1E6E → $08D0`.
`83:D9A5` executa seis estados; os temporizadores e transições estão no JSON.
`83:D920` ativa blocos não-negativos, define bit `0001` de `$11FA`, inicia
`$26 = 64` e `$2E = 0`.

O fluxo conhecido de ativação é `$F4 → $D0 → $1E6C + ($22 << 1)`. `86:AADB`
transfere os cinco bits baixos de bytes de um buffer de trabalho e `AB0F`
trata o marcador bit `20`. O buffer indireto `$28` possui 20 bytes; é derivado
de RAM dinâmica `$7E:3F90`, não de um asset ROM.

**Limite.** Não há evidência suficiente para dizer que um valor do script é
passe, chute, quique, trave ou rede. Coordenadas, velocidades, colisões e
efeito visual por frame ainda exigem captura passiva. Portanto a física web
atual não é a implementação de referência.

**Artefatos.** `issd-ball-trajectory.json`,
`issd-trajectory-activation.json`, `issd-trajectory-script-buffer.json`.

## Goleiro

**Confirmado.** O seletor de mergulho `$14A8` possui domínio `0/1/2`.
Captura usa nove handlers de `83:DDA1`, indexados pelo acumulador em `DD99`;
`$1500` é contexto em `Y`, não seletor. Os sete registros de controle
`81:B01C..B02E` foram extraídos sem atribuir semântica visual indevida.

**Implementação.** Não trocar o goleiro por uma simples colisão circular;
modelar uma máquina de estados somente quando os descritores e transições
forem cobertos por captura.

**Artefatos.** `issd-goalkeeper-context-writes.json`,
`issd-goalkeeper-catch-records.json`.

## Regras e arbitragem

**Confirmado.** Impedimento possui porta em `80:D5DF` e auxiliar `80:D627`.
Faltas e cartões usam portas em `80:EED3`, `80:EF83`, `80:F005`, `F076` e
`F09E`; suas polaridades dependem de flags e contexto. `80:F125` é a saída
comum de alguns ramos e prepara registros internos.

**Implementação.** Manter falta, cartão, impedimento e reinícios do protótipo
como provisórios até capturar transições completas. Em particular, não tratar
configuração zero/não-zero como uma regra global de ligado/desligado.

**Artefatos.** `issd-foul-gates.json`,
`issd-match-setting-consumers.json`, `issd-static-mechanics.md`.

## Ordem obrigatória de reconstrução

1. Classificar por captura passiva os pares de seleção de `83:C74F`, sem lhes
   atribuir eventos antes da correlação visual.
2. Associar, por captura passiva, cada valor de trajetória a evento, posição,
   velocidade e frame visual.
3. Substituir a bola/posse provisórias pela máquina de colisão e trajetória.
4. Completar descritores OAM de ações antes de usar sprites para chute, passe,
   carrinho e defesas.
5. Integrar goleiro, regras, reinícios e cronômetro de término.
6. Somente então adaptar renderização/câmera widescreen e multiplayer sem
   modificar a simulação determinística de referência.

O protocolo de captura para o próximo item gráfico está em
`issd-next-runtime-capture.md`; ele exige VRAM/CGRAM/OAM pareados para chute
forte e proíbe completar poses ausentes manualmente.

## Critério de aceite para cada mecânica

Uma mecânica só entra como fiel quando possuir:

- fonte estática ou captura com endereço/rótulo identificável;
- artefato regenerável em `dist/data/` com `source` e `limitations`;
- teste do extrator e `verify_issd_documentation.py` aprovados;
- teste web reproduzível ou comparação de captura que cubra a transição;
- documentação do que mudou no navegador e do que continua pendente.
