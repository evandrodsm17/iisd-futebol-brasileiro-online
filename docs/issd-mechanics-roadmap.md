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
