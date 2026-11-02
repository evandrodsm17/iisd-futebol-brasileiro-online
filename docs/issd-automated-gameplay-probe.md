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

O script injeta entradas de teste e lê WRAM; não modifica a ROM nem a RAM do
jogo. Registra modos, entrada recebida, configuração de jogadores, ator
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
