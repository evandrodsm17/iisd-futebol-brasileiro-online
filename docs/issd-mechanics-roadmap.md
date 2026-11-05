# Roteiro de mecânica fiel — ISS Deluxe

Para prioridades e acompanhamento de implementação, consulte o
[checklist de física, eventos e animações](issd-checklist-fisica-animacoes.md).

## Pontos de entrada confirmados

| Sistema | ROM / RAM | Papel |
| --- | --- | --- |
| Filtro de ator por fase | `$7E:00C0` → `$83:CF86` | Gate de 15 entradas; não é a máquina completa de fases |
| Fase secundária | `$83:F375` | Continuação do dispatch de fase |
| Colisão/física | `$83:D77F` | Modos de colisão e bola |
| Trajetória | `$83:D9A5` | Bola, trave e rede |
| Mergulho GK | `$83:DCAA` | Defesa baixa/alta do goleiro |
| Captura GK | `$83:DDA1` | Segurar e proteger a bola |
| Sequenciador de jogador | `$84:A35F` | Seleção/composição de animação |

## Ordem de reconstrução

1. Registrar fase e registros de bola/jogador ao longo de jogo natural.
2. Substituir posse e bola livre pelo modo de colisão observado.
3. Ligar passe/chute às trajetórias observadas.
4. Integrar goleiro, rede e trave.
5. Tratar faltas, reinícios e cartão pelo dispatch de fase.

Nenhuma etapa promove uma regra do protótipo a comportamento final sem uma
rotina, tabela ou captura correspondente da ROM USA.

O código web atual mantém bola livre, posse por proximidade, atrito, quique e
reinícios apenas para que a tela de partida seja navegável. Eles não são
equivalentes à máquina da ROM e devem ser substituídos — e não ajustados por
sensação — conforme os handlers e registros forem recuperados.

## Melhorias jogáveis provisórias — contato e saídas

O protótipo agora resolve sobreposição entre atletas após seus deslocamentos,
com uma área elíptica de contato em unidades do navegador, redistribuição de
posição dentro dos limites e remoção apenas da velocidade de aproximação.
`dist/player-contact.mjs` usa quatro passagens para lidar com grupos. Raios,
resposta, massa e tratamento de contato são valores provisórios; não se trata
de atrito, disputa corporal, falta ou física de contato da ROM. Em aglomerações
extremas, quatro passagens não garantem ausência absoluta de sobreposição.

`dist/field-events.mjs` classifica a primeira linha cruzada pela trajetória da
bola e distingue lateral, gol, escanteio e tiro de meta pela última equipe a
tocar. Usa o campo lógico do protótipo, raio de bola 4,7 e altura de travessão
24 unidades, ainda sem calibração nativa. Cruzamento simultâneo de duas linhas
é resolvido por ordem determinística, não por regra original comprovada. As
reposições continuam imediatas; posicionamento, cobrança e fases originais
seguem pendentes.

O botão de pressão permite ao jogador controlado tomar posse de uma bola no
chão que pertença ao adversário quando passa pelo teste de contato já adaptado
de `84:E8B0`; o intervalo de 420 ms e a transferência são provisórios. Não há
animação ou máquina de estados de carrinho implementada por essa ação. O teste de contato da bola possui evidência própria,
mas isso não valida a regra de roubo nem os resultados da colisão entre atletas.

Os testes `dist/test-player-contact.mjs`, `dist/test-field-events.mjs` e
`dist/test-ball-steal.mjs` cobrem separação, limites, posse e decisões de
saída. O próximo passo é confrontar contato, carrinho, trajetórias e reinícios
com registros da ROM antes de trocar essas aproximações por suas máquinas.

### Investigação do contato durante carrinho

Na rota `84:A056 → 84:A08D`, a ROM instala `$70=12`, `$72=8` e o script
`82:DB25`. Quando o ator não é o apontado por `$00A6`, o handler decrementa
`$70`; no intervalo resultante de 0 a 7 e com bits `$0420` de `$6E` limpos,
ele chama a verificação `85:F11A`. Há uma chamada anterior a `84:E8B0`: se
ela retorna carry limpo, `85:F125` é executada antes e pode alterar o estado.
Portanto a janela, sozinha, não determina um roubo ou uma falta.

`85:F11A` seleciona a tabela `81:CF6B`, cujas primeiras seis words são
`12,24,8,16,8,16`, e entra na verificação compartilhada `85:FAEA/FAF1`.
Ela aplica condições de fase e flags, testa as três coordenadas do ator e da
bola com offsets e marca `$0400` em `$6E` quando o volume é aceito. Valores
estão em unidades nativas, sem conversão calibrada para o campo web. O modelo
em `dist/native-slide-ball-gate.mjs` cobre a ramificação restrita em que a
verificação anterior retorna carry definido; o outro caminho permanece
explicitamente pendente, porque pode executar `85:F125` antes do teste.

Em replay isolado, oito chamadas ao gate compartilhado rejeitaram a bola fora
do volume, coincidindo com o modelo de aritmética de 16 bits. Uma nona aceitou
o contato e marcou `$0400` após ajuste **sintético** das coordenadas da bola na
RAM, restauradas antes do retorno. Essas chamadas ocorreram sob o script
`$DF7F`, não durante `$DB25`: validam a rotina compartilhada nesses exemplos,
mas ainda não demonstram um carrinho real, o botão de entrada nem seu resultado
físico. Evidência: `docs/issd-slide-ball-gate-probe.json`; tabela e ressalvas:
`dist/data/issd-slide-ball-gate.json`.

Testes adicionais comparam 500 entradas do modelo JavaScript com o modelo
Python existente e verificam as bordas e flags. O código continua fora do
jogo até haver correspondência de unidades e captura da sequência completa de
carrinho, contato e resposta.

### Entradas defensivas em replay controlado

Em cinco execuções isoladas do mesmo estado salvo, com dois jogadores humanos,
o jogador selecionado do P1 era `$0F00` e `$00A6` apontava para `$1900`,
do outro lado. Entre os passos relativos 480 e 485 foi pressionado apenas um
botão do P1; a execução de controle não recebeu botão. Antes disso, os 245
registros comuns observados são iguais nos campos comparados, incluindo
atores, scripts, controles e posição e velocidade da bola. As quatro
comparações confirmaram os seis quadros de entrada e a cobertura prevista.

| Entrada P1 | Estado e script observados no passo 480 | Passo 500 |
| --- | --- | --- |
| Nenhuma | `$0050`, `$DA56` | `$0050`, `$DA56` |
| A (`$0080`) | `$02C8`, `$DF7F` | `$02F8`, `$DB5B` |
| B (`$8000`) | `$02C0`, `$D110` | `$0050`, `$DA56` |
| X (`$0040`) | `$0050`, `$DA56` | `$0050`, `$DA56` |
| Y (`$4000`) | `$0050`, `$DA56` | `$0050`, `$DA56` |

Essas identificações são estados e scripts, não nomes comprovados de
movimentos. Em particular, a entrada A desta situação não iniciou o script
`$DB25` da rota acima; o uso do mesmo `$DF7F` que apareceu na investigação do
gate compartilhado não comprova que houve carrinho ou contato. A igualdade
dos campos registrados tampouco prova igualdade de toda a memória oculta, e os
resultados não generalizam para outras distâncias, direções, configurações de
controle ou condições de posse. O registro resumido, hashes e limitações estão
em `docs/issd-p1-defense-matrix.json`. O estado salvo e as capturas brutas
permanecem locais, fora da distribuição. A reprodução usa
`tools/automate_issd_probe.lua` com `ISSD_AUTO_P1_BUTTON` e o sumarizador
`tools/summarize_issd_p1_defense_matrix.py`.

Próximo passo: rastrear as condições que escolhem `$DF7F` ou `$DB25` e a
sequência de estados após contato real, antes de ligar qualquer entrada ou
consequência ao jogo web.

### Bifurcação das ações defensivas

Três novos replays passivos (A, B e controle) registraram a execução do ator
selecionado em pontos do banco `$84`. Para cada botão, 245 amostras anteriores
coincidiram com os campos ampliados registrados no controle; os seis quadros
do botão também foram conferidos. A execução do frame 4275 mostrou:

- Com A, `84:9FED` encontrou `$6E=$A080`, com bit `$4000` limpo, e passou a
  `84:A124`. Depois de `80:D56D`, `$68=10`, levando a `84:A136` em vez da
  entrada direta `84:A056`. A chamada `80:E450` retornou carry limpo e o
  resultado de `80:E46B` foi não zero; assim foi executado `84:A16E`, que
  preparou estado `$02C8` e script `$DF7F`.
- Com B, `84:9FED` encontrou `$6E=$C080`, com bit `$4000` ativo, e desviou
  para `84:A00C`, que prepara estado `$02C0` e script `$D110`.
- No controle, esses pontos de entrada não ocorreram naquele frame. A
  relação entre botão e bits internos é observada nessa condição específica;
  não é uma tabela universal de comandos.

O hook de `84:A08D` foi chamado no estado `$02C8` com script `$DF7F`, e o
gate de bola `85:FAEA` foi chamado nos frames 4280 a 4287. Portanto `84:A08D`
é compartilhado: sua execução, isoladamente, não prova que o estado é
`$02D0` nem que o script é `$DB25`. O hook do gate registra entrada, não
resultado da colisão. A prova anterior de rejeição natural e contato
sintético continua limitada aos testes documentados acima; ainda não há prova
de transferência de posse ou falta nesta ação. O resumo rastreável, hashes e
valores dos registradores estão em `docs/issd-defense-route-probe.json`;
o observador e a auditoria são `tools/probe_issd_defense_route.lua` e
`tools/audit_issd_defense_route.py`. Capturas brutas e ROM permanecem locais.

Falta provocar ou localizar a rota `$DB25` naturalmente, identificar o papel
de `$68` e dos cálculos `80:E450/80:E46B`, e capturar a resposta completa a
contato sem alterar a RAM. Esses resultados não substituem as aproximações de
colisão e roubo já presentes no navegador.

### Aproximação controlada e contato natural

Novos replays mantiveram o estado inicial e os comandos anteriores, mas
aplicaram um deslocamento ao P1 nos 40 quadros que antecedem a ação A. Para
as direções Right e DownRight houve um controle independente com a mesma
aproximação e sem o botão A. A auditoria encontrou 245 amostras anteriores
iguais nos campos registrados e confirmou os seis quadros da entrada; isso
não compara toda a memória nem prova identidade de estados ocultos.

- **Right:** a ação entrou em `$02C8/$DF7F`. No frame 4280, a chamada passiva
  a `85:FAEA` retornou carry limpo e o bit `$0400` apareceu em `$6E`, sem
  escrita sintética. Na primeira amostra seguinte, o vínculo `$00A6` mudou
  de `$1900` para o ator `$0F00`; no controle equivalente permaneceu `$1900`.
  A sequência prosseguiu por `$02F8/$DB5B`. Isso associa contato aceito e
  mudança de vínculo neste cenário, mas ainda não demonstra qual instrução
  escreveu o vínculo nem estabelece a regra geral de roubo.
- **DownRight:** a ação entrou naturalmente em `$02D0/$DB25`. As oito
  chamadas observadas ao gate nos frames 4280–4287 retornaram carry definido;
  não houve mudança de `$00A6` em relação ao controle nas amostras analisadas.
  Isso confirma a entrada natural e rejeições nesse contexto, não um contato
  aceito ou falta durante `$DB25`.

As direções são nomes de entrada do replay, não nomes de direção interna da
ROM. Os dados pareados, coordenadas, estados, flags, hashes e limitações estão
em `docs/issd-defense-approach-probe.json`; a reprodução usa
`ISSD_AUTO_P1_APPROACH` com `tools/automate_issd_probe.lua`, o observador
passivo `tools/probe_issd_slide_ball_gate.lua` e a auditoria
`tools/audit_issd_defense_approach.py`. Não foram alteradas posições em RAM,
e a ROM e os arquivos brutos permanecem locais. A seleção do jogador pode
mudar durante a partida; a auditoria identifica o ator selecionado antes do
comando, em vez de presumir que ele permaneça selecionado depois.

Próximo passo: rastrear o escritor de `$00A6` e os efeitos sobre o ator e a
bola no caso Right; buscar contato aceito sob `$DB25` em mais geometrias e
comparar falta, queda e recuperação antes de integrar ao navegador.

### Escrita do vínculo após contato aceito

Um novo par de replays passivos reproduziu a aproximação Right com A e o
controle sem A. As 245 amostras anteriores conferidas e os registros dos
hooks anteriores ao comando coincidem entre os dois; as entradas também
foram conferidas. No frame 4280 do caso com A, para o ator `$0F00`:

1. `85:F11A` chamou o gate; ele retornou carry limpo, e em `85:F12A` o bit
   `$0400` de `$6E` já estava ativo. `$00A6` ainda apontava para `$1900`.
2. A execução alcançou `85:F137`, ramo em que a rotina escreve o ator em
   `$0076,x` e prepara `$0078,x` para o ator apontado pelo vínculo anterior.
   Os efeitos e a semântica completa desses campos ainda precisam de captura.
3. O caminho `85:F178 → 85:F18E` chamou `85:F8B9`; dentro dele, em
   `85:F8D9`, `STZ $00A6` limpou o vínculo. No hook seguinte, em `85:F8DC`,
   ele já era zero.
4. Após o retorno, em `85:F192`, `STX $00A6` foi executado com `X=$0F00`;
   o hook em `85:F195` confirmou `$00A6=$0F00`. O controle sem A não
   executou esses pontos na janela equivalente.

O monitor genérico de escrita não capturou essa alteração mesmo com hooks
registrados; por isso a evidência acima vem de hooks de execução antes e
depois das instruções, não de uma suposta captura de escrita. Os dados e
limitações estão em `docs/issd-defense-link-probe.json`, produzidos por
`tools/probe_issd_defense_link.lua` e `tools/audit_issd_defense_link.py`.
Trata-se de uma sequência real sob `$02C8/$DF7F`, não de prova de contato
aceito sob `$02D0/$DB25`, nem de uma regra genérica para todas as disputas.
Seis durações adicionais de aproximação DownRight alcançaram `$DB25`, mas
as chamadas observadas ao gate continuaram rejeitadas; sem controle pareado
essas buscas são exploração, não evidência de regra ou resultado de falta.

Próximo passo: observar os campos e estados do adversário após `85:F137` e
buscar um contato aceito sob `$DB25`; calibrar unidades nativas antes de
usar qualquer consequência como substituição da disputa provisória web.

### Reação do adversário após o contato observado

No mesmo cenário pareado de `$02C8/$DF7F`, o traço passivo acompanhou o ator
que tinha o vínculo anterior, `$1900`, até o frame 4380. No frame 4280,
`85:F137` atribuiu `$0F00` a `$1900+76`, e `85:F175` alterou `$1900+78` de
`$000C` para `$0002`. Depois da mudança de vínculo para `$0F00`, o adversário
executou `84:A346 → 84:A36D → 80:F005 → 84:A52B`. Os hooks antes/depois e
o controle sem ação estão em `docs/issd-defense-opponent.json`.

| Frames observados | Estado | Script | Descritor inicial |
| --- | --- | --- | --- |
| 4281–4291 | `$0328` | `$DB05` | `$B5A1` |
| 4292–4299 | `$0330` | `$DB15` | `$B5AA` |
| 4300–4315 | `$0360` | `$DDAC` | `$B4F6` |
| 4316–4380 | `$0350` | `$E214` | `$C249`, depois outras poses |

Os rótulos de assets associados aos três primeiros descritores incluem
`KnockedOnButt` e `OnBack`, sugerindo reação de queda. São nomes de fontes
gráficas, não validação das poses OAM ou de toda a animação. No controle sem
ação, o adversário permaneceu no estado `$00B8` durante a janela.

`$00C0` permaneceu zero nas amostras de ambos os replays, e o hook de entrada
de `80:F005` foi observado com `$1E50=0`. Isso **não comprova** a regra de
falta nem sua polaridade, e a reação ainda estava em `$0350` no fim da janela;
não se deve afirmar que se recuperou. A captura não é um contato aceito sob
`$DB25`. O auditor `tools/audit_issd_defense_opponent.py` valida a comparação
com o controle, os hooks e a cadeia observada, enquanto a instrumentação
`tools/probe_issd_defense_opponent.lua` não altera a RAM. Ainda é necessário
capturar os ramos de falta e a saída completa da reação antes de integrar ao
motor web.

#### Saída da reação no replay estendido

Uma observação pareada estendida até o frame 4550 acompanhou a saída desse
mesmo estado: no frame 4435, `84:A6D7` terminou a sequência, alcançou
`84:A6E9` e chamou `84:9FAF`; a partir do frame 4436 o adversário entrou em
`$02F8/$DB5B`. Em 4483, a rotina seguiu para `84:878A` sem o vínculo da
bola e, no frame 4484, o ator apareceu em `$0010/$D320`, uma pose parada.
O vínculo da bola permanecia com `$0F00`. O controle sem a ação não percorreu
essa cadeia. Isto é uma sequência de recuperação observada, não uma prova
de que todas as quedas sigam o mesmo caminho ou duração.

Nessa rota, `84:9FAF` usa a tabela `$82:DB6F`: os três descritores de
recuperação duraram 16 quadros cada, diferentemente dos 5 quadros por pose da
outra rota de `$DB5B` documentada para o carrinho. `docs/issd-defense-recovery.json`
contém os registros e hashes auditados. A fase `$00C0` permaneceu zero na
janela registrada; a decisão de falta e suas alternativas ainda não estão
resolvidas. Nenhuma dessas durações foi integrada à física provisória web.

### Ramificações de falta e árbitro em replays pareados

Foram executados replays isolados com o mesmo estado inicial e aproximação,
cada um acompanhado de controle sem o comando defensivo. Os valores de
`$1E50` (configuração de faltas) e `$1E58` (índice do árbitro) foram
**alterados sinteticamente em RAM após carregar o estado salvo**; a ROM e o
estado salvo original não foram modificados. Os números abaixo não são
traduzidos para ON/OFF ou nomes de árbitro sem prova adicional do menu.

Com `$1E50=0` e índice de árbitro original `$1E58=1`, o contato aceito passou
por `80:F005 → F047 → F04F → F06A`, marcou o bit `$0100` em `$12F6` e
retornou carry limpo. Com `$1E50=1`, a mesma janela seguiu diretamente para
`80:F045`, também com carry limpo, sem esse bit. Em ambos os casos a fase
`$00C0` permaneceu zero até o frame 4550. As amostras registradas antes da
ação coincidiram nos controles; isso não prova igualdade de toda a memória ou
da evolução aleatória depois da ação. Evidência:
`docs/issd-foul-setting-paired.json`.

Com `$1E50=0` e `$1E58=0` sintéticos, o mesmo contato passou por
`80:F047 → F125`, retornou carry definido e o campo `$00BA` passou a `$0003`;
no frame seguinte a fase mudou para `$0004`. A imagem local do frame 4306
mostra a mensagem **FOUL**, enquanto a imagem do controle pareado não a
mostra; a leitura visual foi conferida manualmente, não por reconhecimento
automático de texto. Com índices sintéticos 1 e 2, essa execução específica
retornou carry limpo e não exibiu a mesma mudança de fase na janela. O estado
salvo tinha índice 1 originalmente, portanto o caso de índice 0 não é uma
captura inteiramente natural. Evidência e hashes:
`docs/issd-foul-referee-replay.json`.

Os três controles e suas ações tiveram 245 amostras anteriores coincidentes
nos campos registrados. A alteração de índice revela uma ramificação real,
mas não prova uma tabela geral de rigor dos árbitros, nem o comportamento
de outras direções, configurações, contatos ou do script `$DB25`. O reinício
após a falta, a posição da cobrança e cartões ainda precisam ser observados.
Os auditores são `tools/audit_issd_foul_setting.py` e
`tools/audit_issd_foul_referees.py`; a captura registra explicitamente cada
intervenção sintética. Nenhuma regra nova foi promovida ao motor web.

### Continuação do fluxo jogável

`dist/match-flow.mjs` prepara o cobrador e a direção de reinício para evitar
que a bola seja colocada imediatamente para fora. Em reposições da equipe do
usuário, o controle passa ao cobrador; em tiro de meta é priorizado o goleiro.
Essas são escolhas provisórias da aplicação, não a sequência original de
reposição, e a cobrança continua imediata.

Jogadores controlados pela CPU podem finalizar perto do gol e o goleiro da
CPU pode afastar a bola depois de recebê-la. A CPU também pode tomar uma bola
no chão quando um adversário está próximo, após proteção provisória de um
segundo da nova posse. Distâncias, tempo, velocidade e seleção dessas ações
foram definidos para permitir partidas, não extraídos da ROM. O chute do usuário
conserva os parâmetros anteriores; o chute automático usa trajetória mais baixa
para poder passar sob o travessão provisório. Falta reconstruir a IA, disputa,
faltas, carrinho, cobranças e estados originais. `dist/test-match-flow.mjs`
verifica seleção do cobrador, orientação, disputa, goleiro e uma finalização
automática que chega ao gol.

## Projeção e geometria confirmadas para a próxima telemetria

O capturador passivo passa a registrar `stadium.layout` em `$7E:0086`, o
comprimento/largura nativos em `$7E:12A2/$7E:12A4` e a origem de câmera em
`$7E:13A0/$7E:13B0`. A alteração corrige a leitura anterior de câmera em
`$00A0/$00A2`, que não era a origem de visualização do jogo.

O leitor de recursos do `issd-native` confirma que os oito layouts originais
usam comprimentos `1792, 1856, 1984, 2048, 1920, 1920, 1792, 2176` e larguras
`576, 640, 704, 640, 640, 576, 704, 704`, extraídos da tabela ROM
`$81:EC47`. Esses valores serão usados apenas depois de aparecerem numa nova
telemetria; não serão aplicados retroativamente ao traço que não os registrou.

`tools/extract_issd_stadium_geometry.py` valida essa tabela diretamente na
ROM USA headerless e grava apenas os pares decodificados em
`dist/data/issd-stadium-geometry.json`. A ROM e seus bytes não entram no
repositório nem na distribuição web.

Os oito previews visuais extraídos estão em
`dist/assets/issd/stadium/layout-0.png` até `layout-7.png`, cada um com seu
manifesto de MD5/layout/dimensões. A tela de configuração web já permite
selecioná-los pelos mesmos índices de `StadiumIDs`; para a ROM USA, o estado
inicial é o layout 1.

## Seleção de estádio

O fluxo de configuração da partida usa `RAM_ISSD_MainMenu_SelectedStadium`
em `$7E:1FA2`. Em `CODE_85A4F8`, a ROM aplica `AND #$0007` e copia o valor
para `$7E:0086`, o seletor consumido pelo carregador de recursos em
`CODE_8B8CDE`. Os oito índices válidos e seus nomes estão definidos no
disassembly: `0 Japan`, `1 USA`, `2 Spain`, `3 Italy`, `4 England`,
`5 Germany`, `6 Brazil`, `7 Nigeria`.

A inicialização USA (`CODE_85A3B1`) define `StadiumIDs_USA` (`1`) como
padrão. Por isso o navegador carrega `layout-1.png` como cenário inicial em
vez de `layout-0.png`. A interface de configuração usa somente esses oito
valores e troca o preview/cenário sem inventar um nono estádio.

O manifesto `dist/data/issd-stadium-layouts.json` fornece ao navegador o
nome, arquivo e recorte de cada preview. `tools/build_issd_stadium_layout_manifest.py`
obtém cada recorte pelo limite RGB não-preto da própria extração, que reproduz
o recorte anterior do layout 0; portanto a troca de cenário não reutiliza
coordenadas de outra imagem.

Em fluxos sem escolha manual, `CODE_85C058` também pode produzir `$0086` por
uma tabela de cenário (`DATA_8BFC28`) ou pela rotina `CODE_858419`. Esses
caminhos ficarão separados da futura escolha manual para preservar o
comportamento de cada modo original.

## Opções de partida

`CODE_85:A456` normaliza as opções escolhidas no menu antes de iniciar a
partida. O manifesto `dist/data/issd-match-settings.json` registra as faixas
confirmadas: cinco níveis, três opções de tempo, regras binárias, três horários
e três climas, oito estádios e três árbitros mais a opção aleatória. Ele é um
contrato de armazenamento da ROM, não uma afirmação de que os respectivos
efeitos já foram reproduzidos no navegador.

A tela atual materializa o contrato de armazenamento dessas opções para a
partida web. Somente a seleção de estádio já altera a apresentação; nível,
tempo, regras, horário, clima e árbitro permanecem dados selecionáveis até que
as rotinas que consomem cada campo sejam validadas na ROM. Assim a interface
não antecipa efeitos de mecânica ainda não comprovados.

`tools/extract_issd_match_setting_transfer.py` agora recupera a transferência
inteira de `CODE_85:A456` a partir do disassembly e grava
`dist/data/issd-match-setting-transfer.json`. O registro inclui as doze
transferências reais do trecho: as dez opções da partida, som e o flag de
locução marcado como não usado. Para cada uma, preserva os endereços WRAM de
menu, destino em jogo e linhas-fonte. Isso separa o fato já provado — por
exemplo, estádio termina em `$7E:0086` — do efeito de jogo que ainda requer
análise de cada consumidor.

O índice complementar `dist/data/issd-match-setting-consumers.json`, gerado
por `tools/extract_issd_match_setting_consumers.py`, encontra 136 acessos
explícitos aos dez registros de partida que mantêm símbolos `InGame`.
Ele identifica rotinas e leitura/escrita, sem nomear o resultado de um ramo:
por exemplo, `CurrentOffSideSetting` é lido em `CODE_80:D5DF`, e
`CurrentYellowCardSetting` em `CODE_80:F076`. Este é o ponto de partida
reproduzível para recuperar cada regra; o índice não transforma esses acessos
em uma implementação web prematura.

## Relógio

O código de interface em `CODE_83:C201` usa BCD e consulta
`DATA_81:AC83`; `CODE_A4:9401` só atualiza o contador quando os flags de pausa
não estão ativos e compara contra `60` frames. A porta de elegibilidade faz OR
de `$11FA/$00C0/$00B8/$00B6/$00BA`: qualquer valor não-zero impede tanto o
incremento do contador de frames quanto o tick BCD. Esses campos são
bloqueadores internos observados, não nomes de pausa, reinício ou fase já
resolvidos. O extrator
`tools/extract_issd_match_clock.py` grava os valores e fontes em
`dist/data/issd-match-clock.json`: além dos offsets de exibição, ele recupera
as duas tabelas de contagem inicial de `CODE_A4:A4926F` (`$81:E893` e
`$81:E89B`). `CODE_83:B02C` zera `$00A8` na inicialização e, portanto, prova
que a primeira partida usa a tabela `$81:E893`. A semântica do contador e o
quarto índice das tabelas continuam pendentes. Por isso o relógio simplificado
do navegador não foi substituído até que a transição de fases e as interrupções
sejam validadas em execução.

`CODE_A4:93CC` também foi recuperada: sob `SED`, reduz `$0001` enquanto o byte
BCD inferior é não-zero e reduz `$0041` quando ele é zero (`0500 → 0459`). O
Canvas usa a tabela inicial da primeira etapa (`$00A8 = 0`) e essa transformação
para apresentar a contagem regressiva das três opções de tempo. Ainda não
implementa os bloqueadores internos nem a transição de intervalo/fim ao chegar
em zero; por isso a apresentação congela em `00:00`, sem inventar uma fase.
O caminho nativo de zero em `A4:92CF` limpa `$16D8`, incrementa `$16F8` e muda
um atributo de exibição, mas não escreve diretamente `$00A8`. Logo, a mudança
de etapa precisa ser localizada fora da rotina de relógio antes de ser
implementada.

`A4:9456` separa os índices de fase em dois grupos para a tabela de exibição:
`0/1` usam o índice base de tempo e `2/3` recebem deslocamento de três. Essa
partição é confirmada, mas seus nomes esportivos e o escritor que move o jogo
entre os grupos continuam pendentes.

O navegador implementa a subtração BCD em `dist/match-clock.mjs`, com ajuste
decimal explícito: por exemplo, `05:00 → 04:59` e `04:50 → 04:49`. A antiga
subtração binária gerava bytes inválidos como `$BF`, exibidos como `123`.
O teste `dist/test-match-clock.mjs` verifica as transições e uma contagem
completa de cinco minutos. Isso corrige apenas a exibição e o decremento;
os bloqueios e transições de período continuam pendentes.

O navegador já aplica o trecho de inicialização comprovado: ao começar uma
**nova** partida, zera placares e o progresso exibido do relógio. Isso fica
separado de reinícios dentro da partida, que preservam o tempo. O limite de
duração, intervalos e a transição de fim de período ainda não foram conectados
ao motor web.

## Câmera ampla

O código `issd-native` oferece perfis modernos `TACTICAL (80%)` e
`TACTICAL WIDE (67%)`, com projeções `4/5` e `2/3`. Eles estão registrados em
`dist/data/issd-camera-profiles.json` como extensões opt-in, e não como valores
originais da ROM. A projeção de referência continuará dependente da origem de
câmera capturada em `$7E:13A0/$7E:13B0` e do frame correspondente.

### Preparação da falta e seleção de ator — replay pareado

No cenário de contato `$DF7F`, com valores sintéticos `$1E50=0` e
`$1E58=0` aplicados apenas à RAM do replay, o caminho observado no frame 4281
foi `A4:DB90 → A4:DD11 → A4:DD45 → A4:DD6A → A4:DDB7`. O controle
sem a ação não executou esses hooks. O contato havia registrado `$00C4=$0F00`
e `$00C6=$1900`; a chamada `80:E2E1` retornou `$1200` em X e o código o
armazenou em `$11E8`. No frame seguinte `$00C0=$00C2=4`. O slot selecionado
permaneceu `$1200` e a fase 4 permaneceu ativa até o frame 5000, sem uma
entrada deliberada posterior de cobrança. Isso confirma a preparação nesse
cenário, não a execução de uma cobrança nem uma regra universal de escolha.

Estática: `A4:DB90` usa `$00C6` para obter `$00CA/$00CE` quando `$00BC=3`
e despacha a entrada correspondente para `A4:DD11`. Na rota observada,
`A4:DD6A` lê o campo `$88` do ator `$00C4` e passa o valor a `80:E2E1`,
que transforma coordenadas e percorre dez slots de atores, com filtros e
comparações adicionais. Não é correto reduzi-la a uma seleção do atleta
mais próximo sem analisar esses filtros. `A4:DDB7` escreve a fase 4 pelo
caminho `A4:DCA6`. Outra rotina, `A4:DCC8`, também contém escrita de fase e
posicionamento de bola, mas **não foi executada nesta captura**; sua relação
com a retomada observada continua pendente. As coordenadas registradas em
`$00CA/$00CE` não foram diretamente comparadas às coordenadas de tela.

A evidência reproduzível está em `docs/issd-foul-restart-paired.json` e
`tools/audit_issd_foul_restart.py`; o observador é
`tools/probe_issd_defense_opponent.lua`. As capturas locais completas e a ROM
não são distribuídas. Próximo passo: rastrear os estados e comandos do slot
`$1200`, com entrada deliberada e controle pareado, para distinguir a
preparação da execução efetiva e acompanhar bola, relógio e transição de fase.

### Cobrança com entrada controlada — uma falta

Três replays reproduziram a mesma falta da seção anterior, com as mesmas
alterações sintéticas em RAM (`$1E50=0`, `$1E58=0`). No passo relativo 800,
foi enviado ao controle 2 um pulso de seis passos de A, B ou nenhum botão.
As amostras registradas antes do pulso foram idênticas entre os três replays;
no início do pulso o controle 2 apontava para o atleta `$1200`. Essa igualdade
não cobre estados internos que não foram registrados.

Nos dois testes com botão, as amostras do atleta mostraram os estados/scripts
`$0460/$D69A → $0468/$CF9F → $0470/$D1C5`. No frame 4613, a
observação por frame registrou a fase `$00C0` passando de 4 a 0 e o tipo da
bola passando de `$000E` a `$0003` com A ou `$0002` com B. Na amostra desse
frame, os componentes brutos de velocidade `(vx, vy, vz)` eram,
respectivamente, `($FFFB,$FFFF,$FFFB)` e `($FFF8,$FFFF,$FFFE)`.
No controle sem botão a fase 4 permaneceu ativa até o frame 5000. Os valores
são palavras de 16 bits, ainda não convertidas para unidades físicas; esses
resultados não estabelecem, por si só, os rótulos de passe ou chute, nem a
montagem visual completa da animação. O relógio não foi medido neste ensaio.

A sonda registra explicitamente botão, controle, passo e duração via
`ISSD_AUTO_P2_RESTART_BUTTON` e exige replay isolado. Fontes e hashes estão em
`docs/issd-foul-kick-input.json`, auditados por
`tools/audit_issd_foul_kick_input.py`. Próximo passo: correlacionar os scripts
`$CF9F/$D1C5` com descritores e composição gráfica, e medir separadamente
relógio e posições em coordenadas de mundo antes de aplicar a cobrança no jogo
web.

### Relógio e descritores da cobrança A

Em um novo par de replays do mesmo cenário sintético, `$16D0` permaneceu no
valor BCD `$0451` (4:51) durante os frames 4282–4612, com a fase 4 ativa.
Depois da cobrança A, a fase passou a zero no frame 4613 e o relógio caiu para
`$0450` no frame 4668. No controle sem comando, tanto a fase 4 quanto o
valor `$0451` permaneceram até o frame 5000. Essa medida vale para o cenário
observado e não define o comportamento do relógio em todas as interrupções.

Para o jogador `$1200`, uma captura por frame registrou a sequência seguinte
(`script: descritores`, direção interna indicada entre parênteses):

- `$CF9F`: `$A791 → A79A → A7A3 → A7AC` (direção 3).
- `$D1C5`: `$AD4C → AD55 → AD5E → AD67` (direção 3), seguido de
  `$AD3A` quando a direção passou a 4 no frame 4613.

Foram preservadas localmente 36 amostras com OAM, VRAM, CGRAM e imagem;
a sequência e o relógio são auditados por
`tools/audit_issd_foul_kick_graphics_clock.py`, com hashes e limitações em
`docs/issd-foul-kick-graphics-clock.json`. A presença dessas capturas ainda
não valida quais entradas OAM pertencem ao jogador nem o alinhamento da PPU
com o frame lógico. Por isso, estes descritores não são uma spritesheet ou
composição visual validada, e a animação de cobrança ainda não foi aplicada
como definitiva no jogo web.

### Validação visual do corpo na cobrança A

Em replay isolado equivalente ao da captura anterior, os ganchos da lista de
renderização identificaram os slots OAM do ator `$1200`. Para oito quadros
preparados entre 4596 e 4612, as 50 peças do corpo corresponderam à geometria
e ao espelho OAM; as mesmas peças corresponderam à OAM da PPU no frame de
exibição seguinte. Os 2.857 pixels visíveis compostos desses slots também
coincidiram com as respectivas imagens do emulador. Para `$AD4C`, `$AD55`,
`$AD5E` e `$AD67`, os registros de geometria ainda coincidiram com os bytes
da ROM no banco `$88`. Para `$A791`, `$A79A`, `$A7A3` e `$A7AC`, a geometria
foi capturada em WRAM: há correspondência com OAM e imagem, mas não se afirma
que sua extração direta da ROM já esteja validada.

Na mudança para `$AD3A`, direção 4, a geometria preparada no frame 4613
coincidiu com o espelho, mas as seis peças divergiram da amostra seguinte da
PPU. A sincronização desse quadro permanece em aberto; ele não entra nos oito
quadros validados. O cabelo e outros objetos auxiliares também não estão
cobertos. A evidência, hashes e limites constam em
`docs/issd-foul-kick-body-geometry.json`, reproduzidos por
`tools/audit_issd_foul_kick_body_geometry.py`. A ROM, imagens e dumps gráficos
continuam locais. O coletor `capture_issd_slide_replay.lua` agora respeita o
ator solicitado também na captura ao fim do frame.

### Passe no protótipo web — comportamento visual provisório

A partida web já acionava a folha local `$D100` ao executar `pass()`, mas a
primeira tentativa iniciava o download apenas durante o desenho e podia
terminar antes de a imagem ficar disponível. `dist/game.js` havia passado a solicitar
antecipadamente as folhas de ação existentes; a correção abaixo desativou as
folhas provisórias de passe por conterem fragmentos incorretos. O passe agora calcula o setor visual a partir do direcional pressionado ou da
última orientação do jogador; direções de animação ausentes ainda usam o
fallback anterior.

Isso melhora a demonstração web, mas permanece um adaptador experimental:
`$D100` não foi confirmado como passe normal, as folhas possuem composição e
aparência capturadas, o tempo usa multiplicador de prévia, e a física do passe
continua provisória. A sequência `$CF9F → D1C5` validada acima refere-se à
cobrança de falta e não foi atribuída automaticamente ao passe normal.
`node dist/test-gameplay-actions.mjs` e `node dist/test-player-drawing.mjs`
verificam os oito setores e o acionamento na direção do alvo.

### Ação B com posse normal — composição do corpo

Uma nova execução do botão físico B no controle 2 usou o mesmo savestate da
matriz de ações e foi comparada ao replay neutro. As 240 amostras anteriores
nos campos registrados coincidiram e o botão foi confirmado nas três amostras
da janela. Nesse cenário, o ator `$1900` entrou no estado `$0258`, com script
`$82:D01F`; dois descritores de corpo, `$A629` e `$A632`, foram validados
contra a geometria da ROM e contra o espelho OAM e a OAM da PPU. Os 654 pixels
visíveis das peças identificadas coincidiram com as capturas de referência.

Essa observação confirma uma ação sobre a bola em posse normal e diferencia a
sequência observada da folha `$D100` atualmente usada como aproximação do
passe no navegador. **Ainda não confirma que o botão B represente passe** na
configuração capturada, nem autoriza substituir a animação de todas as
direções. A prova cobre dois quadros do corpo e não inclui cabelo, demais
objetos, física ou casos distintos. A auditoria reproduzível está em
`tools/audit_issd_normal_b_body.py`, com hashes e limites em
`docs/issd-normal-b-action-body.json`; ROM e capturas permanecem locais.
Próximo passo: identificar a função esportiva da entrada e o mapeamento
configurado, ampliar direções e compor corpo, cabelo e uniforme antes da
integração dinâmica no jogo.

### B com direções em posse normal

O [manual norte-americano do ISS Deluxe](https://www.scribd.com/document/626704713/International-Superstar-Soccer-Deluxe-28-USA-29)
informa que os botões podem ser reconfigurados. Guias de controle do jogo
[associam B e direcional ao passe na configuração padrão](https://gamefaqs.gamespot.com/snes/588391-international-superstar-soccer-deluxe/faqs/18278).
Essa referência ajuda a formular o experimento, mas não prova qual configuração
estava ativa no savestate, nem que todo caminho de B seja passe.

Quatro replays com o mesmo estado inicial enviaram B + cima, direita, baixo ou
esquerda ao controle 2, comparados ao mesmo controle neutro. Cada um manteve
240 amostras anteriores iguais nos campos registrados, e o botão e a direção
foram conferidos na janela do comando. Foram validadas 19 amostras distintas
do corpo contra espelho OAM, OAM da PPU e pixels visíveis; geometria em ROM
foi conferida para as poses armazenadas no banco `$88`.

Na janela capturada, B + cima passou por `$D16E`, B + direita e B + baixo por
`$D1C5`, e B + esquerda por `$D280 → D290`. Antes dessas rotas, o ator
começou de `$D6DB`; as sequências e direções internas por frame estão em
`docs/issd-directional-b-body.json`. Isso mostra que uma folha única `$D01F`
não representa todas as combinações. Os rótulos de direção da entrada não
são automaticamente as direções de tela ou índices de animação. Os comandos
podem depender de configuração e contexto; cabelo e objetos auxiliares ainda
não foram validados. `tools/audit_issd_directional_b_body.py` reproduz a
conferência; a ROM e as capturas ficam locais. Ainda faltam diagonais, a
associação de cada comando ao passe na configuração efetivamente usada e a
composição por aparência/uniforme para uma troca geral na partida web.

Atualização: o mesmo experimento foi repetido para as quatro diagonais.
A auditoria agora cobre **oito direções de entrada e 37 amostras distintas**
do corpo no total. Neste estado inicial, cima-direita seguiu a rota observada
para cima; baixo-direita, a de direita/baixo; e as duas diagonais à esquerda,
a de esquerda. Essa equivalência é uma observação deste replay, não regra
geral para posição, orientação ou configuração diferentes. As amostras das
outras direções do corpo, variações de jogador e semântica dos caminhos ainda
exigem correlação antes de uma substituição geral no jogo.

`tools/export_issd_normal_b_body_preview.py` executa a auditoria da ação B
sem direcional antes de gerar localmente uma folha PNG transparente com os
dois quadros validados do corpo. A folha demonstra o atleta e uniforme da
captura, não é um renderizador dinâmico nem uma animação completa; ela fica
em `analysis/` e não é distribuída. A seleção automática por equipe, aparência
e direção no jogo web permanece pendente.

### Integração inicial experimental no passe web

A partida carrega `native-pass-body-local.json` quando o arquivo local existe.
Para Inglaterra (id 2), primeiro uniforme, pele 0, cabelo 0, jogador de linha
e direção de tela 2, a ação usa dois quadros montados dos descritores ROM
`$A629/$A632`, com duração observada de 2 e 16 frames na captura de B sem
uma direção pressionada. O exportador `tools/export_issd_pass_body.py` exige
a auditoria pareada e compara cada tile usado com a VRAM capturada antes de
gerar o arquivo local; o JSON contém gráficos derivados da ROM e está no
`.gitignore`. Nos demais casos ou sem arquivo local, mantém-se a folha anterior.

A integração é experimental: a paleta da captura coincide com a da Inglaterra
no primeiro uniforme e pele 0; a associação do cabelo 0 e o uso dessa sequência
para o passe web direcionado são hipóteses ainda não validadas. A captura
original não estabeleceu montagem de cabelo auxiliar nem todos os contextos
ou direções. O renderer só compõe o corpo capturado e não prova equivalência
da física ou do comando da partida web. Teste local: escolha Inglaterra como
primeiro time, primeiro uniforme e um jogador com pele/cabelo 0; direcione o
passe para a direita. A ação mantém a alternativa anterior quando não há dados.

A renderização dos dois quadros extraídos foi comparada pixel a pixel com a
prévia da OAM capturada: zero pixels diferentes. Os testes Node cobrem os
limites de seleção, duração, fallback e o ramo de desenho; a auditoria de
origem é `tools/audit_issd_normal_b_body.py`. Próximo passo: validar a
associação da aparência e o comando direcional, depois substituir também as
outras direções e uniformes com dados efetivamente capturados.

### Direção do passe no protótipo web

O passe web deixou de escolher automaticamente um companheiro à frente para
definir a direção da bola: o vetor agora segue o direcional pressionado no
momento do comando ou, sem direcional, a última orientação do jogador. A
animação recebe a mesma direção. Os testes cobrem as oito direções, entrada
simultânea e orientação preservada. A velocidade e a altura continuam sendo
valores provisórios; essa alteração resolve o controle web, não estabelece a
fórmula ou a assistência de passe originais da ROM.


### Correção visual temporária do passe

As folhas locais provisórias `$D100` contêm fragmentos OAM soltos e aparência
fixa. Elas deixaram de ser desenhadas no passe: fora do contexto limitado da
composição nativa acima, o jogador mantém a pose parada da própria equipe e
aparência, voltada para a direção do passe, inclusive nas diagonais. Esta é
uma reserva visual, **não uma animação de passe original completa**. A
composição nativa já disponível continua sendo usada no caso limitado; a
recuperação dos demais quadros e aparências permanece pendente. Testes cobrem
a preferência pela composição nativa, ausência das folhas defeituosas e as
quatro diagonais.

### Passe composto em seis orientações capturadas

Foram repetidos pares de replays com o jogador orientado antes do comando B,
sempre comparando com controle neutro e confirmando a posse no início. Os
contextos com orientação de tela cima, direita, baixo-direita, baixo,
baixo-esquerda e esquerda produziram dois quadros `$D01F`, de 2 e 16 frames,
sem interrupção no intervalo observado. A geometria da ROM, os tiles da VRAM,
o espelho OAM e a OAM da PPU foram conferidos. Para cada quadro, todos os
pixels visíveis coincidiram com a imagem; nas direções inferiores, os pixels
restantes coincidiram com a composição de todos os objetos da OAM, indicando
sobreposição por outros sprites sem identificar sua natureza. O compositor
web foi comparado diretamente com as peças da PPU: zero diferenças nos 12
quadros. O detalhe de uniforme da direção superior usa uma segunda paleta;
o compositor agora mantém as paletas separadas.

`tools/export_issd_pass_orientations.py` reproduz as verificações e gera
`native-pass-body-local.json` v2, não versionado. Os hashes e a cobertura
estão em `docs/issd-pass-orientations.json`. No jogo web, a seleção segue
limitada à Inglaterra, primeiro uniforme, pele e cabelo de índice 0; a
associação do cabelo e o uso em todos os contextos continuam provisórios.
As diagonais superiores permanecem na pose de reserva: em cima-direita o
atleta perdeu a posse antes da ação e, em cima-esquerda, a sequência foi
interrompida. Esse resultado não comprova regras ou tempos universais da ROM.

### Escala do passe em relação à locomoção

A célula transparente dos quadros de passe mede 96 pixels de altura, enquanto
as células de caminhada capturadas atualmente medem 52. Dimensionar ambas
como se a célula inteira fosse a altura do jogador deixava o passe reduzido.
O renderizador agora consulta a altura da célula de caminhada correspondente
à direção e aplica a mesma escala em pixels nativos, preservando a âncora
observada do passe. A consulta usa o recurso local de locomoção; se ele não
estiver disponível, a composição limitada de passe não é ativada e a reserva
visual permanece. Isso corrige a escala da apresentação web, sem alterar os
quadros ou declarar equivalência física com o jogo original.

### Passe nas duas diagonais superiores

Em replays pareados, variar a duração do movimento antes de B permitiu manter a
posse e completar `$D01F` nas duas diagonais superiores: `UpRight` encerrou o
movimento no passo relativo 355 e `UpLeft` no 335. Cada caso foi comparado a
um controle sem B com a mesma janela; a entrada e os campos anteriores foram
conferidos. Os dois quadros em cada direção foram validados contra geometria,
tiles, OAM e captura, e o compositor web coincidiu pixel a pixel com a OAM.
Os replays anteriores interrompidos não foram descartados nem usados como
prova de duração; esta é uma nova captura em outro contexto.

O exportador aceita `--diagonals analysis/pass-final-diagonals` e agora gera
os oito ciclos locais de passe, com relatório em
`docs/issd-pass-orientations.json`. O jogo usa os oito apenas no contexto
limitado da Inglaterra, primeiro uniforme, pele e cabelo de índice 0. A
aparência e os demais contextos continuam pendentes de validação; os demais
jogadores mantêm a pose de reserva. `ISSD_AUTO_P2_MOVE_END` permite repetir
estas janelas em replay isolado e registra a alteração na telemetria.

### Paletas de equipe e uniforme no passe

A composição experimental do corpo do passe aceita agora as 36 seleções,
os dois uniformes e nos tons de pele 0 e 1, para cabelo de índice 0, em sete
direções de tela. As cores de pele vêm do recurso local de prévia de jogador;
as cores de uniforme vêm da paleta da equipe selecionada e são convertidas
para a representação de 5 bits usada pela PPU. O cache inclui equipe,
uniforme, pele, direção e paleta para evitar reutilizar cores de outro atleta.

A direção para cima continua limitada ao contexto da Inglaterra/primeiro
uniforme/pele 0: nela há uma peça em banco de paleta separado cujo seletor e
tile não foram validados para as demais equipes. Outros cabelos e goleiros
continuam usando a pose de reserva. A geometria, o cabelo 0 e a aplicação
para outras equipes e tons de pele permanecem uma extrapolação de um ator
capturado, não uma validação por equipe no emulador.

Foram exercitadas 1.008 combinações locais de equipe, uniforme, pele e sete
direções, além dos testes automatizados de paletas, cache e seleção. Os 16
quadros da Inglaterra/primeiro uniforme/pele 0 permaneceram idênticos aos
quadros de corpo anteriormente validados contra a PPU. Os dados de imagem
derivados da ROM continuam locais e fora do repositório.

### Detalhe do passe para cima por número e uniforme

`84:E77D` seleciona o tile de detalhe de `$A5BD/$A5C6` usando o campo local
`+$56`; a captura natural registrou variante 18. Em replays isolados, as
variantes 0, 14 e 30 foram escritas sinteticamente nesse campo e registradas
na telemetria. Nos dois descritores, os quatro tiles (incluindo o natural)
coincidiram com os bytes da ROM e da VRAM. Os campos anteriores registrados
nos replays foram iguais; essa comparação não cobre toda a memória. A
correspondência e seus limites estão em `docs/issd-pass-detail-variants.json`,
gerados por `tools/audit_issd_pass_detail_variants.py`.

O exportador local pode receber `--detail-evidence` e gerar os tiles de detalhe
para números de 1 a 20. A seleção no navegador usa o número do jogador, as
cores de uniforme da equipe e a tabela `issd-team-detail-colors.json`. A
animação para cima agora é utilizada para equipes e uniformes cujo seletor
escreve uma cor conhecida; seletores zero não escrevem cor e continuam na
pose de reserva. Números fora de 1–20, cabelos diferentes de 0 e goleiros
permanecem fora desta integração. A associação entre número editado e campo
local é baseada no formato de dados e precisa de captura específica com
edição; as cores de outras equipes seguem a tabela extraída, mas ainda não
foram comparadas individualmente com partidas no emulador.

A verificação incluiu testes de seleção por número e cor, quatro variantes em
VRAM, e comparação dos 16 quadros da Inglaterra com os já validados. O JSON
com os tiles extraídos continua local e fora da distribuição. A reconstrução
de cabelo para as poses de passe permanece a próxima etapa.

### Cabelo no passe para a direita — estilos 1, 2 e 13

O replay do passe foi repetido em três estilos. Como o atleta capturado não
possuía contexto auxiliar de cabelo, um contexto existente foi reassociado a
ele **somente na RAM de cada replay isolado**, com estilo e proprietário
anteriores registrados. A rotina original carregou os tiles correspondentes
às poses `$A629/$A632`; posição e prioridade da peça auxiliar foram obtidas
da lista de desenho e da OAM, sem coordenadas inventadas. Os offsets de origem,
hashes e limites estão em `docs/issd-pass-hair-synthetic.json`.

`tools/audit_issd_pass_hair.py` confirmou os tiles de cabelo da ROM contra a
VRAM e a composição com o corpo contra a captura. O renderer do navegador foi
comparado à composição OAM: zero diferenças nos seis quadros dos três
estilos. `tools/export_issd_pass_hair.py` gera o recurso local ignorado pelo
Git; a ausência do recurso mantém a pose de reserva. Na partida, os estilos
1, 2 e 13 usam essa composição somente ao passar para a direita; outras
direções e cabelos permanecem na reserva. As cores de outras equipes e tons
de pele reutilizam as paletas já disponíveis, mas essa generalização não foi
capturada individualmente no emulador. A captura teve reassociação sintética
do contexto e cobre um ator, uma direção e dois quadros; não comprova todas
as regras de seleção de cabelo em qualquer estado da partida.

### Prioridade nas ações: passe e primeira integração visual do carrinho

Para não ocultar a ação de passe por falta de cabelo validado, estilos 0–13
podem usar o corpo capturado nas direções e uniformes já suportados. Quando
há uma camada de cabelo validada para o estilo e direção, ela continua sendo
composta; nos demais casos o corpo é desenhado sem essa camada. Isso prioriza
a animação, mas a aparência de cabelo nesses casos é provisória. Permanecem
as restrições de detalhe de uniforme para cima, número de camisa e goleiros.

A sequência parcial de corpo `$DB25 → DB5B` já validada no laboratório foi
ligada ao comando defensivo F na partida, apenas para Brasil, primeiro
uniforme, pele 0 e direção de tela direita, quando o adversário tem a bola.
Os quadros vêm do recurso local validado, com escala de locomoção e âncora
própria. A camada de cabelo não foi incorporada. A sequência registrada termina
no limite da captura, portanto não estabelece a duração universal do carrinho.

**Ação visual ainda não significa mecânica original:** o comando continua
usando a interceptação provisória `canStealBall`; esta integração não adiciona
colisão de carrinho, falta, queda ou recuperação de física. Outros uniformes,
equipes e direções continuam sem o carrinho visual até sua composição ser
validada. Os seis quadros locais foram novamente comparados à OAM capturada;
os testes cobrem seleção, duração, âncora e preservação do controle existente.

### Regra de apresentação das próximas ações

Sempre que uma animação de ação for disponibilizada na partida, disponibilizar
uma prévia acessível pelo laboratório, com seleção dos contextos suportados e
indicação clara de recursos provisórios ou ausentes. Passe e chute estão em
`editor/locomotion-lab.html#action-lab`; o carrinho está em `#slide-lab`.
O painel de passe reutiliza o renderer da partida, e o de chute apresenta a
folha experimental usada pela partida; não representa validação adicional.

## Carrinho: direções e uniformes (2026-11-04)

A comparação de oito execuções pareadas da ROM USA registrou seis descritores
por direção, com geometria da ROM e OAM do PPU verificadas. As direções de
exibição, em ordem horária a partir de cima, correspondem aos índices internos
6, 7, 0, 1, 2, 3, 4 e 5. Os detalhes, hashes, quadros e diferenças de pixels
constam em [issd-slide-direction-captures.json](issd-slide-direction-captures.json).
Nos pixels em que a composição do jogador diferiu da captura de tela, o pixel
observado foi igual ao da execução de controle; isso não identifica por si só
qual camada o produziu. O roteiro é reproduzível por
`tools/audit_issd_slide_directions.py` com a ROM e capturas locais.

A versão web e o laboratório agora usam a composição lateral capturada para
ambos os sentidos, com os uniformes das 36 equipes, duas opções de uniforme e
as duas paletas de pele do editor. A geometria e os tiles foram verificados no
ator capturado; a aplicação das demais paletas é uma generalização da tabela de
uniformes, não uma captura individual de cada seleção. A camada de cabelo do
carrinho ainda não foi validada. A física de carrinho e roubo continua
provisória. Nas outras seis direções, uma peça usa uma paleta e um tile de
detalhe adicionais, selecionados por informações do jogador; não foram
habilitadas até que essa composição seja reproduzida e testada para cada caso.

Para reconstruir o recurso local da esquerda, mantendo a ROM fora da
distribuição, execute na raiz do projeto:

```powershell
python tools/export_issd_slide_lab.py analysis/slide-direction-paired/A/Left analysis/slide-direction-control-graphics/Left --rom "International Superstar Soccer Deluxe/International Superstar Soccer Deluxe (USA).sfc" --state analysis/bsnes-shared-state/issd-auto-probe-20261102-211624-trigger.State --catalog dist/data/issd-rom-catalog.json --action-input 0x280 --neutral-input 0x200 --output dist/assets/issd/slide-lab-local/left.json
```

O arquivo gerado é ignorado pelo Git, assim como a ROM e as capturas locais.
Caso falte, o jogo continua usando somente o sentido lateral previamente
instalado. Próximo passo: validar a construção dinâmica do tile 23 e da cor da
paleta adicional a partir do número do jogador e do uniforme, incluindo os
casos em que a ROM não escreve uma cor nova; só então habilitar as seis
direções restantes no laboratório e na partida.

### Atualização: detalhe de uniforme por direção

A composição dinâmica agora inclui o tile 23 selecionado pela rotina
`$84:E77D`, com variantes de equipe e número de camisa extraídas localmente da
ROM. A cor do detalhe segue o modelo de `$8B:D151`; quando o seletor não escreve
uma cor, ou quando o tile usa cores além do índice 12, a combinação fica
indisponível até que seu estado seja compreendido. O laboratório permite
escolher o número da camisa. A partida utiliza o número cadastrado no elenco.

As oito direções estão disponíveis para as combinações de uniforme cuja
composição é conhecida. Para o ator capturado (Brasil, uniforme 1, camisa 7),
os 48 quadros são idênticos, pixel a pixel, à composição das capturas
OAM/VRAM/CGRAM. O teste `node tools/test_issd_slide_direction_pixels.mjs`
reproduz a comparação com os recursos locais. A seleção das demais equipes,
números e uniformes é uma generalização das tabelas da ROM; não representa
capturas individuais de todas as combinações. Cabelo permanece pendente.

**Correção de continuidade:** a análise anterior concluiu incorretamente que
as sequências para baixo foram interrompidas. A seleção automática mudou para
outro jogador durante a execução, enquanto o ator original continuou o
carrinho. Ao acompanhar seu endereço `$0F00` nos registros de atores, as seis
poses e suas durações foram recuperadas para as três direções. O teste
`python tools/test_issd_slide_actor_tracking.py` protege contra essa troca.

As direções para baixo, baixo-direita e baixo-esquerda permanecem limitadas a
combinações cujo tile de detalhe usa somente o índice de cor 12 e cuja cor foi
identificada: onze seleções na amostra das 36 equipes, considerando camisa 7; essa limitação foi resolvida conforme a atualização de paleta abaixo.
Para os outros casos, há índices de cor adicionais ou uma ausência de escrita
que ainda precisam ser investigados. Nessas situações a animação não é exibida
como se estivesse validada.
Para gerar as oito direções localmente, a partir das capturas já realizadas:

```powershell
python tools/export_issd_slide_directions.py --rom "International Superstar Soccer Deluxe/International Superstar Soccer Deluxe (USA).sfc" --state analysis/bsnes-shared-state/issd-auto-probe-20261102-211624-trigger.State --catalog dist/data/issd-rom-catalog.json --output dist/assets/issd/slide-lab-local/directions.json
```

O arquivo resultante contém gráficos derivados e é ignorado pelo Git. Ausente
esse arquivo, continuam disponíveis as duas direções laterais geradas antes.


### Tile transparente do detalhe do carrinho

A leitura de `$84:E7EF`–`$84:E811` mostra que o ponteiro `$98:F014`
é enviado por DMA como os demais; ele não representa ausência de escrita de
gráficos. Na ROM USA usada aqui, seus 32 bytes são zero: o tile é transparente.
O exportador agora preserva esse caso para Inglaterra, Áustria, República
Tcheca e Uruguai nas direções inferiores. O teste local
`tools/test_issd_slide_transparent_tile.py` compara 960 variantes com a ROM e
os dados gerados; o teste do renderizador confirma que uma cor não escrita não
altera um tile transparente. Isso permite renderizar o Uruguai mesmo com
seletor de cor zero, sem atribuir uma cor fictícia.

O comportamento de não escrever a **cor** em `$8B:D151` é distinto do DMA do
tile e continua dependendo do estado anterior quando há pixels visíveis.
Ainda falta determinar a origem das demais cores usadas por alguns tiles e
validar essas combinações; até lá, continuam bloqueadas. A execução completa de
uma partida por equipe ainda não foi capturada para validar essas variantes.


### Paleta de detalhes das 36 equipes

O fluxo de inicialização `$8B:CFAF` chama `$A4:920B` antes de `$8B:CFBB`.
A primeira rotina usa a tabela de ponteiros `$81:E7D8` e o carregador
`$80:A4EF` para copiar quatro cores da equipe às posições `$CC`–`$CF` do
espelho de paletas do primeiro time; a segunda chama `$8B:D151` para substituir
`$CC` somente quando o seletor do uniforme determina uma escrita. Portanto,
um seletor zero conserva a cor inicialmente carregada para a equipe, nesse
fluxo de inicialização observado. O segundo time usa `$DC`–`$DF`.

A mesma inicialização usa a tabela `$82:8326` para carregar a paleta do
goleiro a partir de `$C1`; sua cor de índice 10 tem o valor BGR555 `$0865`
nas 43 entradas conferidas. A tabela `$81:E7D8` fornece as cores 13, 14 e 15
usadas pelos demais detalhes. O exportador verifica as tabelas da ROM e compara
os índices 10 e 13–15, além da cor 12 resultante para o Brasil, com 264 capturas
CGRAM locais. Os hashes, endereços e limites constam em
[issd-slide-palette-evidence.json](issd-slide-palette-evidence.json).

A composição agora cobre 36 equipes, dois uniformes, oito direções e números de
camisa de 1 a 20. Foram verificados programaticamente 11.520 contextos de
seleção e os 48 quadros do Brasil continuam iguais à captura de referência.
As demais combinações derivam das tabelas e da ordem de inicialização da ROM;
não constituem capturas de partida de cada equipe. Atualizações posteriores de
paleta podem alterar o estado real e continuam sujeitas a investigação. A
camada de cabelo e a mecânica física do carrinho também não foram validadas.

### Contato natural do carrinho com outro jogador

Em dois replays pareados do mesmo estado salvo, foram comparadas 245 amostras
anteriores nos campos registrados. Ambos movimentaram o adversário e fizeram a
mesma aproximação; durante seis quadros, a execução de ação recebeu A com a
mesma direção mantida no controle. Não houve alteração sintética de posições.
O jogador `$0D00` entrou em `$02D0/$DB25`, enquanto `$1900` era o ator ligado
por `$00A6`.

No frame 4280, a verificação direta de bola `$85:FAEA` rejeitou o contato.
Na sequência, `$98:FE8D` comparou o ator com `$1900` e retornou carry limpo,
marcando `$0020` no campo `$6E`. A comparação usou a tabela `$81:D003`
(`12, 8`), o deslocamento do atacante e os valores registrados dos dois
jogadores. O caminho chamou `$80:EED3`; mais adiante no mesmo frame,
`$85:F8D9` limpou `$00A6` enquanto o contexto ativo era `$1900`. Na amostra
seguinte, o adversário estava em `$0328/$DB05` e a bola passou ao tipo 1 e
começou a mover-se. No controle, `$00A6` permaneceu ligado e a bola permaneceu
parada na mesma amostra. Depois, nesse replay, o adversário passou pelos
estados `$0330/$DB15` e `$0360/$DDAC`.

Esses eventos sustentam uma distinção importante: o teste direto da bola pode
falhar e ainda assim ocorrer uma colisão com o jogador ligado à bola. O
experimento não rastreou todas as instruções entre a colisão e a limpeza do
vínculo, nem prova a regra geral, a existência de falta ou a conversão das
coordenadas e velocidades para o navegador. A evidência, parâmetros e hashes
estão em [issd-slide-player-contact.json](issd-slide-player-contact.json); os
coletores são `tools/probe_issd_slide_contact_route.lua` e
`tools/probe_issd_slide_ball_gate.lua`, com auditoria reproduzível em
`tools/audit_issd_slide_player_contact.py`.

O modelo isolado `dist/native-slide-player-overlap.mjs` reproduz a aritmética
de 16 bits, as barreiras de alvo e os limites de `$98:FE8D` para a tabela
observada. `dist/test-native-slide-player-overlap.mjs` o confronta com a
captura e testa os limites. Ele permanece fora da partida até calibrarmos as
unidades e verificarmos as demais condições e consequências. O próximo passo é
rastrear os estados do jogador atingido, o lançamento da bola e as condições
de falta, com outras geometrias e controles pareados.

### Reação de salto com manutenção da bola

Em um novo par de replays sem alteração sintética da memória, o P1 executou
A durante seis quadros e entrou no carrinho `$02D0/$DB25`. Antes do comando,
215 amostras comparadas coincidiram nos campos registrados. O portador da bola
`$1900` recebeu uma reação cujo campo `$78` era 4 e cujo campo `$76` apontava
para o atacante `$0D00`; passou por `$84:A346 → $84:A736 → $84:A744` e entrou
em `$0370/$DF4D`. No controle sem A, ele não percorreu essa reação.

O portador permaneceu nesse estado por 23 quadros observados; sua coordenada
vertical assinada variou de 0 até -14 e retornou, e o vínculo `$00A6`
permaneceu em `$1900` durante a sequência e após a saída observada. Na direção
interna 4, a sequência usou os descritores `$BCD6`, `$BCDF` e `$BCE8`, cujas
fontes na ROM são `$9C:E760`, `$9C:E8E4` e `$9C:EA28`. O disassembly nomeia
esses gráficos como `Side_JumpForward1`, `2` e `3`. O P2 não pressionou botão
na janela observada. Isso confirma um exemplo de reação compatível com salto
durante o carrinho e manutenção do vínculo da bola; não determina todas as
condições que o provocam nem se outros controles podem influenciá-lo.

Os dados, trajetória, hashes e ressalvas estão em
[issd-slide-jump-reaction.json](issd-slide-jump-reaction.json), verificados por
`tools/audit_issd_slide_jump_reaction.py`. Ainda falta capturar a composição OAM
dessa reação, suas outras direções e a lógica que escolhe entre saltar, cair
ou perder a bola. Não há alteração da física da partida nesta etapa.

### Prévia visual do salto do portador

O replay pareado foi repetido com captura da OAM, VRAM, CGRAM e tela em cada
quadro da reação lateral do portador `$1900`. Os 23 quadros foram verificados
contra a geometria no banco `$88`, os tiles extraídos da ROM, a OAM do PPU e a
captura de tela. Para cada peça opaca do corpo, a comparação direta com a tela
teve zero divergências. O teste do compositor do navegador compara os 23
quadros com a OAM do PPU, permitindo diferença de até 1 por canal RGB devido
à conversão de cores de 5 bits. A evidência e hashes estão em
[issd-jump-lab-evidence.json](issd-jump-lab-evidence.json).

A sequência observada possui 10 quadros do descritor `$BCD6`, 8 de `$BCDF` e
5 de `$BCE8`; os deslocamentos em relação ao chão foram preservados quadro a
quadro. Ela está acessível em `editor/locomotion-lab.html#jump-lab`, com pausa
e inspeção manual. A prévia mostra somente o corpo do ator e a paleta
capturada, em uma direção lateral; ela não é uma composição dinâmica de todas
as equipes e não inclui uma camada de cabelo validada nem a bola. Ela ainda
não foi ligada à partida.

Para gerar localmente o recurso ignorado pelo Git a partir das capturas:

```powershell
python tools/export_issd_jump_lab.py analysis/slide-jump-graphics/A analysis/slide-jump-graphics/NEUTRAL --rom "International Superstar Soccer Deluxe/International Superstar Soccer Deluxe (USA).sfc" --state analysis/bsnes-shared-state/issd-auto-probe-20261102-211624-trigger.State --output dist/assets/issd/slide-lab-local/jump.json --evidence docs/issd-jump-lab-evidence.json
python tools/test_issd_jump_browser_pixels.py analysis/slide-jump-graphics/A --asset dist/assets/issd/slide-lab-local/jump.json --evidence docs/issd-jump-lab-evidence.json
```

Próximo passo: validar as demais direções, paletas e composição do cabelo e
mapear quando a ROM escolhe essa reação ou a queda antes de integrá-la à
máquina de estados da partida.

### Salto dinâmico em quatro direções

Foram capturados e verificados 23 quadros em cada uma de quatro direções de
tela: cima, baixo, baixo-direita e esquerda. Cada replay foi comparado a seu
controle antes da ação. A geometria veio da ROM e as peças, prioridades,
paletas e tiles foram confrontados com a OAM/VRAM/CGRAM do mesmo replay.
Nas capturas para baixo e baixo-direita, 60 pixels em cada sequência coincidem
com outros objetos OAM de índice anterior; a prévia mostra o corpo sem essas
sobreposições. Cima e esquerda tiveram correspondência direta de todos os
pixels candidatos. A fonte exata dos objetos sobrepostos não foi identificada.
Os dados e limites estão em
[issd-jump-direction-evidence.json](issd-jump-direction-evidence.json).

O laboratório usa `dist/native-jump-body.mjs` para compor o corpo com a
paleta da equipe, uniforme, tom de pele e detalhe selecionado pela camisa, a
partir das tabelas da ROM. As 92 imagens do ator capturado coincidiram com as
composições OAM de referência; 11.520 combinações de equipe, uniforme, pele,
camisa e direção passaram pela verificação de disponibilidade. Essas variantes
são uma generalização a partir das tabelas, não capturas de todas as equipes.
As outras quatro direções, a camada de cabelo, a bola e a integração dessa
reação à física da partida continuam pendentes.

Após gerar a prévia lateral descrita acima, gere o recurso dinâmico local com:

```powershell
python tools/export_issd_jump_directions.py --rom "International Superstar Soccer Deluxe/International Superstar Soccer Deluxe (USA).sfc" --state analysis/bsnes-shared-state/issd-auto-probe-20261102-211624-trigger.State --output dist/assets/issd/slide-lab-local/jump-directions.json --evidence docs/issd-jump-direction-evidence.json
node tools/test_issd_jump_dynamic_local.mjs
```

As capturas e os gráficos derivados são locais e não são distribuídos. Para
regenerar esse conjunto também é necessário executar os replays presentes em
`analysis/slide-jump-graphics` e `analysis/jump-directions` com o coletor
`tools/capture_issd_slide_replay.lua`; eles não acompanham o repositório.

### Salto de reação nas oito direções

Os quatro sentidos que faltavam foram capturados diretamente em novos replays
pareados. A sequência de 23 quadros está disponível no laboratório para as
oito direções, com equipe, uniforme, pele e número de camisa selecionáveis.
O renderizador monta as variantes usando as tabelas da ROM; os 184 quadros do
ator capturado correspondem às composições OAM/VRAM/CGRAM, e 23.040
combinações passaram pela verificação de disponibilidade. Essas combinações
não são capturas individuais de partida de cada equipe.

A distinção de gatilho importa: a direção lateral inicialmente investigada
foi observada com o atacante em `$02D0/$DB25`, a rota de carrinho. As outras
sete foram capturadas com o atacante em `$02C8` e scripts `$DF7F` ou `$DFAD`,
portanto confirmam as poses da mesma reação em outras ações defensivas, mas
não provam que todas ocorram durante um carrinho. Em cada captura, o portador
manteve `$00A6` durante os 23 quadros. Os gatilhos e hashes de cada caso estão
em [issd-jump-direction-evidence.json](issd-jump-direction-evidence.json).

Alguns pixels do corpo nas capturas ficam encobertos por outros objetos OAM;
essas amostras as diferenças encontradas coincidem em cor e posição com uma
peça OAM anterior. A identidade e a camada completa desses objetos ainda não
foram confirmadas. A prévia representa o corpo sem eles; cabelo e bola não
estão incluídos. A física e as condições de escolha da reação ainda não foram
integradas à partida web. O recurso de gráficos derivados continua local e
ignorado pelo Git.

### Queda após contato confirmado com carrinho

O replay pareado de contato `$02D0/$DB25` foi repetido com captura do jogador
atingido `$1900`, sem alterar a RAM. A sequência visual observada compreende
35 quadros: 11 no estado `$0328/$DB05`, descritor `$B5B3`; 8 no estado
`$0330/$DB15`, descritor `$B5BC`; e 16 no estado `$0360/$DDAC`, descritor
`$B4ED`. O ator entra na recuperação `$02F8/$DB5B` em seguida, que não está
incluída nesta prévia de queda. Os dados da comparação pareada de contato estão
em [issd-slide-player-contact.json](issd-slide-player-contact.json).

A geometria e os tiles de todos os quadros foram confrontados com a ROM e com
OAM, VRAM e CGRAM do PPU. Dos 10.445 pixels candidatos, 21 diferiram da tela e
coincidiram em posição e cor com outros objetos OAM anteriores; a identidade
dessas peças não foi determinada. Os hashes e valores constam em
[issd-fall-lab-evidence.json](issd-fall-lab-evidence.json). O teste do
compositor no navegador confirma os 35 quadros contra a composição do PPU,
com tolerância de até 1 por canal de cor na conversão de 5 bits.

A prévia está em `editor/locomotion-lab.html#fall-lab`, com pausa e seleção de
quadro. Mostra apenas o corpo da vítima capturada, com uma direção e uniforme;
a posição do ator é recentralizada para comparar as poses. O deslocamento sobre
o campo, cabelo, outras direções e uniformes, recuperação e integração com a
física da partida permanecem pendentes. O ciclo de reprodução é somente uma
prévia de laboratório, não uma repetição da queda na partida.

Para reconstruir os gráficos localmente a partir das capturas já realizadas:

```powershell
python tools/export_issd_fall_lab.py analysis/slide-fall-graphics/A analysis/slide-fall-graphics/NEUTRAL --rom "International Superstar Soccer Deluxe/International Superstar Soccer Deluxe (USA).sfc" --state analysis/bsnes-shared-state/issd-auto-probe-20261102-211624-trigger.State --output dist/assets/issd/slide-lab-local/fall.json --evidence docs/issd-fall-lab-evidence.json
python tools/test_issd_fall_browser_pixels.py analysis/slide-fall-graphics/A --asset dist/assets/issd/slide-lab-local/fall.json --evidence docs/issd-fall-lab-evidence.json
```

O arquivo gerado e as capturas permanecem locais e são ignorados pelo Git; a
ROM original não é alterada nem incluída na distribuição.

### Queda por equipe e início da recuperação

O corpo da queda capturada agora é composto no laboratório para 36 equipes,
dois uniformes, dois tons de pele e camisas de 1 a 20, usando as tabelas de
paletas e o tile de detalhe da ROM. A direção continua sendo a única observada
nesse contato. Os 35 quadros do ator capturado permanecem pixel a pixel iguais
à composição OAM de referência; 2.880 combinações passaram pela verificação de
disponibilidade. As demais aparências são derivadas das tabelas, não capturas
individuais de partida.

A reprodução dinâmica acrescenta os cinco quadros observados imediatamente
após a queda, no estado `$02F8/$DB5B`, descritor `$B2EC`. Em seguida, nesse
replay, o ator apareceu no estado transitório `$0008` e depois em `$0010` com
o script `$D320`; o vínculo da bola permaneceu zero nas amostras conferidas.
Os cinco quadros foram confrontados com ROM, OAM/VRAM/CGRAM e captura de tela;
o navegador também foi comparado com o PPU com tolerância de 1 por canal RGB.
Veja [issd-fall-recovery-evidence.json](issd-fall-recovery-evidence.json).
Essa sequência é específica do contato registrado e não comprova a duração
ou os estados de todas as recuperações.

No [laboratório](../dist/editor/locomotion-lab.html), a prévia dinâmica tem
40 quadros: 35 da queda e cinco do início da recuperação. A prévia permanece
centralizada e não substitui a trajetória no campo; cabelo, outras direções,
regras de falta e integração com a física ainda estão pendentes. Quando o
recurso dinâmico local não existe, o painel mantém a captura original de
35 quadros.

Para gerar os recursos derivados localmente, depois da captura documentada na
seção anterior:

```powershell
python tools/export_issd_fall_recovery.py analysis/slide-fall-graphics/A analysis/slide-fall-graphics/NEUTRAL --rom "International Superstar Soccer Deluxe/International Superstar Soccer Deluxe (USA).sfc" --state analysis/bsnes-shared-state/issd-auto-probe-20261102-211624-trigger.State --output dist/assets/issd/slide-lab-local/fall-recovery.json --evidence docs/issd-fall-recovery-evidence.json
python tools/export_issd_fall_dynamic.py --rom "International Superstar Soccer Deluxe/International Superstar Soccer Deluxe (USA).sfc" --state analysis/bsnes-shared-state/issd-auto-probe-20261102-211624-trigger.State --output dist/assets/issd/slide-lab-local/fall-dynamic.json --evidence docs/issd-fall-lab-evidence.json --recovery-evidence docs/issd-fall-recovery-evidence.json
node tools/test_issd_fall_dynamic_local.mjs
```

Os arquivos com gráficos continuam locais e ignorados pelo Git.

### Queda em três direções capturadas

O laboratório agora oferece as direções de tela baixo-esquerda, direita e
cima-esquerda, com uniformes e aparência derivados das tabelas da ROM. Cada
prévia contém 35 quadros da queda e cinco quadros da continuação observada no
respectivo replay. Foram conferidos 120 quadros de referência e 8.640
combinações de equipe, uniforme, tom de pele, camisa e direção; apenas o ator
original de cada captura foi comparado individualmente com o emulador.

A distinção entre gatilhos foi mantida: a direção baixo-esquerda veio do
contato de carrinho `$02D0/$DB25`; as direções direita e cima-esquerda vieram
de uma ação defensiva `$02C8/$DF7F`. Elas mostram a mesma família de reações
de queda, mas não comprovam essas duas direções durante um carrinho. Após os
35 quadros, a captura direita entra em `$0340/$D94D`, enquanto a cima-esquerda
entra em `$02F8/$DB5B`; por isso o painel as identifica genericamente como
continuação, sem presumir que ambas sejam a mesma recuperação.

Na direção cima-esquerda, 182 pixels candidatos da queda coincidem com peças
OAM anteriores em posição e cor, indicando sobreposição; a identidade dessas
peças ainda não foi determinada. Os demais pixels e os tiles foram verificados,
e a composição do navegador foi comparada com a OAM do PPU. Evidências e
limitações estão em [issd-fall-direction-evidence.json](issd-fall-direction-evidence.json).
Outras direções, cabelo, continuação completa e física permanecem pendentes.

O comando `tools/export_issd_fall_dynamic.py` documentado acima agora usa,
além da captura original, os replays locais `analysis/fall-directions/Right`
e `analysis/fall-directions/UpLeft`. O JSON com gráficos gerado continua local
e ignorado pelo Git.

### Queda em cinco direções capturadas

Dois replays pareados acrescentaram as direções de tela cima-direita e
baixo-direita à prévia de queda. O laboratório oferece agora cinco direções,
cada uma com 35 quadros da queda e cinco da continuação observada, além das
variantes de equipe, uniforme, pele e camisa extraídas das tabelas da ROM.
Os 200 quadros do ator de referência coincidiram com as composições capturadas;
14.400 combinações passaram pela verificação de disponibilidade.

A direção baixo-esquerda continua sendo a única capturada no estado de carrinho
`$02D0/$DB25`. As quatro restantes foram observadas após ações defensivas
`$02C8/$DF7F` ou `$02C8/$DFAD`; elas não demonstram, por si só, o mesmo
resultado contra carrinhos. Nas novas capturas, a continuação observada começa
em `$0340/$D94D` para cima-direita e em `$02F8/$DB5B` para baixo-direita.

Na captura baixo-direita, 1.973 pixels candidatos da queda coincidem em posição
e cor com outros objetos OAM anteriores; a identidade dessas peças ainda não
foi determinada. A geometria, os tiles e a composição do PPU foram conferidos,
mas a prévia do corpo isolado não reproduz essa sobreposição. Para cima-direita,
esse número é 10. Os registros, gatilhos, hashes e limitações estão em
[issd-fall-direction-evidence.json](issd-fall-direction-evidence.json).
Outras direções, a camada de cabelo, as condições completas da reação e sua
integração com a física da partida permanecem pendentes.

O gerador `tools/export_issd_fall_dynamic.py` também requer as capturas locais
`analysis/fall-directions/UpRight` e `analysis/fall-directions/DownRight`. Os
gráficos derivados são gerados localmente e continuam ignorados pelo Git.

### Sexta direção da queda

Um replay pareado acrescentou a direção de tela esquerda à prévia da queda.
O laboratório oferece agora seis direções, cada uma com 35 quadros da queda
e cinco de continuação observada, com as variantes de uniforme derivadas das
tabelas da ROM. Os 240 quadros dos atores de referência coincidiram com suas
composições OAM/VRAM/CGRAM; 17.280 combinações passaram pela verificação de
disponibilidade, sem implicar captura individual de cada equipe.

O novo caso ocorreu após a ação defensiva `$02C8/$DFAD`, não após o estado de
carrinho `$02D0/$DB25`. Após a queda, sua continuação observada começa em
`$0350/$E214`; o painel não presume que seja igual à continuação das demais
capturas. Dos pixels candidatos da queda, 342 coincidem em posição e cor com
outros objetos OAM anteriores, cuja identidade permanece pendente. A evidência
está em [issd-fall-direction-evidence.json](issd-fall-direction-evidence.json).

As direções de tela cima e baixo continuam pendentes de captura verificável,
assim como cabelo, continuação completa e integração da física. O gerador
`tools/export_issd_fall_dynamic.py` usa também o replay local
`analysis/fall-directions/Left`; os gráficos gerados não são distribuídos.

### Busca controlada pelas duas direções restantes

O controle automatizado aceita `ISSD_AUTO_P2_PRE_DIRECTION` e
`ISSD_AUTO_P2_PRE_START` para orientar o jogador 2 antes da ação, em um replay
isolado, sem editar a ROM. A janela termina no passo relativo 420 e não pode
se sobrepor à primeira movimentação; sem essas opções o comportamento anterior
é preservado. A direção e a janela ficam registradas no JSONL da captura.

Foram executadas seis tentativas com o mesmo estado inicial usado nos replays
anteriores: movimentação inicial `Right` até 260, `UpLeft` até 340 ou `UpRight`
até 360, seguida de `Up` ou `Down` entre 416 e 419. Os registros locais estão
em `analysis/fall-p2-pre-search/`. Em `UpRight-360-Down`, o ator `$1900`
entrou no estado `$0328` do passo 425 ao 435, com direção interna 0; nas
outras cinco tentativas esse estado não apareceu para esse ator na janela
420–478. A entrada `Down` foi observada no registro do controle durante a
janela solicitada. Esses dados não constituem uma captura validada das duas
direções de tela ainda faltantes e não alteram as animações do laboratório.

Próximo passo: variar a aproximação e a duração da orientação antes do contato,
registrar uma queda natural com direção interna 6 ou 2 e produzir, para cada
caso, um replay pareado com controle neutro e validação OAM/VRAM/CGRAM antes
de disponibilizar a animação.

### Novas variações do contato e inspeção das capturas

Foram realizados seis replays com as mesmas três movimentações anteriores,
mas com `Up` ou `Down` entre os passos relativos 405 e 419. Nenhum registrou
o estado de queda `$0328` de qualquer ator na janela amostrada 420–478.

Outros oito replays aplicaram `A` junto com cada uma das oito direções do
defensor entre 420 e 425, após a movimentação `UpRight` do jogador 2 até 360.
Os registros confirmam os comandos compostos; somente `A+Right` produziu o
estado `$0328` nessa janela, no ator `$1900`, passos 425–435, direção interna
7, já presente no laboratório. Esses resultados são específicos do estado
inicial e das trajetórias experimentadas; não demonstram que as outras
reações sejam impossíveis no jogo.

A opção `ISSD_AUTO_EARLY_ACTION_DIRECTION` permite repetir essas entradas na
ação inicial; a opção anterior `ISSD_AUTO_P1_ACTION_DIRECTION` se refere à
ação posterior, no passo 480. O utilitário
`python tools/summarize_issd_fall_search.py <pasta>` resume os candidatos e
registra lacunas na amostragem e hashes dos registros, sem afirmar causalidade
ou substituir a validação visual e o controle pareado. As capturas ficam em
`analysis/fall-p2-long-search/` e `analysis/fall-early-action-search/`.
As direções internas 2 e 6 ainda exigem captura verificável.

### Busca por trajetórias verticais e aproximação do defensor

Mais 24 replays isolados ampliaram a busca sem alterar a memória da partida.
Em oito, o jogador 2 se moveu diretamente para cima ou para baixo até os passos
260, 300, 340 ou 380. Duas tentativas para baixo produziram queda na direção
interna 1, já capturada. Nas outras 16 tentativas, o defensor mudou de direção
entre 410 e 419, em todas as oito direções, antes de apertar `A`: oito com o
jogador 2 tendo percorrido `UpRight` até 360 e oito com `Down` até 300. Foram
observadas três quedas de direção 7 no primeiro grupo e duas de direção 1 no
segundo. Todas as janelas 420–478 têm amostras completas e os processos
registraram término da sessão.

O inventário com hashes, quadros e primeiros e últimos registros de cada
candidato está em [issd-fall-search-evidence.json](issd-fall-search-evidence.json).
São observações dos cenários testados, não uma prova sobre outras trajetórias.
As direções internas 2 e 6 continuam pendentes de captura e validação; os novos
resultados não foram apresentados como animações adicionais no laboratório.

### Investigação de goleiros retomada

A captura natural já documenta descritores de mergulho para goleiros e sua
correlação com fontes gráficas da ROM; também foram identificadas famílias de
recursos para bola agarrada e reposição baixa. Detalhes, limites e comandos de
reprodução estão em [issd-animation-inventory.md](issd-animation-inventory.md)
e [issd-goalkeeper-action-evidence.json](issd-goalkeeper-action-evidence.json).
Defesa, retenção e reposição com as mãos ainda não têm validação quadro a
quadro suficiente para serem integradas como mecânica original.

O mapa estático de reposição baixa do goleiro foi recuperado: `$82:E80A`
contém oito índices de direção e três descritores por índice, selecionados
pela rotina `$84:ECEF`. Uma captura separada apresenta nove amostras de um
recurso identificado como bola agarrada, mas há diferença ainda não explicada
entre a pose registrada e o ponteiro no descritor. Ver detalhes e limites em
[issd-animation-inventory.md](issd-animation-inventory.md) e
[issd-goalkeeper-lowthrow-table.json](issd-goalkeeper-lowthrow-table.json).

A análise de `$84:E6C7` mostrou que o descritor pode ser registrado antes
da atualização da pose, condicionada por três testes. A captura antiga
também excluía poses diretas na faixa de ROM; portanto as nove amostras de
`$CC73` não comprovam o gráfico de bola agarrada exibido. O motivo concreto
da divergência permanece pendente de uma captura dos guardas e do desenho.

O novo observador de goleiro registra as entradas em `$84:E6C7`, guardas,
estado da bola e controles sem alterar a memória. Num replay pareado, 381
amostras coincidiram com o controle, mas os scripts de bola agarrada e
lançamento baixo não ocorreram. A evidência e suas limitações estão em
[issd-goalkeeper-transfer-audit.json](issd-goalkeeper-transfer-audit.json) e
[issd-animation-inventory.md](issd-animation-inventory.md).

Uma pose estática de goleiro do script `$E7C7` foi reconstruída e comparada
com ROM, OAM, VRAM, CGRAM e imagem da PPU; os 359 pixels candidatos coincidem.
A prévia local está no laboratório `#goalkeeper-lab`. Trata-se de uma pose,
não da sequência de defesa ou reposição; detalhes e limites estão em
[issd-animation-inventory.md](issd-animation-inventory.md) e
[issd-goalkeeper-catch-pose-audit.json](issd-goalkeeper-catch-pose-audit.json).

Doze replays pareados com o goleiro selecionado identificaram sequências
associadas a `A` e `B` em duas janelas posteriores; `B` apontou para recursos
nomeados `HighThrow`. Uma pose dessa sequência foi validada com 435 pixels e
está no laboratório, mas a animação completa e a física de reposição seguem
pendentes. Ver [issd-goalkeeper-input-audit.json](issd-goalkeeper-input-audit.json)
e [issd-animation-inventory.md](issd-animation-inventory.md).

A prévia de lançamento alto no laboratório agora reproduz cinco poses e 28
quadros observados em um replay. As poses foram verificadas em replays
pareados do mesmo estado; duas têm pixels coincidentes com outro objeto OAM,
cuja identidade ainda não foi confirmada. Outras direções, continuação e
física da bola permanecem pendentes. Veja
[issd-goalkeeper-throw-sequence-audit.json](issd-goalkeeper-throw-sequence-audit.json)
e [issd-animation-inventory.md](issd-animation-inventory.md).

O lançamento alto do goleiro foi ampliado no laboratório para os índices
internos 0, 7 e 1, com cinco poses por sequência e cadências observadas em
replays pareados. A correspondência com a direção da tela, outras aparências,
continuação e física da bola seguem pendentes. Evidências em
[issd-goalkeeper-directed-throw-audit.json](issd-goalkeeper-directed-throw-audit.json).

Dezesseis replays adicionais com trajetórias longas e mudanças de direção não
revelaram outros índices de lançamento além de 0, 1 e 7 neste estado inicial.
A transição posterior ao trecho da primeira prévia foi observada em estado,
mas ainda não validada visualmente. Detalhes em
[issd-goalkeeper-direction-search.json](issd-goalkeeper-direction-search.json)
e [issd-animation-inventory.md](issd-animation-inventory.md).

No replay pareado do lançamento alto na orientação interna 0, foi observada
entrada em `$85:EE38` e `$85:F8B9` antes da mudança do vínculo `$00A6` e dos
campos de velocidade da bola. A marca correspondente aparece no laboratório
para esse replay; unidades, outras orientações e física completa ainda estão
pendentes. Evidência em
[issd-goalkeeper-throw-release-audit.json](issd-goalkeeper-throw-release-audit.json).

Nos replays pareados dos índices internos 7 e 1, o vínculo com o goleiro foi
limpo no sétimo quadro das sequências após entradas em `$85:EE38` e
`$85:F8B9`; os controles neutros mantiveram o vínculo. A marca foi estendida
no laboratório, sem extrapolar unidades ou física. Ver
[issd-goalkeeper-directed-release-audit.json](issd-goalkeeper-directed-release-audit.json).

Os lançamentos de goleiro nas orientações internas 0, 7 e 1 passaram por
`$83:94A4/$83:9E32` com ângulos e parâmetros que coincidem com as tabelas da
ROM. Três vetores observados no quadro seguinte foram registrados, ainda em
unidades não calibradas; o cálculo Mode 7 e as atualizações posteriores seguem
pendentes de validação antes de alterar a física web. Evidência em
[issd-goalkeeper-throw-vector-audit.json](issd-goalkeeper-throw-vector-audit.json).

Os três vetores de lançamento do goleiro agora foram conferidos além da entrada:
produtos Mode 7, correção de sinais e words gravadas na bola coincidem com os
coeficientes da ROM nos replays. A escala web e a física posterior permanecem
pendentes. Ver [issd-goalkeeper-vector-products-audit.json](issd-goalkeeper-vector-products-audit.json).

Após o lançamento alto do goleiro, 143 chamadas da integração horizontal da
bola foram verificadas na entrada e na saída: a soma 16.16 de posição e
velocidade coincidiu em X e Y. Mudanças entre chamadas ainda têm origem
indeterminada, e não há escala validada para a web. Ver
[issd-goalkeeper-ball-integration-audit.json](issd-goalkeeper-ball-integration-audit.json).

A diferença entre integrações de bola após o lançamento foi explicada em 133
intervalos observados por uma translação comum à bola e ao ator em `$83:CFCB`.
Uma função isolada reproduz a soma 16.16 e essa translação, testada com três
capturas; ela ainda não modifica a partida web. Ver
[issd-goalkeeper-world-translation-audit.json](issd-goalkeeper-world-translation-audit.json).

A atualização aérea vertical da bola tipo `$0A` foi verificada em 143 passos
de replays do goleiro: aceleração e soma de altura em 16.16 coincidiram. Uma
função isolada cobre esse ramo; quique, solo e escala web continuam pendentes.
Ver [issd-goalkeeper-vertical-audit.json](issd-goalkeeper-vertical-audit.json).
