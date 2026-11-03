# Automação inicial de partida — 02/11/2026

## Resultado observado

Foi iniciada uma instância própria do BizHawk com janela oculta, ROM local e
`tools/automate_issd_probe.lua`. A sequência experimental de pulsos navegou
até uma partida: a imagem de teste no frame 3600 mostra Inglaterra × Brasil
em campo, e o campo `$11E6` registrado é 0 (modo 1 × CPU no disassembly).
As instâncias usadas no experimento foram encerradas ao término; não houve
interação com a tela nem alteração da ROM.

A primeira tentativa enviava nomes `P1 Start` com o argumento de controle 1;
o registro de entrada permanecia zero nos pulsos observados e a partida
apresentada podia ser demonstração. Com nomes sem prefixo (`Start`, `A`,
`Right`, `B`) e controle 1, os registros confirmaram `held_p1=$1000` para
Start, `$0080` para A e `$0100` para Right. O campo de entrada é evidência
de botão recebido, não de efeito esportivo específico.

Dois experimentos concluídos:

- 9.000 passos, 4.500 amostras; 900 amostras com Right e slot de ator
  válido, mas a imagem de 7200 mostra uma reposição próxima ao gol. Relatório
  `docs/issd-automated-probe-summary.json`.
- 4.800 passos, 2.400 amostras; a pressão de Right ocorreu entre passos
  3600 e 3898, com 150 amostras de slot válido. Relatório
  `docs/issd-automated-motion-probe-summary.json`.

Na segunda execução, `$1ACC=$0E00` e as coordenadas inteiras capturadas
passaram de `(160,136)` no passo 3600 a `(168,136)` no passo 3620, mas
permaneceram `(168,136)` nas amostras posteriores até 3898. Ainda não
sabemos se o ponteiro, o estado da partida ou a interpretação das
coordenadas explica essa interrupção. Os números são registrados sem
concluir velocidade, resposta de controle ou fidelidade da física.

## Instrumentos e limites

O script injeta entradas de teste e lê WRAM; não modifica a ROM. O modo
opcional de replay carrega o estado do emulador, incluindo sua RAM, apenas
na instância de teste. Registra modos, entrada recebida, configuração de jogadores, ator
candidato, bola e vínculos a cada dois passos, além de screenshots a cada
600. Usa nomes de arquivo únicos em `analysis/` (ignorado pelo Git); a
variável `ISSD_AUTO_OUTPUT_DIR` pode indicar outro diretório existente.
O script não identifica sozinho um evento ou uma condição segura para
medir. O fechamento da instância é feito pelo processo que a iniciou.

`tools/analyze_issd_auto_probe.py` gera resumos com hash dos traces locais;
`tools/test_issd_auto_probe.py` cobre integridade básica e contagem de
entradas. Os traces e screenshots são evidência local, não distribuição da
ROM. O script foi executado duas vezes com sucesso após corrigir as entradas.

## Próxima etapa

### Repetição com scripts e tipo da bola — 02/11/2026

Repetidas as duas execuções automáticas com schema v3: com A de P2 em
`analysis/issd-auto-probe-20261102-170838.jsonl` e com P2 neutro em
`analysis/issd-auto-probe-20261102-171057.jsonl`. As 240 amostras anteriores
ao comando coincidem nos campos registrados, incluindo agora scripts e
descritores dos 22 atores e velocidade/tipo da bola. O botão A foi observado
no registro de P2 nas três amostras da janela somente no teste de ação.
Não há garantia de igualdade de toda a memória interna entre as execuções.

| Deslocamento a partir do gatilho | Com A de P2 | Controle neutro |
| --- | --- | --- |
| 479 | Ator `$1900`: estado `$00B8`, script `$D6DB`, descritor `$AADF`; bola tipo 0 e vínculo `$1900` | Mesmos campos |
| 481 | Estado `$0270`, script `$D01F`, descritor `$A629` | Permanece em `$00B8/$D6DB/$AADF` |
| 483 | Estado `$0270`, descritor `$A632`; bola tipo `$17`, Z=`$FFF9`, VZ=`$FFFC`, vínculo zero | Bola tipo 0, Z/VZ zero, vínculo `$1900` |
| 499 | Estado `$0278`, script `$D320`; bola continua tipo `$17` | Ator permanece em `$00B8`, bola tipo 0 |

São amostras a cada dois passos; não há confirmação do ciclo exato da escrita.
Em `81:BD58`, a linha de estado `$0270` (offset LoROM `00BFC8`) foi
conferida na ROM: os três handlers são `84:979F`, flags `$0920`.
No assembly, `84:9755` instala `$0270` e, conforme a altura, pode selecionar
`82:D01F`. `84:979F` possui um caminho que chama `80:DE3D` e `85:F3FE`;
este pode escolher tipo `$17` e chamar `85:F8B9`, que limpa o vínculo e
inicializa a bola. As condições e chamadas foram verificadas estaticamente
por `tools/verify_issd_action_0270.py`, e o teste detecta alterações da
linha da ROM. O trace **não instrumenta diretamente** a chamada a `F3FE`;
o caminho é compatível com os valores observados, não prova dinâmica da
instrução. Também não se conclui se a ação é passe ou chute.

O relatório completo, incluindo timeline e hashes, é
`docs/issd-two-player-action-comparison-v3.json`. Os testes do comparador e
do verificador passaram. As coordenadas e velocidades permanecem em unidades
nativas brutas; não foi feita alteração da física web. Próximo passo: mapear
o comando remapeável que leva a `84:9755`, instrumentar a chamada ou
observar uma comparação adicional e, só então, avaliar a aplicação visual e
física no navegador.

### Comparação com e sem A do jogador 2 — 02/11/2026

A execução `analysis/issd-auto-probe-20261102-170348.jsonl` repetiu a
navegação e a preparação do teste anterior, mas com
`ISSD_AUTO_P2_ACTION=0`, deixando P2 neutro na janela do pulso. Ela foi
executada em uma nova instância oculta e encerrada ao término. O primeiro
teste com A foi `analysis/issd-auto-probe-20261102-164945.jsonl`.

O comparador `tools/compare_issd_action_trials.py` alinhou as execuções pelo
gatilho 3795. Nas 240 amostras anteriores à janela de A de P2, não houve
divergência entre os campos registrados: modos, fase, configuração, vínculos,
bola, cinco registros de controle e coordenadas/estado dos 22 atores. Isso
é uma base observada igual, **não prova que todo o estado interno do emulador
seja idêntico**, pois nem toda a memória foi registrada.

Nos três frames amostrados do pulso, `held_p2 & $0080` foi não zero apenas
na execução com A. Nas 60 amostras da janela iniciada pelo pulso, as posições
de bola registradas diferiram entre as execuções desde o primeiro frame
amostrado (deslocamento 481). Na execução com A, o vínculo `$00A6` passou
de `$1900` a zero e a altura da bola passou a valores negativos; na execução
neutra, nessa janela inicial a bola e o vínculo permaneceram registrados.
As imagens da execução com A mostram a bola subindo após o comando.

Este contraste fortalece a hipótese de que o comando causou essa liberação
na situação testada. Ele **não identifica se a ação é passe, chute ou outro
tipo**, não garante equivalência do estado interno oculto e não prova duração
exata devido à amostragem de dois frames. A comparação também não calibra
velocidade ou projeção web. O relatório reproduzível com hashes e limites é
`docs/issd-two-player-action-comparison.json`. Dois testes verificam base
igual/divergente e rejeição de base vazia; auditoria documental passou.

O coletor schema v3 passou a registrar scripts/descritores dos atores e
componentes de velocidade/tipo da bola para futuras execuções. O teste de
controle já os contém; o teste com A é anterior e não os contém, portanto
não se pode comparar esses campos entre os dois. Próximo passo: repetir os
dois cenários com schema v3 e comparar scripts, tipo e velocidade da bola;
depois confrontar o caminho de ROM correspondente antes de aplicá-lo na web.

### Observação após comandos dos dois jogadores — 02/11/2026

O cenário `ISSD_AUTO_SCENARIO=two_player_action_observation` usa a mesma
navegação 1 × 2, mas espera, além dos atores e da fase elegível, uma mudança
no contador BCD da partida em `$16D0` antes de iniciar o experimento. Esse
filtro é mais forte que apenas observar atores, embora ainda não prove todos
os estados de jogo aberto. A instância isolada terminou e foi encerrada.

A execução `analysis/issd-auto-probe-20261102-164945.jsonl` acionou o
experimento no passo 3795. Ela separou períodos neutros, Right para cada
controle, A para P1 e A para P2, com 27 amostras após o pulso de P1 e 57
após o de P2. O trace é amostrado a cada dois passos.

Durante o pulso A de P2, a altura bruta da bola passou de 0 a `$FFF3`
(-13 em complemento de dois); nas 57 amostras seguintes foram observadas
42 combinações distintas de X/Y/Z. As imagens locais dos passos 4275 e
4305 mostram a bola próxima ao jogador e depois no ar. Isso sustenta a
ocorrência de uma mudança após o comando, mas **não identifica passe ou
chute**, nem isola todos os outros eventos que podem ter ocorrido.

Na janela Right de P1, seu ator mudou posição em 56 de 58 pares válidos;
na janela Right de P2, o ator de P2 mudou em 56 de 59 pares. O ator de P1
também mudou em 54 de 59 pares durante a janela de P2, então não se pode
atribuir cada deslocamento somente ao comando sem uma repetição controlada
a partir do mesmo estado. Não houve calibração de velocidade web.

O resumo com hash e posições brutas está em
`docs/issd-two-player-action-observation.json`; as imagens permanecem em
`analysis/`. `tools/analyze_issd_two_player_experiment.py` agora inclui
as janelas posteriores aos pulsos. Dois testes automatizados e a auditoria
da documentação passaram. Próximo passo: registrar estado, script, descritor
e velocidade da bola em cada janela e comparar repetições com/sem o pulso
do P2 a partir de uma condição equivalente, antes de portar o evento.

### Experimento automático com dois controles — 02/11/2026

O cenário `ISSD_AUTO_SCENARIO=two_player_experiment` navega até 1 × 2 e
aguarda 30 passos consecutivos com `$11E6=4`, `$00C0=0` e dois atores
ativos de registros de equipe diferentes. Essa condição é um filtro
experimental, não prova isolada de jogo aberto. Em seguida, envia períodos
neutros, Right ao P1, Right ao P2 e pulsos A separados, registrando todos os
atores, controles e bola a cada dois passos.

A execução local `analysis/issd-auto-probe-20261102-164513.jsonl` terminou
6.500 passos e acionou o experimento no passo 3666. A imagem de início mostra
os jogadores no círculo central e relógio `5:00`, portanto o experimento
começou próximo à saída de bola; ela não comprova que as condições de jogo
aberto já estavam estabilizadas. Na janela Right do P1, seu ator mudou
posição inteira/fracionária em 47 de 56 pares consecutivos; na janela Right
do P2, o ator de P2 mudou em 55 de 59 pares. O ator de P1 também mudou em
56 de 59 pares durante a janela de P2, mostrando que estes números, sozinhos,
não isolam a causa do movimento.

A bola mudou de posição nas janelas direcionais, mas os três registros de
cada pulso A tiveram a mesma posição dentro de sua própria janela. Não há
evidência suficiente para nomear passe ou chute, e o intervalo entre pulsos
não foi monitorado como um experimento de transferência de posse. O resumo
`docs/issd-two-player-experiment-summary.json` inclui hash do trace, janelas,
contagens e primeiras/últimas posições da bola. Instância isolada encerrada;
nenhuma alteração à mecânica web.

Dois testes de `test_issd_two_player_experiment.py` passaram para janelas,
coordenadas fracionárias e ausência de gatilho; auditoria documental passou.
Próximo passo: registrar bola e estados durante uma janela completa após
cada pulso, com controle neutro e screenshots próximos da ação, e construir
uma condição mais forte de jogo em andamento antes de medir comportamento.

### Partida humano × humano automatizada — 02/11/2026

O cenário `ISSD_AUTO_SCENARIO=two_player_probe` iniciou uma partida 1 × 2
em instância própria oculta do BizHawk. A navegação observada foi: Start,
confirmar Open Game, confirmar Single Game, mover para a direita na seleção
de participantes e confirmar 1 × 2. O valor interno `$11E6=4` foi registrado,
correspondente a `NumOfPlayers_1_VS_2` no disassembly. A seleção do segundo
time exigiu confirmação pelo **controle 2**; pulsos apenas pelo controle 1
deixaram a execução nessa tela.

Na execução concluída `analysis/issd-auto-probe-20261102-164118.jsonl`, o
frame 4200 mostra Brasil × Inglaterra em campo. O trace registra os cinco
controles e os jogadores. Entre os passos 3780–3898, os registros `$1AA0`
e `$1AD0` apontavam respectivamente para `$0F00` e `$1900`, em equipes
diferentes; seus flags eram `$4000/$4001`, sem o bit `$8000` que identifica
a rota automatizada nesse contexto. O controle 2 recebeu Right com
`held_p2=$0100` durante 60 amostras; a posição inteira/fracionária do ator
associado mudou em 55 de 59 pares consecutivos. O controle 1 também recebeu
comandos nas outras direções e seu ator apresentou mudanças de posição.

Os resumos por controle estão em `docs/issd-auto-two-player-p1-summary.json`
e `docs/issd-auto-two-player-p2-summary.json`, com hash do trace. A análise
de P2 usa o registro `$1AD0`; não compara seu ponteiro com `$1ACC`, que é
campo do controle 1. Testes cobrem a seleção do registro de P2. As instâncias
ocultas de teste foram encerradas.

**Limites:** na primeira janela de movimento a partida ainda estava entrando
em campo; não se deve tratar todas as amostras iniciais como jogo ativo.
Mudança de coordenadas enquanto um comando está aplicado não comprova por si
só causalidade, velocidade ou posse. Ainda não foi reproduzida uma troca de
bola controlada entre P1 e P2. A mecânica web continua inalterada.

Próxima etapa: iniciar comandos somente depois de confirmar jogo ativo,
comparar P1 e P2 em trechos neutros e direcionais separados e registrar
tentativas de passe/chute e transferência da bola entre eles. Isso elimina a
dependência da CPU para preparar os dois jogadores, mas exige validar o
resultado de cada ação em vez de presumir que ela ocorreu.

### Movimento humano quando o vínculo da bola aponta ao outro time — 02/11/2026

O cenário `ISSD_AUTO_SCENARIO=opponent_link` espera um ator válido associado
ao controle físico e um `$00A6` válido de equipe diferente; nesse momento,
salva uma imagem e envia Right, Left, Up e Down ao P1 em sequência. O teste
tem limite de 10.000 passos e registra se encontrou candidato. A condição é
um **indício para seleção do experimento**, não uma definição universal de
posse. A imagem do teste fica em
`analysis/issd-auto-probe-20261102-163255-candidate.png`; nela há jogadores
próximos e a posse não pode ser estabelecida com segurança apenas pela imagem.

O candidato ocorreu no passo 4175, com ator controlado `$0E00` e vínculo
`$1A00`, de registros de equipe diferentes. A execução terminou os 10.000
passos em instância oculta, depois encerrada. Foram registrados 45 amostras
de controle ativo por direção. Enquanto `$00A6` apontava para um ator
diferente do controlado, houve mudanças na posição inteira/fracionária em
28 pares consecutivos para Right, sete para Left, nove para Up e oito para
Down. O vínculo pode mudar durante cada trecho: as contagens são por amostra,
não significam posse adversária contínua durante toda a sequência.

Os resumos com hash estão em `docs/issd-auto-opponent-link-summary.json` e
`docs/issd-auto-opponent-probe-summary.json`. Os analisadores aceitam o evento
de gatilho sem confundi-lo com amostra; quatro testes passaram. Não há ainda
prova visual suficiente para chamar o instante de posse da CPU, nem dados
para converter movimento ao Canvas. Próxima etapa: acompanhar por frame a
bola, os dois atores e suas distâncias/estados, com screenshots ao longo da
sequência, para distinguir condução adversária de outros vínculos.

### Vetores com sinais mistos — 03/11/2026

Duas instâncias isoladas repetiram o cenário com ângulos sintéticos 20 e 52
na entrada de `83:9E32`. Ambos selecionaram em `81:A5D7` os words 615 e 1522
(offset sem header `0xA627`), multiplicados por 40. No ângulo 20, a CPU
gravou `(-24600, 60880)`; no 52, `(24600, -60880)`. Os valores são os
componentes inteiros de ponto fixo bruto, não velocidades em pixels do Canvas.

`tools/analyze_issd_vector_quadrants.py` verifica os bytes da ROM, as 245
amostras anteriores comparáveis de cada replay, os overrides e os callbacks
de produto, correção de sinal e armazenamento. Os dados e hashes estão em
`issd-type1-mixed-sign-vectors.json`. Somados ao ângulo natural 4 e ao
sintético 36, estes casos exercitam as quatro combinações de sinal.

Os ângulos 20 e 52 foram forçados apenas no registrador de entrada: o campo
da bola `$0452` permaneceu 4. Os ensaios validam esses pontos isolados da
rotina, não uma partida natural para cada direção, toda a tabela ou a
projeção de velocidades para a versão web. Próximo passo: validar bordas dos
quadrantes e a evolução temporal da bola após inicializar o vetor.

### Vetor oposto com ângulo sintético — 03/11/2026

No mesmo replay, `ISSD_AUTO_VECTOR_TEST_ANGLE=36` substituiu apenas o
registrador A na entrada de `83:9E32`, no passo 493. O valor original era 4;
`$0452` permaneceu 4, portanto o teste **não é uma jogada natural** nem um
estado de bola completamente coerente com ângulo 36. Foi executado em
instância isolada, sem alterar ROM ou savestate. A comparação anterior à
ação repetiu 245 amostras iguais nos campos registrados.

A CPU primeiro produziu os mesmos módulos 144960 e 59440 do ângulo 4;
em seguida, a correção de sinal de `83:9E92` inverteu ambos, resultando em
`-144960` e `-59440`, gravados como `$FFFD:$C9C0` e `$FFFF:$17D0` nas
velocidades X e Y. `tools/analyze_issd_type1_opposite_vector.py` valida
o override, a tabela da ROM, os callbacks e as palavras gravadas;
`issd-type1-opposite-vector-observation.json` registra dados e hashes.

Estão comprovados dois pontos específicos do cálculo, um natural e outro
sintético. Os outros quadrantes, limites e a relação com o sistema web ainda
precisam de validação. Não aplicar essa velocidade diretamente ao Canvas.

### Vetor inicial da bola tipo 1 observado — 03/11/2026

A reação do passo 493 foi repetida com callbacks de `83:9E32`, `83:9E92`,
`83:9EC3`, `83:953F`, `83:9722` e seus retornos. O controle pareado teve
245 amostras anteriores iguais nos campos registrados. O analisador
`tools/analyze_issd_type1_vector.py` verifica as duas entradas na ROM, a
ordem dos callbacks e os produtos; os dados e hashes estão em
`issd-type1-vector-observation.json`.

Para esta inicialização, tipo 1 e parâmetro 1 selecionaram o byte 40 de
`81:A367` (offset sem header `0xA378`). Ângulo 4 selecionou em `81:A5D7`
(offset `0xA5E7`) os words 3624 e 1486. O multiplicador produziu
respectivamente 144960 e 59440, armazenados como pares de words
`$0002:$3640` e `$0000:$E830` nas velocidades X e Y. O ramo observado tinha
`$00AC=$00AE=0`; nesse ângulo não houve inversão de sinal. Em `83:9722`, o
jogo zerou as duas palavras de velocidade vertical e as duas de altura;
ao retornar, o timer observado era 12.

Esse é um caso concreto com ângulo e parâmetro específicos: ainda não valida
todos os sinais, magnitudes, clima, ramos alternativos ou a conversão de
velocidade nativa para Canvas. O timer não deve ser atribuído a uma condição
de clima sem registrar `$1E4C` no mesmo instante. A reação aérea permanece
isolada do motor web; próximo passo: validar mais ângulos e a integração
quadro a quadro em unidades nativas antes de calibrar a projeção web.

### Modelo isolado da resposta à bola tipo 2 — 03/11/2026

`dist/native-ball-contact-response.mjs` modela o trecho `84:BAB7 → 85:F088 →
85:F0D3` quando a bola é tipo 2, `$046C < 10`, os campos de equipe são
diferentes e `+$60 & $8000` está ativo. Nessa rota, o jogo usa a tabela
`81:9632` para o byte de ângulo, calcula Y como `($0078 & 3) + 1` e encaminha
tipo 1 à inicialização. O chamador ainda precisa confirmar o contato espacial
e os estados anteriores; o módulo não os simula. Para `+$60 & $8000` limpo,
retorna rota não resolvida, pois há testes adicionais.

`dist/test-native-ball-contact-response.mjs` confere os limites e reproduz
os parâmetros observados no callback `85:F8BF` (X=1, A=4, Y=1). A direção 1
e os dois bits baixos de `$0078` iguais a zero no teste são inferidos desses
parâmetros e das tabelas, **não foram registrados diretamente nesse callback**.
O módulo não altera a bola na partida web: faltam a correspondência de seus
estados, os valores de velocidade e a escala das coordenadas. Continuar pela
inicialização e integração temporal da bola tipo 1 antes de ligar essa
resposta ao navegador.

### Interceptação durante o atraso de recolhimento — 03/11/2026

No protótipo, o atraso de 260 ms após um passe ou chute bloqueava tanto a
equipe que tocou por último quanto o adversário. A captura da ROM no cenário
estudado mostra que um jogador adversário consegue interagir com a bola em
poucos passos após a liberação; não sustenta esse bloqueio geral. O adaptador
web agora permite ao adversário recolher uma bola livre **no chão** durante
esse intervalo, se passar no teste geométrico. A equipe do último toque
continua sujeita ao atraso provisório; depois dele, qualquer equipe elegível
pode recolher. Testes cobrem adversário imediato, equipe bloqueada e o limite
de 260 ms.

A captura nativa em questão envolveu bola no ar e uma reação intermediária de
tipo 2 para tipo 1. A mudança web não reproduz essa sequência nem prova que
260 ms seja o tempo original: é uma correção limitada do bloqueio geral,
enquanto física aérea, transição de estados e o tratamento da equipe que
liberou a bola permanecem pendentes de integração.

### Primeiro uso da geometria de contato na partida web — 03/11/2026

`dist/ball-contact.mjs` implementa a aritmética do ramo comum de `84:E8B0`
(`+$68 != 0`), incluindo carry e wrap. `dist/game.js` usa esse teste para
localizar jogadores elegíveis quando a bola está livre; se houver mais de um,
escolhe o mais próximo entre os elegíveis. Antes, o protótipo comparava apenas
o mais próximo com um raio circular fixo. O teste em
`dist/test-ball-contact.mjs` compara o núcleo com 28 retornos observados na ROM
e verifica a seleção quando o mais próximo fica fora dos limites por eixo.

Este é um adaptador de jogabilidade **provisório**: converte distâncias do
Canvas com as proporções de `dist/native-field.mjs`, cuja escala ainda não foi
calibrada contra a ROM. Assume altura zero para jogadores e o ramo comum; a
exigência de bola no chão, o intervalo de 260 ms para a equipe do último toque
e a escolha do jogador mais próximo são regras do protótipo, não regras
recuperadas. A integração ainda não reproduz a reação tipo 2→1 nem a física
e os vínculos completos da ROM. O próximo passo é medir o mapeamento espacial
real e portar os estados, timers e reação demonstrados no replay.

### Ramo alternativo com alteração temporária de RAM — 03/11/2026

Como o replay natural não alcançou `+$68=0`, foi executado um experimento
sintético e isolado: no passo 493, na entrada de `84:E8B0` para o jogador
`$0F00`, o script alterou **temporariamente a RAM do emulador** de `+$68=10`
para zero. No callback de retorno, restaurou 10 antes de a partida continuar.
A ROM e o estado salvo de origem não foram alterados. A opção explícita
`ISSD_AUTO_GEOMETRY_TEST_FORCE_68_ZERO=1` exige replay isolado e trace de bola;
o log registra override e restauração, que o analisador exige em pares.

Com equipes `$0D00` e `$0E00`, a execução passou por `84:E8E9 → 84:E902 →
84:E91E` e retornou carry limpo, como previsto pelo modelo. A coordenada Z
era `$FFF9`, com ator em Z=0. O relatório
`issd-ball-contact-geometry-synthetic.json` registra a modificação e contém
36 comparações sem divergência, **uma** delas no ramo alternativo. Os campos
observados no controle neutro correspondiam antes da ação.

Este único ponto demonstra concordância nesse cenário artificial; não valida
todo o espaço de entradas, os casos de rejeição ou uma situação natural com
`+$68=0`. Próxima etapa: testar limites e rejeições diretamente na CPU em
experimentos isolados, além de procurar a ocorrência natural. Não conectar o
modelo ao motor web enquanto a cadeia completa de contato não estiver validada.

### Cobertura ampliada da geometria — 03/11/2026

`ISSD_AUTO_BALL_TRACE_START` e `ISSD_AUTO_BALL_TRACE_END` permitem ampliar
a janela de callbacks (limites inclusivos entre 0 e 650). Com a mesma entrada
e o mesmo savestate, foi capturado o intervalo inteiro 0–650, comparado ao
controle neutro nos campos registrados antes da ação. O relatório
`issd-ball-contact-geometry-extended.json` preserva o hash das fontes e os
37 pares de entrada/retorno: **2 carry limpo e 35 carry set**, todos iguais
ao modelo isolado.

A classificação dos pares mostra 29 que passaram pelos gates e tinham
`+$68 != 0`, oito recusados nos gates iniciais, e **nenhum** com `+$68=0`
em qualquer relação de equipe. Portanto ampliar a janela deste replay não
validou o ramo alternativo. `tools/test_issd_ball_contact_geometry.py` agora
cobre seus limites de eixo e inclui casos sintéticos de overflow do ADC em
16 bits; esses testes não substituem observações no processador. Próxima
etapa: obter autonomamente outra situação em que `+$68=0` e a bola esteja
livre, e comparar as saídas desse ramo com o emulador antes de usá-lo na web.

### Proximidade anterior à reação — 03/11/2026

No replay do passo 493, o caminho foi `84:86E2 → 84:E8B0 → 84:E8BD →
84:E8E4 → 84:B9F7 → 84:BA01 → 84:BA6F`. A entrada em `84:86E2` exige
`$00A6=0` e bit 0 de `+$60` ativo; `84:E8B0` deve retornar carry limpo.
A rotina também recusa quando `$11FA` é negativo ou `+$3E` não é zero.

Na chamada observada, `+$68=10`, então foi selecionado o caminho `E8BD`:
o jogador estava nas coordenadas inteiras `(158,119,0)` e a bola em
`(160,121,$FFF9)`. O teste de altura usa `(ator_z - bola_z) & $FFFF < $18`.
Os testes seguintes usam centros/larguras `(12,24)` no eixo X e `(8,16)`
no Y. Em cada eixo a ROM faz `CLC; ADC ator; SBC bola; SEC; SBC largura`:
o primeiro SBC **herda o carry do ADC** e pode subtrair uma unidade adicional.
O retorno observado foi carry limpo.

Se `+$68=0`, a equipe do ator é comparada com a do objeto em `$00C8`:
iguais usam o mesmo caminho; diferentes testam outra faixa vertical e usam
centros/larguras `(14,28)` e `(10,20)`. Os valores são palavras brutas do
jogo, não metros. A implementação isolada em `tools/issd_ball_contact_geometry.py`
preserva wrap e carry; não altera a física web. O analisador verifica os bytes
da rotina na ROM e comparou **36 retornos reais sem divergência**, inclusive
aceitações e rejeições, no relatório `issd-ball-contact-geometry-observation.json`.
Os testes de limites são sintéticos; o ramo alternativo de equipe diferente
com `+$68=0` não foi observado nessa captura e ainda precisa de validação
dinâmica. O modelo também não identifica sozinho a ação esportiva resultante.

### Rota que reage à bola tipo 2 — 03/11/2026

O replay instrumentado localizou a origem da reinicialização intermediária:
no passo relativo 493, o ator `$0F00` executou, nesta ordem,
`84:BA6F → 84:BAA8 → 84:BAB7 → 84:BAF6 → 85:F06E → 85:F088 → 85:F0D3 →
85:F8BF → 85:F8D6 → 83:94EB`. O controle pareado teve 245 amostras prévias
iguais nos campos registrados, e X foi confirmado apenas no replay de ação.
`tools/analyze_issd_ball_contact_route.py` valida os callbacks ordenados,
as condições observadas e os bytes das instruções na ROM local; o relatório
`issd-ball-contact-route-observation.json` guarda dados e hashes.

Em `84:BAB7`, a ROM testa tipo `$0430=2`, contador `$046C < 10` e diferença
entre o campo de equipe `+$9A` do ator e o do objeto em `$00C8`. Nesta
captura os valores eram respectivamente 2, 6, `$0D00` e `$0E00`. O campo
`+$60` do ator era `$A387`, com bit `$8000` ativo, levando diretamente a
`84:BAF6` e à chamada `85:F06E`. Em `85:F088`, a ROM calcula Y a partir de
`$0078`, obtém um valor direcional e chega a `85:F0D3`, que passa X=1 ao
caminho de inicialização. O callback de `83:94EB` ainda vê o tipo anterior 2
e `$0000=1`, antes das instruções que gravam o novo tipo.

No passo 502 o mesmo handler foi novamente alcançado, mas a bola já era do
tipo 1 e a execução seguiu para `84:BAFB`; a amostra posterior mostra o
vínculo `$00A6=$0F00`. Isso não determina, por si, como o jogo detectou a
proximidade nem o significado esportivo completo da reação. Também não
justifica aplicar essas condições isoladamente ao motor web. A continuação
acima recupera a entrada e os testes espaciais deste caso; os demais ramos
e a integração completa da reação continuam pendentes.

### Reinicializações e troca de vínculo da bola — 03/11/2026

Uma repetição instrumentada do mesmo cenário mostra três passagens pela
inicialização `85:F8D6 → 83:94A4`, com página direta do ator e parâmetros:

| Passo | DP / X do ator | Tipo anterior em `$0430` | Novo tipo em `$0000` | Y |
| --- | --- | --- | --- | --- |
| 487 | `$1900` | 0 | 2 | 11 |
| 493 | `$0F00` | 2 | 1 | 1 |
| 502 | `$0F00` | 1 | 0 | 0 |

No callback em `83:94EB` a gravação ainda não ocorreu; as instruções seguintes
copiam `$0000` para `$0430` e `$0476`. Os bytes dessas instruções e de
`85:EECE` foram verificados na ROM pelo analisador
`tools/analyze_issd_ball_reinitialization.py`. No passo 502 também foi
observada a entrada `85:EECE` com DP=`$0F00`: a rotina passa X=0 para
`85:F8C5` e, quando a chamada retorna, grava X em `$00A6`. A amostra depois
do passo mostra tipo 0 e vínculo `$0F00`. Isto é consistente com a
preservação de X documentada em `issd-ball-state-routing.md`; não identifica
sozinho a ação esportiva nem demonstra todas as condições de contato.

A comparação com o controle teve 245 amostras anteriores iguais nos campos
registrados e seis amostras com X exclusivo; os eventos e hashes estão em
`issd-ball-reinitialization-observation.json`. A troca 2→1 no passo 493 é
outra inicialização acionada pelo ator `$0F00`, não uma conclusão que possa
ser atribuída apenas à atualização vertical. A continuação acima identifica
o chamador imediato; a detecção espacial do contato permanece pendente.

Uma tentativa separada registrou com sucesso callbacks de escrita nos aliases
de `$0430/$00A6` no domínio `System Bus`, porém não recebeu eventos mesmo
havendo mudanças verificadas. Não se trata essa ausência como prova de que
não houve escritas. Os callbacks de execução acima, conferidos contra a ROM,
foram usados no lugar deles. Próxima etapa: rastrear a origem da chamada do
passo 493 e os testes que a permitem.

### Atualização da bola após a ação — 03/11/2026

O replay anterior foi repetido no BSNES com callbacks opcionais
`ISSD_AUTO_BALL_UPDATE_TRACE=1`; todas as oito inscrições foram confirmadas.
O controle neutro apresentou 245 amostras prévias iguais nos campos comparados,
e o botão X foi confirmado nas seis amostras do intervalo de ação. O relatório
`issd-ball-update-observation.json` contém 81 callbacks, registrando palavras
inteiras e fracionárias, com hashes das fontes. Os callbacks ocorrem **antes**
da instrução indicada.

Estática e dinamicamente, `83:90E6` usa `$0430` para indexar palavras da
tabela `83:90F9` (offset LoROM sem cabeçalho `0x190F9`): tipos 0, 1 e 2
apontam respectivamente a `83:9137`, `83:9240` e `83:91F6`.
`tools/analyze_issd_ball_update.py` verifica esses bytes na ROM local e
confere as inscrições e o controle pareado. No experimento:

- Nos passos 487–492, o despachante observou tipo 2 e passou por `83:91F6`,
  `83:941F` e `83:882A`; `$0454` permaneceu em 16 nos callbacks registrados.
- Nos passos 493–501, observou tipo 1 e passou por `83:9240`, `83:941F` e
  `83:9264`. No primeiro desses passos, o callback em `83:9240` registrou
  `$0454=12` e o de `83:9264`, após o decremento no código, registrou 11;
  no passo 501 registraram-se respectivamente 4 e 3.
- O primeiro callback do despachante no passo 493 já via tipo 1. Portanto
  essa captura não identifica quem mudou o tipo 2 para 1. Não houve callback
  dessas rotinas nos passos 502–510, apesar de haver amostras da bola; isso
  não prova por si só a causa da mudança de vínculo.

O assembly em `83:9264` soma as palavras `$0434/$0436` a `$040E/$0410`
com carry e contém um limite dependente do sinal. A interpretação física,
os demais cálculos e a causa da transição continuam pendentes; não se deve
extrapolar uma fórmula geral a partir desse único caso. Próximo passo: rastrear
os escritores de `$0430` e `$00A6` entre os passos 492 e 502, incluindo o
contexto da colisão e a ordem dentro do frame.

### Bola após o caminho alternativo — 03/11/2026

O mesmo par de replays foi analisado por `tools/analyze_issd_alternate_ball.py`,
que exige comparação estendida prévia sem divergências, confirmação do botão
X exclusivo, controle neutro e amostras consecutivas nos passos 480–510.
O resultado reproduzível, com hashes das fontes, está em
`issd-alternate-ball-observation.json`. Os passos são relativos ao gatilho,
não ao início da partida.

| Passo | Amostra de ação | Controle neutro |
| --- | --- | --- |
| 486 | tipo 0, vínculo `$00A6=$1900` | tipo 0, vínculo `$1900` |
| 487 | tipo 2, vínculo zero; posição bruta `(171,135,$FFFE)` | tipo 0, vínculo `$1900`; `(179,139,0)` |
| 493 | tipo 1, vínculo zero; posição `(159,121,0)` | tipo 0, vínculo `$1900` |
| 502 | tipo 0, vínculo `$00A6=$0F00`; posição `(167,135,0)` | tipo 0, vínculo `$1900` |

Os valores são registros de 16 bits, sem conversão presumida para unidades
físicas. A transição de tipo 2 para 1 e o vínculo posterior a outro objeto
são observações dessa partida, não prova da causa da mudança nem de posse
formal. A amostragem não registra todos os campos fracionários nem eventos
de colisão; por isso não se pode inferir a trajetória contínua, atribuir um
nome esportivo à ação ou implementar uma fórmula geral de física. Próximo
passo: capturar os handlers de atualização da bola e colisão no intervalo
487–502 e correlacioná-los aos campos completos do objeto.

### Transição observada no caminho alternativo — 02/11/2026

O replay de X com `UpLeft` mantido foi repetido com
`ISSD_AUTO_ALTERNATE_TRACE=1`, que monitora os handlers do ator de P2 e os
pontos de liberação da bola. O controle neutro usou o mesmo estado salvo e
a mesma preparação. Foram comparadas 245 amostras anteriores, sem diferenças
nos campos registrados; o botão X foi confirmado em seis amostras apenas no
replay de ação. A primeira diferença no registro amostrado da bola apareceu
no passo relativo 487.

No replay de ação, o ator passou para estado `$0160` e script `$D280` no
passo relativo 480; no 486, para `$0168/$D290`. Os callbacks mostraram
`$84:96B8`, depois `$84:96CF` e `$84:96D4`; no passo 487, `$84:96E5` entrou
com contador `+$70=1`, seguido de `$85:F438`, `$85:F45F` e `$85:F871` com
X=`$0002` e Y=`$000B`. Na amostra posterior desse passo, a bola tinha tipo
`$0002` e `$00A6=0`; no neutro permanecia tipo zero e vinculada ao objeto
anterior. Os callbacks são anteriores às respectivas instruções.

`tools/analyze_issd_alternate_action.py` verifica as linhas de dispatch na
ROM local: offsets LoROM sem cabeçalho `0xBEB8` para `$0160` e `0xBEC0` para
`$0168`. O trace com hashes está em `issd-alternate-action-trace.json` e a
comparação pareada em `issd-alternate-action-neutral-comparison.json`.
Isso documenta uma transição específica, mas não define seu nome esportivo,
todas as condições de entrada ou a física completa. O caminho alternativo
continua sem integração à partida web. Próximo passo: investigar as condições
e os parâmetros de `$85:F871` em outros estados e comparar as consequências
da bola antes de modelá-las.

### Oito direcionais mantidos e desvio de seleção — 02/11/2026

Repetida a ação X com os oito direcionais mantidos, sempre a partir do mesmo
savestate, da preparação `DownRight` e de um replay neutro correspondente.
Todos os oito tiveram cobertura prévia completa e igualdade nos campos
observados, além de confirmação do botão e do direcional. As oito consultas
da tabela de direção e de `+$86` corresponderam à ROM. Em sete casos, a
seleção posterior `$84:968B/$84:E600` também correspondeu às tabelas;
esses resultados estão em `issd-eight-held-directions-audit.json`, gerado
por `tools/audit_issd_held_directions.py`.

No caso `UpLeft`, a diferença angular foi 4 e a tabela gerou `+$86=$8004`.
O seletor principal não foi chamado: uma repetição instrumentada observou
`$84:96B8` seguido de `$84:E6AC`, com A=`$D280` e Y=`$E4EA`; o estado
amostrado passou a `$0160`, script `$D280`. O disassembly em `$84:967E`
testa o sinal de `+$86` e desvia para esse caminho. Isso é evidência para
essa situação específica, não prova de que todo valor negativo produza a
mesma animação em qualquer estado.

O modelo isolado `nativeActionSelection` foi corrigido para retornar script
e controle nulos quando `+$86` tem bit 15 ativo, em vez de inferir a tabela
principal. O módulo continua fora da partida; o desvio ainda não é modelado
como regra geral. O comparador de ensaios também passou a aceitar amostras
extras por frame, exigindo ainda uma sequência completa de 240 amostras
alternadas e a janela de entrada coberta. Testes cobrem cobertura adicional,
lacunas e a exceção do seletor. Próximo passo: investigar o caminho `$0160`
e validar sua relação com controles e condições da bola antes da integração.

### Ação com direcional mantido — 02/11/2026

`ISSD_AUTO_P2_ACTION_DIRECTION` permite manter um dos oito direcionais no
mesmo intervalo do botão de ação. Três replays partiram do mesmo estado e
usaram a mesma preparação `DownRight`; somente o direcional junto com X
variou. No caminho observado, `$80:DD34` leu o nibble alto do registro do
controle e consultou a tabela de bytes `$81:9613`:

| Entrada junto com X | Palavra do controle | Nibble | Saída da tabela | Script observado |
| --- | --- | ---: | ---: | --- |
| Up | `$0840` | 8 | 6 | `$D16E` |
| DownLeft | `$0640` | 6 | 3 | `$D1C5` |
| Right | `$0140` | 1 | 0 | `$D16E` |

Os hooks registraram a saída em `$83:F1B1`, a escrita em `+$86` e a escolha
do script; os valores foram conferidos com as tabelas na ROM local. Os
relatórios com hashes seguem os padrões `issd-input-held-*.json`,
`issd-field86-held-*.json` e `issd-action-selector-held-*.json`.
`nativeHeldDirection` em `dist/native-action-selector.mjs` modela a consulta
isolada de `$80:DD34`, incluindo o caso de nibble zero; testes cobrem as três
capturas. O chamador ainda precisa decidir se o fluxo realmente chegou a esse
ramo, pois em outras condições o valor vem de outro cálculo. A função continua
fora da jogabilidade web; nomes de ações, controles remapeáveis e demais
condições de seleção seguem pendentes.

### Origem observada da entrada de `$80:E48D` — 02/11/2026

Com `ISSD_AUTO_INPUT_ORIGIN_TRACE=1`, o coletor monitora a janela da ação no
ator associado a P2. Nos três replays com X, o registro do controle tinha
`$0040` no momento observado, sem bits direcionais no nibble consultado por
`$80:DD34`. Os fluxos se dividiram:

- `UpLeft` e `DownLeft`: foram observadas, na ordem, `$83:F151`, `$80:E770`,
  `$80:E7B0`, `$80:F455`, `$80:DE35` e `$83:F1B1`. Em `$80:DE35`, A era 31
  e 34 respectivamente; a tabela de bytes `$81:963A`, mascarada por `$0F`,
  retornou 4 e 5, que chegaram a `$83:F1B1` antes de gravar `+$84`.
- `DownRight`: após `$80:E770`, o caminho passou por `$83:F19F`, `$80:DD34`
  e `$80:DD45`; com o nibble direcional zero, chegou a `$83:F1B1` com A=1,
  igual à direção `+$2E` observada.

O disassembly mostra que `$80:E770` testa campos do ator e valores globais,
e que `$80:E7B0` e `$80:F455` participam do cálculo anterior à consulta de
direção. Esses caminhos envolvem mais do que a última tecla pressionada;
os significados completos das coordenadas e das condições ainda não estão
estabelecidos. `tools/analyze_issd_input_origin.py` verifica os bytes das
rotinas `$80:DD34/$80:DE35` e a tabela na ROM local. Resultados com hashes:
`issd-input-origin-{upleft,downleft,downright}.json`.

Essas evidências valem para os replays testados e não nomeiam a ação como
passe ou chute. O modelo isolado de seleção web continua sem ligação à
partida. Próximo passo: identificar os valores de entrada e resultados de
`$80:E770/$80:E7B0/$80:F455` em situações variadas, incluindo direção mantida
no momento do botão, antes de reproduzir o caminho completo.

### Origem observada do campo `+$86` — 02/11/2026

Na rotina `$80:E48D`, a direção em `+$2E` é subtraída do valor em A, o
resultado é reduzido com `& 7` e multiplicado por dois para indexar a tabela
de palavras `$81:96B2`. O valor lido é escrito em `+$86`. Em três replays,
capturados na entrada e na saída da rotina para o ator inicial de P2, foram
observados:

| Preparação | A na entrada | `+$2E` | Diferença `& 7` | `+$86` resultante |
| --- | ---: | ---: | ---: | --- |
| DownRight | 1 | 1 | 0 | `$0000` |
| DownLeft | 5 | 3 | 2 | `$0282` |
| UpLeft | 4 | 5 | 7 | `$0481` |

Nos três casos, A coincidiu com o campo `+$84` registrado na entrada. A
fórmula e o resultado observados foram verificados contra os bytes da rotina
e da tabela na ROM local por `tools/analyze_issd_field86.py`. A tabela está
no offset LoROM sem cabeçalho `0x96B2` e a rotina em `0x648D`; relatórios
com hashes estão em `issd-field86-{downright,downleft,upleft}.json`.

`dist/native-action-selector.mjs` modela isoladamente essa consulta e o
seletor de `$81:C510/$81:C520` no caminho observado, com testes para os oito
índices e as três capturas. O módulo não está ligado à partida: `+$86` tem
outros escritores, `$80:E4AD` possui uma exceção para outro tipo de ator, e
a origem e o significado completos de A/`+$84` ainda precisam de validação.
Também não se conclui o nome esportivo da ação. Próximo passo: rastrear os
escritores de `+$84` e comparar a escolha em cenários distintos antes de
aplicar o modelo ao jogo web.

### Seleção observada dos scripts de ação — 02/11/2026

O coletor aceita `ISSD_AUTO_SELECTION_TRACE=1` para acompanhar os pontos
`$84:968B`, `$80:E4C7`, `$84:E600` e `$84:E60C` quando o registrador direct
page aponta para o ator de P2. Em três replays do mesmo estado, após X foi
observada a passagem por `$84:968B`, `$80:E4C7` e `$84:E600` no mesmo passo.
No caminho observado, `$80:E4C7` troca os bytes de `+$86`, aplica `$0007` e
coloca o resultado em X. `$84:968B` usa X como deslocamento em bytes nas
tabelas de palavras `$81:C510` (controle) e `$81:C520` (script), antes do
despacho para `$84:E600`.

| Preparação | `+$86` | Deslocamento X | Controle em A | Script em Y |
| --- | --- | ---: | --- | --- |
| DownRight | `$0000` | 0 | `$D0F2` | `$D007` |
| DownLeft | `$0282` | 2 | `$D169` | `$D1C5` |
| UpLeft | `$0481` | 4 | `$D169` | `$D16E` |

`tools/analyze_issd_action_selector.py` confere os valores observados com as
tabelas na ROM local, nos offsets LoROM sem cabeçalho `0xC510` e `0xC520`, e
rejeita captura incompleta, hooks indisponíveis e offsets ímpares. Os três
casos corresponderam às tabelas; detalhes e hashes estão em
`issd-action-selector-{downright,downleft,upleft}.json`. O campo `+$86`
participa da escolha neste caminho, mas seu significado completo e seus
escritores ainda não foram estabelecidos; ele não deve ser reduzido a uma
direção nem conectado diretamente à física web. Não foi estabelecido o nome
esportivo dessas ações. Próximo passo: investigar como o jogo preenche esse
campo e em quais condições cada valor é produzido.

### Captura de X após deslocamentos diagonais — 02/11/2026

`ISSD_AUTO_P2_MOVE` aceita também `UpRight`, `UpLeft`, `DownRight` e
`DownLeft`, pressionando os dois direcionais simultaneamente durante a
preparação. Os testes usam o mesmo savestate e mantêm a ação X na janela
anterior; não estabelecem que o vínculo `$00A6` seja uma definição universal
de posse.

- `Left` produziu `$D007` na direção nativa 4: cinco descritores distintos
  foram comparados com correspondência exata. Outros dois passos foram
  recusados porque os slots candidatos do espelho não coincidiam com a PPU;
  não se afirma uma sequência completa de seis poses.
- `DownRight` produziu `$D007` na direção nativa 1 e seis descritores. Dos
  22 frames da ação comparáveis, 21 coincidiram diretamente; no outro, seis
  pixels divergentes coincidiram com cores de slots anteriores, sugerindo
  cobertura. Isso não comprova a camada ou a prioridade sem outras evidências.
- `UpRight` não produziu `$D007`; na janela da ação, o ator estava em outro
  estado e `$00A6` apontava para outro objeto. A tentativa não serve para
  inferir poses desse script.
- `UpLeft` e `DownLeft` produziram, respectivamente, scripts `$D16E` e
  `$D1C5` na janela; não são tratados como poses `$D007` nem como ações
  esportivas nomeadas. Esses caminhos precisam de investigação própria.

Os resultados por frame e os hashes estão em
`issd-bsnes-x-move-{left,upright,upleft,downright,downleft}-frame-audit.json`
e `issd-bsnes-x-downright-occlusion-audit.json`. O comparador de replay
foi refinado: ele exige igualdade dos slots candidatos entre espelho e PPU,
registrando diferenças no restante do OAM, e continua comparando os pixels
com a screenshot. Slots candidatos divergentes são recusados. Não foi
gerada uma folha completa para essas direções nem alterada a animação web.
Próximo passo: recuperar os frames recusados e entender a seleção dos scripts
alternativos em outras condições e direções.

### Comparação com a imagem do replay neutro — 02/11/2026

Os três frames finais divergentes de `$D007` no replay `Up` têm 8, 37 e 38
pixels divergentes, todos localizados entre x=221–238 e y=197–207. No mesmo
frame da captura neutra, todos esses pixels têm a mesma cor observada no
replay de ação. A região coincide visualmente com a interface inferior; a
comparação reforça a hipótese de cobertura por essa interface, mas a cor
igual não identifica por si só a camada ou a regra de prioridade da PPU.
`tools/audit_issd_reference_overlap.py` reproduz a comparação; o relatório é
`issd-bsnes-x-up-reference-overlap.json`. Os replays usam entradas e posições
diferentes, portanto essa análise compara somente a cor na mesma coordenada.

Cada um dos seis descritores da direção 6 possui ao menos um frame com todos
os pixels candidatos coincidentes. `tools/export_issd_validated_replay_sheet.py`
agora escolhe o primeiro frame exato de cada descritor e recusa a exportação
se algum descritor não tiver frame exato; ele não utiliza os frames
divergentes para montar a imagem. Foi gerada a folha transparente local
`analysis/issd-x-direction-6-diagnostic.png`, além da direção 0 anterior.
Ela conserva as cores da captura e não prova que todas as peças ocultas foram
recuperadas; as células usam uma área comum da tela, não uma âncora validada.
Não houve integração web nem distribuição das folhas. Próximo passo: obter
outras direções e uniformes e determinar os índices e âncoras antes de
preparar uma integração fiel.

### Sobreposição e segundo banco OBJ — 02/11/2026

No frame 4277 do replay com deslocamento `Up`, a lista de desenho atribuiu ao
objeto candidato os slots 45–50. O slot 45 usa banco OBJ 5 e seus 14 pixels
opacos coincidem com a screenshot; ele se sobrepõe em 14 pixels ao slot 50,
que usa banco 1. O slot 50 isolado apresenta exatamente 14 pixels diferentes
da imagem final, enquanto a composição dos seis slots coincide. Isso mostra
uma peça usando outra paleta sobre uma peça do próprio intervalo candidato;
a posição e a cor não bastam para identificá-la como cabelo, número ou
outro componente. Detalhes em `issd-bsnes-x-up-slot-layer-audit.json`,
gerado por `tools/audit_issd_slot_layers.py`.

`tools/audit_issd_candidate_occlusion.py` verifica, para cada pixel candidato
divergente, se um slot anterior possui a cor exata observada na screenshot.
Na direção 2, dos 22 frames comparáveis de `$D007`, 18 correspondem
diretamente e os quatro restantes têm todas as divergências explicadas por
essa comparação com slots anteriores. Na direção 6, 19 dos 22 correspondem
diretamente e três frames da pose final ainda apresentam 8, 37 e 38 pixels
sem explicação por esse método. Os relatórios são
`issd-bsnes-x-down-occlusion-audit.json` e
`issd-bsnes-x-up-occlusion-audit.json`.

Uma cor coincidente sugere sobreposição, mas não comprova sozinha sua causa;
o método não simula todos os limites e prioridades da PPU nem prova que todas
as partes do ator foram capturadas. Nenhuma recoloração automática ou nova
integração web foi feita. Próximo passo: investigar os três frames sem
explicação e obter capturas de outros uniformes para validar a seleção de
bancos separadamente.

### Paletas e direções adicionais no replay — 02/11/2026

`tools/audit_issd_action_palettes.py` compara os 16 valores de cada banco
OBJ usado nos slots candidatos com as paletas do catálogo extraído da ROM.
No replay de direção 0, as seis poses `$D007` usam somente o banco 1 e os
16 valores coincidem com a paleta do uniforme principal da Inglaterra no
catálogo. A comparação usa a convenção de conversão para RGB do catálogo;
um banco idêntico não prova, por si só, qual equipe possui o ator ou que
outras aparências possam usar a mesma substituição.

O coletor aceita `ISSD_AUTO_P2_MOVE=Up|Down|Left|Right` para variar o
deslocamento preparatório, mantendo `Right` como padrão. Partindo do mesmo
estado compartilhado e usando X, dois replays adicionais produziram `$D007`
nas direções nativas 6 (`Up`) e 2 (`Down`). Na direção 6, 22 dos 27 frames
comparáveis de toda a janela coincidiram nos pixels candidatos; na direção 2,
18 dos 27. A pose final `$A5D8` da direção 6 teve 13 de 16 amostras exatas;
as primeiras poses `$A683/$A68C/$A695` da direção 2 apresentaram diferenças.
Não se conclui a causa das divergências nem se elas representam erro de
composição, sobreposição ou sincronização.

No primeiro frame exato de cada pose da direção 6 apareceram os bancos 1 e 5:
o primeiro coincide com Inglaterra titular, enquanto o segundo não coincide
integralmente com nenhuma paleta de uniforme do catálogo. Isso é evidência de
que não é seguro substituir indiscriminadamente todos os bancos pela paleta
de uma equipe. A auditoria de paletas examina o primeiro frame exato de cada
descritor, não todos os seus frames posteriores; a auditoria de pixels deve
ser consultada junto. Resultados e hashes estão em
`issd-bsnes-x-action-palette-audit.json`,
`issd-bsnes-x-move-up-palette-audit.json` e
`issd-bsnes-x-move-{up,down}-frame-audit.json`. Não houve nova spritesheet
ou alteração no jogo web. Próximo passo: determinar a origem e função do
banco 5, isolar diferenças nos frames e comparar outros uniformes.

### Comparação da folha web com o replay — 02/11/2026

O caminho de locomoção escolhe imagens por seleção e uniforme, mas
`getActionImage` usa somente ação e direção: a mesma folha de ação é usada
para ambos os times e uniformes. O catálogo contém paletas, porém a captura
atual não valida ainda como todas as partes da folha de ação devem receber
cada paleta ou os atributos individuais; não foi introduzida uma recoloração
automática especulativa.

`tools/compare_issd_sheet_masks.py` compara as máscaras de transparência de
cada quadro, ignorando cores e escolhendo a melhor translação inteira para
medir forma. A folha diagnóstica de seis poses da direção nativa 0 foi
comparada à folha local `dist/assets/issd/actions/D007/direction-0.png`:
nenhuma das seis máscaras coincide integralmente após translação. O
resultado por quadro e os hashes estão em
`issd-x-action-sheet-mask-comparison.json`. Na primeira pose, 224 pixels
coincidem, 115 aparecem apenas na referência e 103 apenas na folha atual.

Essa comparação não valida âncora, cor ou tempo e não prova qual fonte
contém todas as peças; a referência também pode ter partes ocultas ou
indesejadas. As folhas atuais são experimentais e não foram substituídas.
Próximo passo: capturar um cenário com jogadores separados e confirmar
composição e paletas de diferentes equipes/uniformes antes de gerar e
integrar variantes de ações específicas.

### Correção de sobreposição na versão web — 02/11/2026

Na comparação da folha capturada com o renderer, foi identificado em
`dist/game.js` um erro independente da ROM: ao desenhar uma imagem de ação,
o `else` ligado à condição de locomoção também desenhava o jogador provisório
por cima da imagem. Agora o desenho provisório ocorre somente quando nem a
imagem de ação nem a folha de locomoção puderem ser usadas. Um teste sobre a
função real `drawPlayer` reproduziu a falha antes da correção e verifica os
três caminhos: ação disponível, locomoção disponível e reserva.

Essa correção remove uma sobreposição indevida; ela não valida a fidelidade
das folhas de ação existentes, suas cores por equipe, seus tempos ou o
mapeamento de comando. A folha diagnóstica capturada não foi instalada como
asset universal, pois representa um único uniforme e uma única direção.

### Comparação de pixels corrigida no mesmo replay — 02/11/2026

A captura `analysis/bsnes-x-combined/issd-auto-probe-20261102-213333.jsonl`
registrou simultaneamente a lista de desenho e os gráficos do replay de X.
`tools/compare_issd_replay_oam_frames.py` relaciona o intervalo de pilha ao
espelho preparado no mesmo passo e exige que ele coincida com o OAM da PPU no
frame seguinte antes de comparar pixels com a screenshot. Dos 28 intervalos
do ator `$1900`, 27 tinham os dados necessários e todos os seus pixels
candidatos não transparentes coincidiram exatamente; um não tinha o frame PPU
seguinte na janela. As seis poses `$A617/$A620/$A629/$A632/$A63B/$A644`
estão representadas. O relatório com hashes é
`issd-bsnes-x-combined-frame-audit.json`.

A comparação anterior com 211 de 339 pixels utilizava conversão incorreta
de cores: multiplicação com truncamento, enquanto a screenshot dessa
execução usa replicação dos bits de 5 para 8. Com a conversão corrigida, no
frame 4277 os 339 pixels candidatos coincidiram. Há teste específico para a
conversão e o relatório atualizado é
`issd-bsnes-x-combined-pixel-comparison.json`. O relatório antigo permanece
como registro histórico do comparador anterior e não deve ser usado como
resultado da versão corrigida.

Após essas verificações, `tools/export_issd_validated_replay_sheet.py` gerou
em `analysis/issd-x-direction-0-diagnostic.png` uma folha transparente local
de seis poses, baseada nos pixels e nas cores desse replay. A ferramenta
recalcula a comparação e recusa quadros com pixels divergentes. A folha é
diagnóstica: a igualdade dos pixels candidatos não garante ausência de peças
ocultas ou faltantes, e a paleta é a do contexto capturado. Não representa
todas as direções, uniformes ou tempos; não foi integrada ao jogo web nem
adicionada à distribuição. Próximo passo: validar cobertura completa e
capturar outras direções e uniformes usando a mesma associação.

### Comparação de pixels dos slots candidatos — 02/11/2026

`tools/compare_issd_oam_pixels.py` compõe os slots informados usando OAM e
CGRAM da PPU, VRAM do frame, OBJSEL, transparência de índice zero e paletas
OBJ na segunda metade da CGRAM. O comparador testa igualdade RGB com a
screenshot de 256×224; não tenta reproduzir toda a prioridade, cor e mistura
do SNES. Testes verificam paleta OBJ, transparência e rejeição de slots
duplicados.

Para os slots candidatos 36–41, derivados da execução do objeto `$1900` no
passo 4481, foi comparado o frame 4277 da PPU (o espelho registrado no frame
4276 coincide com o OAM dessa PPU). De 339 pixels opacos candidatos, 211
coincidiram exatamente com a screenshot e 128 não coincidiram. O resultado
reproduzível com hash está em `issd-bsnes-x-oam-pixel-comparison.json`.

O resultado é compatível com parte da composição, mas **não valida a pose**:
os slots foram inferidos em outro replay do mesmo estado, há elementos
sobrepostos, a sincronização exata da screenshot e da VRAM não foi provada,
e o comparador não simula todos os efeitos e prioridades da PPU. Não há
evidência suficiente para atribuir a diferença a uma causa única. Não foi
gerada spritesheet nem alterada a versão web. Próximo passo: capturar
instrumentação e gráficos no mesmo replay, testar sobreposições e prioridades
e identificar o que explica os pixels divergentes.

### Candidatos de OAM pela lista de desenho — 02/11/2026

O coletor aceita `ISSD_AUTO_DRAW_TRACE=1` para registrar a entrada em
`$80:95E3`: ponteiro da lista, objeto e registrador de pilha. No caminho
`$80:957B`, o disassembly inicia a pilha em `$03DF`; o construtor empilha
quatro bytes por peça antes de avançar na lista. O trace da mesma sequência,
`analysis/bsnes-draw-trace/issd-auto-probe-20261102-212857.jsonl`, foi
coletado em uma repetição independente do mesmo estado.

No passo lógico 4481, o objeto `$1900` entrou com pilha `$034F` e o próximo
objeto entrou com `$0337`: sob esse caminho, isso corresponde a seis entradas
candidatas, slots 36–41. O espelho produzido após esse passo equivale ao OAM
da PPU do frame seguinte, conforme a comparação anterior. A imagem desse
momento apresenta jogadores sobrepostos; portanto localização e mudança de
slots, por si sós, não garantem que uma composição isolada reproduza a imagem
final. Em alguns frames não houve callback do construtor, e isso não implica
que o objeto estivesse invisível.

`tools/analyze_issd_draw_trace.py` valida limites e alinhamento da pilha e
registra os intervalos candidatos em `issd-bsnes-x-draw-slot-candidates.json`.
Durante a tentativa de validação visual foi corrigido um erro no
`decode_tile` de `tools/render_issd_oam_composite.py`: uma linha comentada
acidentalmente impedia a definição do offset do tile. Um teste verifica o
decodificador 4bpp com base OBJ acima do tile 511. Ainda falta validar pixels,
prioridade e transparência contra a screenshot, especialmente quando jogadores
se sobrepõem; não foi produzida uma spritesheet nem mudado o jogo web.

### Sincronização dos espelhos com a PPU — 02/11/2026

Com `ISSD_AUTO_GRAPHICS_EVERY_FRAME=1`, uma repetição do mesmo estado coletou
29 frames consecutivos, relativos 477–505, incluindo antes e depois de
`$D007`. Além de OAM, VRAM e o espelho CGRAM em WRAM, o domínio `CGRAM` da
PPU estava disponível e foi gravado com 512 bytes por frame. A integridade
dos arquivos foi verificada antes da comparação.

Para os 28 pares disponíveis, o espelho OAM normalizado do frame `t` foi
idêntico byte a byte ao OAM da PPU em `t+1`. A comparação no mesmo frame teve
apenas uma igualdade em 29 pares. O espelho CGRAM de `t` também foi idêntico
ao CGRAM da PPU em `t+1` nos 28 pares; no mesmo frame houve 25 igualdades em
29. Os resultados e diferenças para deslocamentos de -2 a +2 estão em
`issd-bsnes-x-frame-sync-audit.json`, gerado por
`tools/analyze_issd_graphics_replay.py` a partir dos arquivos locais em
`analysis/bsnes-x-graphics-frames/`.

Isso sustenta uma defasagem observada de um frame nessa execução e explica as
diferenças entre espelho e PPU registradas anteriormente, sem provar que a
regra se aplique a todos os núcleos ou estados. Também não associa slots ao
jogador nem garante a sincronização da screenshot com os dados da PPU. A
próxima análise deve agrupar slots e comparar pixels usando o OAM e paleta
da PPU apropriados; nenhuma spritesheet ou física web foi alterada.

### Captura gráfica associada ao replay de X — 02/11/2026

O coletor aceita `ISSD_AUTO_CAPTURE_GRAPHICS=1` somente quando usa um estado
de replay. Para cada descritor `$D007` distinto do ator de P2 na janela
relativa 477–505, ele registra após `emu.frameadvance()` o espelho OAM de
544 bytes, OAM da PPU quando disponível, VRAM, espelho CGRAM da WRAM,
screenshot e metadados do ator. Cada conjunto é escrito em `analysis/`, não
é distribuído e tem o mesmo frame lógico nos metadados. Isso não garante que
as diferentes representações tenham sido atualizadas no mesmo instante da
renderização interna.

A captura `analysis/bsnes-x-graphics/issd-auto-probe-20261102-212409-graphics.jsonl`
contém seis descritores da direção 0; o validador de tamanho e presença passou
sem erros. O relatório `issd-bsnes-x-graphics-audit.json`, gerado por
`tools/analyze_issd_graphics_replay.py`, compara o espelho normalizado com o
OAM da PPU: `$A617` apresenta 128 bytes diferentes, `$A620` 111, `$A629` 23,
`$A632` zero, `$A63B` 140 e `$A644` 138. São diferenças em 544 bytes totais,
não uma contagem de sprites incorretos. As causas e a relação temporal ainda
precisam ser verificadas. O CGRAM capturado é o espelho em WRAM, não foi
confirmado como paleta da PPU na imagem. O OAM inclui todos os objetos e ainda
não há associação comprovada dos slots ao ator.

Portanto, a integridade dos dumps não valida os PNGs ou a montagem do jogador.
Não foi produzida nova spritesheet nem alterado o jogo web. Próximo passo:
comparar OAM de frames adjacentes, sincronização da transferência à PPU e
slots efetivos do ator antes de confrontar os gráficos do navegador.

### Descritores de X quadro a quadro — 02/11/2026

Com `ISSD_AUTO_ACTION_EVERY_FRAME=1`, o coletor registra cada frame entre os
passos relativos 470 e 520, mantendo a amostragem normal fora da janela.
Uma nova execução de X a partir do mesmo estado compartilhado registrou, no
ator `$1900`, script `$D007` e direção nativa 0, com 51 frames consecutivos:

| Descritor | Início relativo | Duração observada em frames |
| --- | ---: | ---: |
| `$A617` | 480 | 2 |
| `$A620` | 482 | 1 |
| `$A629` | 483 | 1 |
| `$A632` | 484 | 2 |
| `$A63B` | 486 | 1 |
| `$A644` | 487 | 16 |

No passo 503 houve mudança para script `$D320`, portanto início e fim de
cada intervalo da tabela foram observados nessa execução. A sequência de
descritores coincide com os seis primeiros da direção 0 em
`dist/data/issd-action-descriptors.json`, derivado da ROM. Os tempos divergem
dos valores de prévia de `dist/action-visual.mjs`, que usa multiplicador e
última duração provisórios. Uma única jogada não permite assumir que esses
tempos sejam universais, e os metadados do ator não comprovam montagem OAM,
paleta ou aspecto visual dos PNGs. Não foi alterada a animação web.

`tools/analyze_issd_replay_animation.py` exige amostras e números de frame
consecutivos e identifica durações delimitadas ou limitadas pela janela. O
resultado e hash da captura estão em `issd-bsnes-x-animation-timing.json`.
Próximo passo: repetir em outras direções e condições e capturar OAM/VRAM/CGRAM
do mesmo frame antes de aplicar tempos ou substituir gráficos.

### Quatro botões sob o mesmo estado inicial — 02/11/2026

As execuções de A, B e Y foram repetidas a partir do mesmo savestate usado
para X e comparadas ao mesmo controle neutro. Nos quatro casos, houve 240
amostras anteriores iguais nos campos observados, confirmação do botão e
três amostras neutras no controle correspondente. A tabela resume somente
o resultado neste cenário, com a configuração atual de botões:

| Botão | Estado do ator no passo 481 | Script no passo 481 | Tipo da bola no passo 485 | Primeira diferença no registro de bola |
| --- | --- | --- | --- | --- |
| A | `$0270` | `$D01F` | `$17` | 481 |
| B | `$0258` | `$D01F` | `$1E` | 481 |
| X | `$0140` | `$D007` | `$03` | 485 |
| Y | `$00B8` | `$D6DB` | `$00` | não observada nas 60 amostras posteriores |

Os valores da tabela são palavras da ROM; diferenças no registro da bola
incluem velocidade e tipo, não apenas posição. O resumo consolidado
`issd-bsnes-shared-state-action-matrix.json` é produzido por
`tools/summarize_issd_action_matrix.py`, que rejeita interpretações quando
a linha de base, a entrada ou o controle neutro não foram confirmados. O
arquivo inclui hashes dos traces e do savestate informado pelo operador;
o hash do estado não é autenticado pelo próprio trace. Os testes cobrem
linha de base incompatível e uma comparação válida.

O script `$D007` coincide com o atlas provisório atualmente usado no
navegador para chute; essa coincidência isolada não valida o nome do comando,
todos os quadros nem a física. Comandos são remapeáveis e o comportamento
pode variar conforme posse, altura da bola e estado do jogo. Nenhuma mudança
foi feita na jogabilidade web a partir desta matriz. Próximo passo: variar
estado e altura em replays controlados e correlacionar descritores OAM no
mesmo experimento antes de substituir as ações provisórias.

### Comparação de X a partir de um estado compartilhado — 02/11/2026

O coletor agora pode gravar, com `ISSD_AUTO_SAVE_TRIGGER=1`, um savestate
local quando a partida satisfaz as condições de início do experimento.
Com `ISSD_AUTO_REPLAY_STATE=<caminho>` e o cenário
`two_player_action_observation`, uma instância independente carrega esse
estado, verifica configuração e atores, e executa novamente a sequência.
O passo lógico de replay é 4001, escolhido para preservar a paridade das
amostras; o frame do emulador continua sendo o frame real do estado carregado.
O arquivo de estado não é distribuído e fica sob `analysis/`.

O estado `analysis/bsnes-shared-state/issd-auto-probe-20261102-211624-trigger.State`
tem SHA-256 `434aad71aee291e84d4116fca42c92647e44e3157dfa2a825c72a740f698e8f9`.
As duas instâncias independentes BSNES carregaram esse mesmo arquivo, uma com
X e outra neutra, e executaram a mesma preparação. Houve 240 amostras
anteriores iguais nos campos registrados e três amostras confirmando X apenas
na execução de ação. O primeiro registro de bola diferente ocorreu no passo
relativo 485. Em 481, o ator `$1900` passou de estado `$00B8` para `$0140`
e script `$D007`; em 485 a bola tinha tipo `$0003`, VZ `$FFF9` e vínculo
`$00A6=0`, enquanto no controle permanecia tipo zero e vinculada a `$1900`.
O callback em `$84:957E` registrou `D=$1900` e `+$6E=$1081` na ação.
As palavras são valores brutos, e as amostras ocorrem a cada dois passos.

Os resumos com hashes das duas capturas estão em
`issd-bsnes-shared-state-x-neutral-comparison.json`,
`issd-bsnes-shared-state-x-execution.json` e
`issd-bsnes-shared-state-neutral-execution.json`. A linha de base comum e a
entrada distinta fortalecem a comparação nesse caso; não estabelecem o nome
esportivo do comando, nem comportamento em outras condições. Nenhuma regra
ou física web foi alterada. Próximo passo: repetir A, B, X e Y a partir do
mesmo estado em cenários variados e ligar as saídas a eventos validados.

### Botões X e Y e validação da linha de base — 02/11/2026

Foram executados mais dois testes BSNES, com X e Y de P2, comparados ao
controle neutro anterior. A ferramenta `compare_issd_action_trials.py`
aceita `--action-mask` para verificar a máscara física testada; também
informa separadamente diferenças de posição e diferenças em todo o registro
de bola capturado, incluindo tipo e velocidade, quando esses campos existem.

No teste Y (`--action-mask 0x4000`), o controle recebeu Y nas três amostras
do pulso e o neutro estava sem botão. As 240 amostras anteriores coincidiram
nos campos registrados; nas 60 amostras posteriores comparadas, nenhuma
diferença foi observada no registro de bola. Não houve callback nos nove
endereços monitorados na janela relativa 460–540. Isso não demonstra que Y
nunca tenha efeito: o resultado vale apenas para esse cenário, configuração,
intervalo, campos e endereços monitorados.

No teste X (`--action-mask 0x40`), o botão chegou ao jogo, porém todas as
240 amostras anteriores diferiram da execução neutra; os atores associados
e a situação da bola já eram outros antes do pulso. O teste não permite
atribuir diferenças posteriores a X. Repetir com estado inicial compartilhado
ou uma linha de base neutra compatível antes de tirar conclusão. Os resumos
locais com hash estão em `issd-bsnes-button-x-summary.json`,
`issd-bsnes-button-y-summary.json` e nos arquivos
`issd-bsnes-button-{x,y}-neutral-comparison.json`. Não houve mudança na
simulação web.

### Comparação entre botões físicos A e B — 02/11/2026

O coletor aceita `ISSD_AUTO_P2_BUTTON=A|B|X|Y` para variar somente o botão
de ação do segundo controle; a confirmação dos menus continua usando A.
Dois testes BSNES, com A e B respectivamente, tiveram 240 amostras prévias
iguais nos campos registrados e o mesmo gatilho no passo 3795. Os registros
confirmam `$0080` para A e `$8000` para B nas três amostras da janela.
O teste B não é neutro: o comparador agora informa separadamente se a
segunda execução está sem botões; `p2_action_input_confirmed` refere-se
à máscara escolhida (por padrão o bit A), não à neutralidade de B.

No ator `$1900`, o callback em `$84:957E` observou `+$6E=$2081` para A e
`+$6E=$4081` para B. O [disassembly](../YFs_InternationalSuperstarSoccerDeluxe_Disassembly/International_Superstar_Soccer_Deluxe/Routine_Macros_ISSD.asm)
em `$84:9755` testa `$4000`; no caminho A observou-se estado `$0270`, passagem
por `$85:F410` e entrada em `$85:F8B9` com `X=$0017`. No B observou-se
estado `$0258`, passagem por `$85:F3FE` sem evento em `$85:F410` e entrada
em `$85:F8B9` com `X=$001E`. No passo relativo 483, a bola foi amostrada
com tipo `$17` e VZ `$FFFC` para A, e tipo `$1E` e VZ `$FFFE` para B.
Os valores são palavras brutas, não velocidades calibradas.

Os resumos `issd-bsnes-button-a-summary.json`,
`issd-bsnes-button-b-summary.json` e `issd-bsnes-button-ab-comparison.json`
contêm eventos e hashes das capturas locais. Em `$83:94A4`, o direct page
já foi zerado pela rotina anterior; nesse ponto `action_word` lê a página
zero e não representa o campo de um ator. O mesmo campo nos callbacks com
`D=$1900` pertence ao ator identificado.

Esses resultados distinguem dois caminhos no cenário e configuração de
controles testados, mas não estabelecem os nomes passe/chute nem a conversão
dos valores para o navegador. Controles remapeáveis e outras condições de
bola podem alterar a escolha. Nenhuma física web foi alterada.

### Ator identificado e controle neutro no mesmo núcleo — 02/11/2026

O primeiro coletor tentava `memory.getregister`, que não é a API de leitura
de registradores usada pelo BizHawk. Corrigido para `emu.getregister`,
documentado na [implementação da versão local](https://github.com/TASEmulators/BizHawk/blob/427556b5ef3ac437eba754d90c5e7e9096c9a8df/src/BizHawk.Client.Common/lua/CommonLibs/EmulationLuaLibrary.cs).
Em duas instâncias BSNES independentes, ambas chegaram ao gatilho 3795:
`analysis/bsnes-action/issd-auto-probe-20261102-210248.jsonl` com A de P2
e `analysis/bsnes-neutral/issd-auto-probe-20261102-210248.jsonl` sem A.

Foram iguais 240 amostras anteriores nos campos registrados; há três
amostras com A apenas no experimento de ação. A primeira diferença amostrada
na bola ocorre no passo relativo 481. Entre os passos relativos 460 e 540,
os seis hooks estavam registrados nos dois testes: houve 23 eventos no teste
de ação e nenhum no neutro. No teste de ação, o registrador direct page
`D=$1900` identifica o ator P2 nos pontos `$84:9473`, `$84:9755`, `$84:979F`,
`$85:F3FE`, `$85:F410` e `$85:F8B9`. Na entrada de `$85:F8B9`, `X=$0017`,
`$0430=0` e `$00A6=$1900`; no passo seguinte, `$0430=$0017` e `$00A6=0`.
As leituras dos callbacks são anteriores à instrução registrada, e outros
passos de execução podem ocorrer entre callbacks.

Os resultados estão em `issd-bsnes-action-neutral-comparison.json`,
`issd-bsnes-action-register-summary.json` e
`issd-bsnes-neutral-register-summary.json`. A igualdade é limitada aos campos
amostrados, não a toda a memória. O resultado sustenta causalmente a transição
nesse cenário específico e a associação ao ator, mas ainda não demonstra o
nome esportivo do comando nem autoriza generalizar a fórmula física para
outras situações. O próximo passo é mapear o comando configurável e medir
os dados de entrada da rotina e seus efeitos em estados variados.

### Rastreamento de instruções com BSNES — 02/11/2026

O BizHawk local 2.11 (`427556b5`) usava Snes9x na configuração original.
Uma cópia isolada em `analysis/` selecionou `BSNESv115+` e habilitou o
gamepad na segunda porta. O [código do BSNES dessa versão](https://github.com/TASEmulators/BizHawk/blob/427556b5ef3ac437eba754d90c5e7e9096c9a8df/src/BizHawk.Emulation.Cores/Consoles/Nintendo/BSNES/BsnesCore.ISettable.cs)
define a segunda porta como `None` por padrão: enquanto estava desconectada,
os pulsos de P2 não chegavam e a seleção de dois jogadores não avançava.
`ISSD_AUTO_EXTENDED_MENU=1` permite continuar os pulsos de menu dos dois
controles até a partida; o comportamento padrão do coletor não mudou.

Na captura `analysis/issd-auto-probe-20261102-205946.jsonl`, os seis hooks
obtiveram identificadores válidos e o experimento começou no passo 3795.
No passo relativo 480 foram registrados `$84:9473` e `$84:9755`; no 481,
`$84:979F`; no 482, novamente `$84:979F`, seguido de `$85:F3FE`, `$85:F410`
e `$85:F8B9`, nessa ordem. Nos callbacks desse passo a bola ainda tinha tipo
zero e `$00A6=$1900`; no passo 483, uma nova entrada em `$84:979F` já
mostrou tipo `$17` e `$00A6=0`. O callback é anterior à instrução observada.
O resumo reproduzível, com todos os eventos e hash da captura local, está em
`issd-action-execution-bsnes-summary.json`, gerado por
`python tools/analyze_issd_execution_trace.py <trace> --output <resumo>`.

Comparada ao controle neutro anterior em Snes9x, a execução BSNES apresentou
240 amostras anteriores iguais nos campos registrados, três amostras de A
apenas no experimento de ação e primeira diferença na bola no passo relativo
481. São núcleos diferentes e a comparação não prova igualdade integral do
estado. Os hooks registram execução global e os registradores ficaram `null`:
por isso a atribuição de cada chamada ao ator `$1900` é compatível com a
sequência observada, mas não está diretamente comprovada. Também não está
estabelecido se A representa passe ou chute. Ainda não houve alteração na
física web. O próximo passo é recuperar o registrador direct page ou outro
identificador do ator no callback, e comparar com um controle neutro no
mesmo núcleo.

### Tentativa de rastreamento de instruções — 02/11/2026

O coletor `tools/automate_issd_probe.lua` aceita `ISSD_AUTO_TRACE_EXEC=1`
para tentar registrar execução nos endereços CPU `$84:9473`, `$84:9755`,
`$84:979F`, `$85:F3FE`, `$85:F410` e `$85:F8B9`, durante os passos
relativos 460–540 do experimento. Cada evento inclui registradores quando
disponíveis, tipo da bola `$0430` e vínculo `$00A6`. Identificadores vazios
dos callbacks são registrados como falha; ausência de eventos não demonstra
que as instruções não foram executadas.

Na sessão local `analysis/issd-auto-probe-20261102-171500.jsonl`, os seis
registros retornaram GUID zerado e nenhum evento de execução foi observado.
O arquivo dessa tentativa foi criado antes da correção da verificação de GUID,
por isso seus campos `success: true` não devem ser interpretados como sucesso.
Não foi possível estabelecer se a limitação vem do core, domínio ou API.

A comparação com `analysis/issd-auto-probe-20261102-171057.jsonl` usando
`python tools/compare_issd_action_trials.py <ação> <neutro> --output <json>`
encontrou 240 amostras anteriores iguais nos campos registrados, três amostras
com A apenas no teste de ação e primeira diferença na bola no passo relativo
481. A igualdade não garante que todo o estado interno seja idêntico. Essa
repetição reforça a observação da transição, mas não comprova a chamada de
`$85:F3FE` nem se o comando corresponde semanticamente a passe ou chute.
Não houve mudança na física ou nas animações do navegador. Próximo passo:
investigar suporte a callbacks no core e, se necessário, usar outro método de
rastreamento reproduzível sem alterar a configuração do usuário.

### Registro separado do controle e dos atores — 02/11/2026

O script schema v2 agora registra os cinco registros de controle e os 22
slots de atores, incluindo coordenadas inteiras e fracionárias. Os comandos
Right, Left, Up e Down são enviados pelo controle P1 **sem verificar posse
de bola**. `tools/analyze_issd_auto_control.py` acompanha o ator apontado
por `+$2C` do registro `$1AA0`, além do candidato `$1ACC` e do vínculo
`$00A6`. Isso separa o jogador associado ao controle do jogador relacionado
à bola; `$00A6` não foi validado como definição universal de posse.

Na execução `analysis/issd-auto-probe-20261102-162636.jsonl`, foram
registradas 60 amostras em cada direção. O controle `$1AA0` apontou para
`$0E00`, com entrada não zero nas quatro direções. Entre 59 pares consecutivos
por direção, as palavras de posição inteira/fracionária mudaram em 55
(Right), 52 (Left), 56 (Up) e 51 (Down). Isso esclarece a observação anterior:
olhar somente as coordenadas inteiras não mostrava todas as mudanças. Ainda
não há conversão de unidades, comparação causal com um estado repetido nem
medida de velocidade que possa ser aplicada ao navegador.

Nessa coleta, `$00A6` apontou para o mesmo ator durante os comandos. Uma
segunda tentativa, `analysis/issd-auto-probe-20261102-162848.jsonl`, enviou
B antes das direções, mas não demonstrou transferência para outro ator;
as contagens de movimento permaneceram iguais. Portanto **a situação de
CPU com a bola ainda não foi validada**. As saídas resumidas com hashes são
`docs/issd-auto-control-summary.json` e
`docs/issd-auto-control-action-summary.json`. Capturas brutas ficam em
`analysis/` e as instâncias de teste foram encerradas.

Dois testes de `test_issd_auto_control.py` verificam mudança na parte
fracionária, ponteiros diferentes e rejeição de passos repetidos. A auditoria
documental passou. Nenhuma constante da mecânica web foi alterada.

Próximo passo: criar uma sequência que aguarde durante a partida até o vínculo
relacionado à bola ser diferente do ator do controle, sem usar isso como
prova isolada de posse, e então executar movimentos. Correlacionar imagem,
estado e vínculo para confirmar visualmente a CPU com a bola; se esse evento
não ocorrer dentro do limite, registrar a tentativa sem fabricar resultado.

Capturar, no mesmo experimento e em todos os atores, os campos de controle
`$1AA0..$1B60`, ponteiro do ator em `+$2C`, flags `+$2E`, `$1ACC`, estados
e coordenadas inteiras/fracionárias; verificar qual registro realmente
recebe o controle e por que a posição observada ficou parada. Comparar
repetições de sequências neutra/direita a partir de um estado reproduzível
antes de converter unidades ou alterar a velocidade web. Não é necessário
pedir ao usuário que repita caminhada nesta etapa.
