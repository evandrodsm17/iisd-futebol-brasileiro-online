# Roteiro de mecânica fiel — ISS Deluxe

Para prioridades e acompanhamento de implementação, consulte o
[checklist de física, eventos e animações](issd-checklist-fisica-animacoes.md).

## Pontos de entrada confirmados

| Sistema | ROM / RAM | Papel |
| --- | --- | --- |
| Filtro de ator por fase | `$7E:00C0` → `$83:CF86` | Gate de 15 entradas; não é a máquina completa de fases |
| Fase secundária | `$83:F375` | Continuação do dispatch de fase |
| Colisão/física | `$83:D77F` | Modos de colisão e bola |
| Sequenciador associado à bola | `$83:D9A5` | Seis estados e temporizadores identificados; associação específica com trave ou rede ainda não comprovada |
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

Um quique natural de bola tipo 2 foi observado em replay longo iniciado pela
reposição do goleiro, após mudança intermediária de estado. A redução vertical,
inversão e redução horizontal desse caso foram reproduzidas em função isolada;
não estão integradas à partida nem generalizadas para outros ramos. Ver
[issd-ball-type2-bounce-audit.json](issd-ball-type2-bounce-audit.json).

Dezesseis replays adicionais variando a direção prévia e o momento do comando
não registraram bola tipo `$0A` no ponto de quique `$83:8883`. Isso é uma
limitação dos cenários testados; outros tipos e outros caminhos foram vistos.
Ver [issd-goalkeeper-landing-search.json](issd-goalkeeper-landing-search.json).

O objetivo da reposição livre inclui voo, quique, desaceleração e parada. A
mudança do tipo interno da bola não prova contato com jogador. Três trajetórias
já capturadas passaram por reinicialização com endereços de outros atores como
argumento, mas a causa ainda não foi estabelecida; ver
[issd-goalkeeper-flight-reinitialization.json](issd-goalkeeper-flight-reinitialization.json).

A recepção alta e a escolha de companheiro no lançamento do goleiro foram
adicionadas à investigação. Uma tabela direcional candidata aponta para
recursos nomeados `CatchBallWithKnee`, mas a associação com domínio no peito
não está comprovada; os seis replays instrumentados não produziram callback
positivo. Ver [issd-player-receive-candidate.json](issd-player-receive-candidate.json).

Observamos os dez companheiros em três reposições e controles pareados. Há
mudanças de estado e aproximação relativa à bola, mas os dados não distinguem
movimento intencional do jogador de deslocamento da bola ou da referência;
a seleção automática do receptor continua pendente. Ver
[issd-goalkeeper-teammates-observation.json](issd-goalkeeper-teammates-observation.json).

Após remover a translação comum, foram comparados os deslocamentos de dez
companheiros em três reposições e controles. Em todos os lances houve troca do
jogador selecionado após a liberação, sem botão pressionado; um caso não
corresponde ao mais próximo por distância horizontal simples. Elegibilidade,
previsão e rotina de seleção seguem pendentes. Ver
[issd-goalkeeper-teammate-motion-audit.json](issd-goalkeeper-teammate-motion-audit.json).
# Controle após recuperação de bola solta — protótipo web

Na versão web, quando um jogador da equipe humana recupera uma bola solta, o controle passa a ele. Isso também permite continuar a jogada quando um companheiro recolhe uma bola após uma reposição; a troca ocorre na recuperação efetiva, não no lançamento. A regra usa a detecção de contato e o intervalo de proteção já existentes. Uma recuperação adversária ou a ausência de contato não altera o jogador controlado.

**Estado da evidência:** esta é uma política provisória de jogabilidade, não uma reprodução comprovada da seleção de jogador da ROM. Observações de lançamento do goleiro mostram mudança automática de controle após a soltura, mas ainda não identificam a regra de escolha nem demonstram que ela dependa da recuperação. Reposição com as mãos, trajetória, domínio no peito e escolha antecipada de recebedor permanecem pendentes de investigação; um tiro de meta não deve ser tratado como posse nas mãos. Fontes: `docs/issd-goalkeeper-transfer-audit.json` e `docs/issd-goalkeeper-teammate-motion-audit.json`.

**Verificação:** `node dist/test-match-flow.mjs` cobre recuperação por companheiro, adversário, ausência de contato e proteção temporária. O teste não valida a fidelidade à ROM.

## Reação experimental ao carrinho na partida web

Ao usar a ação defensiva com animação de carrinho disponível, se a regra provisória de roubo por proximidade entregar a bola ao jogador controlado, o adversário pode reproduzir a queda capturada para a direção de tela 5. A equipe, o uniforme, a pele e o número usam a composição dinâmica local do laboratório. A reação só é ativada quando os dados locais, a combinação e a escala estão disponíveis; goleiros e direções não confirmadas nesse contexto conservam o comportamento anterior. Os arquivos gráficos locais derivados da ROM não são distribuídos.

Durante os 40 quadros disponíveis da captura e sua continuação, o atingido não persegue nem recupera a bola; depois volta ao comportamento normal. Esses 40 quadros são a duração dos dados usados, **não uma duração de incapacidade comprovada na ROM**. O acionamento após roubo também é uma aproximação do protótipo: a lógica original de contato, salto de desvio, falta, lesão e recuperação completa continua pendente. As demais direções de queda observadas em outros contextos não foram automaticamente classificadas como vítimas de carrinho. A CPU ainda não inicia esse carrinho experimental contra o jogador humano.

Fontes: `dist/editor/fall-lab.mjs`, `dist/native-fall-body.mjs` e evidências no inventário `docs/issd-animation-inventory.md`. Testes: `node dist/test-tackle-reaction.mjs`, `node dist/test-ball-steal.mjs`, `node dist/test-native-fall-body.mjs` e `node dist/test-match-flow.mjs`; eles validam integração e limites, não equivalência visual ou física com a ROM.

### Verificação de contato entre os atletas

A reação de queda agora também requer sobreposição entre o jogador do carrinho e o portador, evitando que a proximidade com a bola, isoladamente, derrube um adversário distante. O adaptador `browserSlidePlayerOverlap` usa o modelo de `98:FE8D` e `DATA_81:D003`, testado contra o evento registrado em `docs/issd-slide-player-contact.json`. A conversão do campo web para unidades nativas reaproveita a escala experimental do contato com a bola; deslocamentos e flags nativos são considerados zero por ainda não estarem mapeados para o protótipo. Por isso, o resultado é uma aproximação de geometria, não uma decisão completa de colisão ou falta da ROM. A transferência de posse mantém o critério provisório anterior.

Verificação: `node dist/test-native-slide-player-overlap.mjs` cobre captura e limites nativos e o adaptador; `node dist/test-ball-steal.mjs` verifica que contato com a bola sem proximidade do atleta não dispara queda.

### Continuidade da queda e despacho nativo da reação

O protótipo zera a velocidade residual de um jogador caído após a separação de corpos, evitando que uma colisão durante a queda o faça deslizar ao recuperar o controle. Uma tentativa defensiva só pode iniciar a queda se a própria tentativa atual tiver iniciado um carrinho suportado; uma animação anterior não é suficiente. A duração e as condições da queda continuam provisórias.

Na investigação do salto, `84:A346` bloqueia o despacho quando `$00C0` é diferente de zero e, caso contrário, seleciona uma das entradas de `DATA_84A35F` pelos quatro bits inferiores de `$78` do ator. A entrada 4 passa por `84:A736`: se o ator é o vinculado por `$00A6` e o bit 15 de `$0078` global está ligado, segue para `84:A977`; caso contrário, segue para `84:A744`, que instala o estado `$0370` e a tabela de animação `$82:DF4D`. Os dois campos `$78` não devem ser confundidos. O modelo isolado `dist/native-player-reaction.mjs` reproduz esse trecho para investigação; ele não identifica quem define a reação nem foi ligado ao jogo web. A rota `84:A744` concorda com o replay `docs/issd-slide-jump-reaction.json`, mas o replay disponível não registra todos os campos necessários para validar as demais ramificações dinamicamente.

Fontes: `Routine_Macros_ISSD.asm`, rótulos `CODE_84A346`, `DATA_84A35F`, `CODE_84A736` e `CODE_84A744`; captura `docs/issd-slide-jump-reaction.json`. Testes: `node dist/test-native-player-reaction.mjs`, `node dist/test-tackle-reaction.mjs` e `node dist/test-ball-steal.mjs`.

### Escolha parcial da reação após contato de carrinho

A leitura estática de `84:A0D1` mostra que, após a sobreposição em `98:FE8D`, a rotina chama `80:EED3`. Em `80:EED3`, há saídas antecipadas envolvendo `$68` e o bit `$0100` de `$6C` do alvo, a configuração de faltas e o sinal de `$11F9`; outra saída ocorre se o bit `$4000` de `$60` do atacante estiver desligado. Quando essas barreiras são ultrapassadas, a rotina consulta `DATA_81:957F` e marca `$0200` em `$6E` do alvo. Se `$11F9` não for negativo, a entrada da tabela for 1 e o bit `$0800` de `$60` do alvo estiver desligado, ela grava no alvo a reação 0 quando `$30` do alvo é 1 e, caso contrário, a reação 4; `$76` do alvo recebe o endereço do atacante. A reação 4 é a rota que pode alcançar o salto descrito acima.

Quando a rotina retorna carry ligado, o chamador `84:A0D1` grava no alvo `$78 = $2002` e `$76 = endereço do atacante`. Saídas antecipadas com carry limpo não devem ser confundidas com a escolha de reação 4. O modelo isolado `dist/native-slide-reaction-choice.mjs` recebe o byte da tabela como entrada e reproduz apenas essas decisões e escritas observáveis no disassembly. O cálculo do índice da tabela envolve `80:E8AD`, atributos e outros dados; ainda não foi validado contra captura pareada. Também não está comprovado que toda ocorrência da reação 4 seja uma esquiva de carrinho. Por isso o modelo **não decide o resultado na partida web** e não representa uma regra completa de falta.

Fonte: `Routine_Macros_ISSD.asm`, `CODE_84A0D1` e `CODE_80EED3` a `CODE_80EF7A`; contexto do replay em `docs/issd-slide-jump-reaction.json`. Teste estático de ramos: `node dist/test-native-slide-reaction-choice.mjs`. As entradas e resultados dessa rotina ainda precisam de captura dinâmica antes de aplicação em gameplay.

#### Cálculo estático do índice de `DATA_81:957F`

`80:EED3` usa o byte baixo de `$30` do atacante para indexar `DATA_81:94C5 - 1`. Para valores de 1 a 6, as classes lidas são `0, 0, 0, 1, 1, 2`. Depois troca temporariamente o direct page para o alvo e chama `80:E8AD` com A=2. Essa rotina usa o `$68` do alvo, o lado determinado pelo endereço do ator e a tabela `DATA_81:95EB` para localizar um registro em RAM; retorna uma palavra e deixa X apontando para ela. As leituras longas seguintes são de `X+1` e `X+6` **desse registro**, não necessariamente campos diretamente acessíveis do objeto do atacante.

Com `a = (palavra_retornada >> 4) & 15`, `b = (palavra_em_X+1 >> 4) & 15`, `c = palavra_em_X+6 & 15`, e `classe` da tabela anterior, o índice é `4 * (floor((a + b) / 2) + c + classe) + ($0078_global & 3)`. A tabela `DATA_81:957F` contém 68 bytes no trecho delimitado por `DATA_81:95C3`; seus 68 bytes foram comparados com a ROM local em offset LoROM sem cabeçalho `0x957F` e coincidiram. `dist/native-slide-reaction-choice.mjs` calcula o índice quando recebe esses valores brutos. Ele recusa classes fora de 1 a 6 e índices fora do trecho identificado, sem afirmar o que o processador leria além dele.

Essa etapa é uma reconstrução **estática**. A observação posterior dos operandos está registrada abaixo; ela não identifica o significado dos atributos nem valida a decisão para aplicação geral na partida. Fontes: `CODE_80EED3`, `CODE_80E8AD`, `DATA_8194C5`, `DATA_81957F`, `DATA_8195EB` no `Routine_Macros_ISSD.asm`; verificação de limites e exemplos em `node dist/test-native-slide-reaction-choice.mjs`.

#### Primeira observação dos operandos da reação

Um replay isolado repetiu o lance de salto com hooks passivos em `80:EED3`, no retorno de `80:E8AD`, em `80:EF7A` e em `84:A346`. As 215 amostras comuns anteriores ao comando coincidiram com o controle neutro nos campos registrados; P1 recebeu A por seis quadros e P2 permaneceu sem botão nessa janela. No frame 4221, o atacante era `$0D00` e o portador `$1900`. O retorno de `80:E8AD` registrou `X=$3F24`, palavra `$7577`, palavra em `X+1=$6775` e palavra em `X+6=$0002`; o byte baixo de `$30` do atacante era 5 e `$0078 global=$410B`. O cálculo produz índice **43**, cujo byte na ROM é **1**. Em seguida, `80:EF7A` recebeu A=4 para gravação no alvo; no despacho, o alvo já tinha `$78=4`, `$76=$0D00` e continuava ligado à bola por `$00A6`.

Isso confirma os operandos e a reação gravada **para este lance**, além da compatibilidade do índice reconstruído com o byte lido diretamente da ROM pelo auditor. O hook não registra a instrução de leitura da tabela, portanto o byte é derivado da ROM e do índice, não uma observação direta do barramento. A configuração de falta não foi registrada, mas nesse evento `$68` do alvo era 9, o que evita a saída antecipada dependente dela. Não se conclui a identidade dos atributos, a regra geral de esquiva nem a escala do navegador. A captura completa fica em `analysis/`, ignorada no Git; o resumo sem ROM está em `docs/issd-slide-reaction-choice-observation.json`. Instrumentação: `tools/probe_issd_slide_reaction_choice.lua`; auditoria reproduzível: `tools/audit_issd_slide_reaction_choice.py`; comparação do modelo com os valores capturados: `node dist/test-native-slide-reaction-choice.mjs`.

#### Comparação com reação de queda

Um segundo replay passivo reproduziu o contato com queda, agora com os mesmos hooks. As 245 amostras comuns anteriores ao carrinho coincidiram com o controle neutro nos campos registrados; durante seis quadros P1 recebeu A+direita, enquanto o controle recebeu apenas direita. No frame 4280, os valores do mesmo registro eram novamente `$7577`, `$6775` e `$0002`, com classe do atacante 5. Dessa vez `$0078 global=$1088`, cujos dois bits baixos são 0: o cálculo produz índice **40**, cujo byte na ROM é **0**. No despacho posterior, o alvo apresentava `$78=$2002` e `$76=$0D00`. A captura pareada também confirmou que o vínculo da bola foi limpo na amostra seguinte, enquanto permaneceu no controle.

No salto, os dois bits baixos do campo global eram 3 e o índice era 43, cujo byte é 1; na queda, eram 0 e o índice era 40, cujo byte é 0. Os dois lances têm outras diferenças de entrada e contexto: a comparação **não prova** que mudar esse campo isoladamente provocaria o outro resultado nem identifica sua origem ou significado. As tabelas foram consultadas offline usando operandos capturados, não pelo hook no barramento. A configuração de falta não foi registrada, mas `$68` do alvo era 9 nos dois eventos e contorna a barreira inicial dependente dessa configuração. A escolha geral, as outras barreiras da colisão e a conversão ao campo web seguem pendentes.

Evidências sem ROM: `docs/issd-slide-reaction-choice-observation.json` e `docs/issd-slide-reaction-fall-observation.json`. A captura de queda é auditável por `tools/audit_issd_slide_reaction_fall.py`; `node dist/test-native-slide-reaction-choice.mjs` confronta os dois eventos com o modelo. Os dados brutos e estados continuam locais em `analysis/`.

#### Origem observada de `$0078` nos dois lances

O laço principal `80:80D4` executa `LDA $78`, `ADC $3A`, `STA $78` e repete; o `ADC` usa o carry de entrada e atualiza o carry para a próxima soma. Dois novos replays isolados registraram as escritas no campo global durante os dois quadros que cercam cada reação. Todas as escritas observadas nessas janelas foram atribuídas ao retorno em `$80:80DE`, com direct page zero. Entre escritas consecutivas no mesmo quadro, o modelo `novo = (anterior + $003A + carry_anterior) & $FFFF` coincidiu em **2.048 pares do salto e 1.223 pares da queda**, incluindo exemplos com carry. A última escrita capturada antes de cada contato deixou `$0078=$410B` e `$0078=$1088`, respectivamente, coincidindo com os valores lidos na reação.

Os replays são compatíveis com seus controles neutros nos campos registrados antes do comando. As palavras `$1FEA/$1FEC`, usadas pelo outro gerador documentado em `issd-cpu-offensive-ai-research.md`, tinham os mesmos valores nos dois contatos; isso não demonstra independência geral entre os mecanismos. O laço mostra que `$0078` evolui enquanto o processador aguarda interrupções, mas ainda não sabemos reproduzir no navegador quantas iterações ocorreriam em cada momento, nem demonstramos causalidade com alteração controlada do campo. Portanto, não se deve substituir a decisão original por uma probabilidade inventada ou afirmar que um replay isolado representa a distribuição dos resultados.

Fontes: `CODE_8080D4` no `Routine_Macros_ISSD.asm`, hooks passivos `tools/probe_issd_reaction_global78.lua` e resumo `docs/issd-reaction-global78-observation.json`. A auditoria `tools/audit_issd_reaction_global78.py` verifica a linha de base, o endereço de escrita, a aritmética e a relação com cada reação. O modelo isolado `nativeIdleGlobal78` e os testes em `dist/test-native-slide-reaction-choice.mjs` cobrem soma e carry. As janelas observadas não provam que esse seja o único local capaz de escrever `$0078` em toda a partida.

### Passe para cima: paleta inicial das equipes

O compositor de passe usa as quatro cores iniciais de detalhe por equipe da tabela `$81:E7D8`, carregadas por `$A4:920B → $80:A4EF`, e a cor 10 da tabela `$82:8326`. Quando `$8B:D151` determina uma cor, ela substitui a cor 12; quando o seletor é zero, preserva-se a cor 12 inicial da equipe. Assim, as nove seleções que antes usavam pose de reserva ao passar para cima podem usar o corpo animado também nessa direção. A mesma composição é usada pela partida e pelo laboratório. Os outros índices de detalhe 13–15 também seguem a paleta inicial da equipe.

As paletas são extraídas da ROM local pelo exportador `tools/export_issd_pass_orientations.py`. Para atualizar um recurso de passe já gerado, use `tools/update_issd_pass_team_palettes.py`; ele confere os hashes da ROM e do recurso. Com o recurso local atualizado, foram verificados 23.040 contextos de disponibilidade (36 equipes, dois uniformes, duas peles, oito direções e 20 números); os 16 quadros anteriormente validados da Inglaterra coincidiram byte a byte com as referências RGBA. `node dist/test-native-pass-body.mjs` testa especificamente a preservação da cor inicial, a substituição com seletor não zero e a reserva quando a paleta inicial falta. A extração completa foi repetida com oito direções validadas.

As cores das demais equipes seguem tabelas e inicialização decodificadas da ROM, mas não foram comparadas individualmente a capturas de partida; alterações posteriores de paleta podem mudar o resultado original. A camada de cabelo continua parcial e o passe dos goleiros ainda não está integrado. A integração posterior do passe da CPU está descrita abaixo. O recurso gráfico derivado permanece local e ignorado pelo Git.

### Passe da CPU no protótipo web

Jogadores de linha controlados pela CPU agora podem passar para um companheiro da mesma equipe. O protótipo aguarda 1.800 ms de posse, procura jogadores de linha entre 60 e 150 unidades do ponto atual da bola, descarta corredores com adversários próximos e prefere avanço em direção ao gol. A CPU dos dois lados usa a mesma regra, mas o atleta controlado pelo usuário nunca passa automaticamente. O chute da CPU em posição de finalização e a saída do goleiro têm prioridade; a bola aérea e o bloqueio de reinício impedem o passe. Jogadores caídos são excluídos da decisão.

O comando libera a bola pelo mesmo fluxo e aciona `startActionVisual(..., 'pass', ...)`, compartilhando o compositor de passe e suas reservas visuais com o usuário. Após a correção descrita abaixo, os passes rolam pelo chão com força ajustada à distância. A recepção e interceptação continuam sujeitas às regras provisórias já existentes, e o jogador de destino pode se mover durante o passe.

Esses limiares, a escolha de destinatário e a velocidade da CPU são **heurísticas do protótipo**, não regras recuperadas da ROM. A IA original, o direcionamento preciso, a recepção em movimento e o comportamento de passe dos goleiros permanecem pendentes. `node dist/test-match-flow.mjs` verifica seleção, barreiras, direção e chegada a um companheiro parado com a física provisória; `node dist/test-player-drawing.mjs` e `node dist/test-pass-direction.mjs` cobrem o passe manual e sua apresentação. Isso não substitui a validação de uma partida completa nem confirma equivalência com o ISSD.

### Direção e desaceleração do passe no protótipo

O passe manual antes usava velocidade fixa de 5,8 unidades por quadro, direção limitada aos oito setores e impulso vertical. Como o atrito era aplicado apenas no chão, a bola atravessava uma distância grande antes de desacelerar. Agora o comando procura um companheiro não caído em até 150 unidades, dentro de um cone na direção pressionada ou da orientação atual, e orienta a bola para sua posição. Sem candidato, mantém a direção solicitada e faz um passe livre. A escolha usa a posição no instante do passe; o destinatário pode se mover e adversários podem interceptar.

Passes do usuário e da CPU agora começam no chão. A força dirigida considera a distância, com limite de 3,6 unidades por quadro, e o atrito exclusivo de passe reduz a velocidade em 0,04 por quadro até parar. A física de chute continua com o tratamento anterior. Esses valores e o auxílio de mira são **ajustes provisórios de jogabilidade**, não constantes confirmadas na ROM. `dist/test-pass-model.mjs` testa seleção direcional, passe livre, alcance e perda de força; `dist/test-match-flow.mjs` testa um passe da CPU até um companheiro parado. A escolha do receptor, a recepção em movimento e a calibração contra capturas do original permanecem pendentes.

### Chute, gol e goleiro: primeira integração jogável

O comando de chute do usuário agora usa as direções pressionadas; sem direção horizontal usa o sentido do ataque. O botão de correr junto do chute seleciona uma trajetória mais alta; sem ele, o chute é baixo. O jogo calcula a animação a partir do vetor do chute. As velocidades e alturas em `dist/shot-model.mjs` são valores provisórios de navegador, não extrações comprovadas da ROM. O chute da CPU mantém sua regra anterior.

O goleiro da CPU permanece próximo da própria linha de fundo e acompanha a posição lateral da bola dentro do espaço lógico do gol. A trajetória de um chute adversário é testada contra o goleiro: no modelo provisório, um chute baixo dentro do alcance pode ser retido, e outro mais alto ou forte pode ser desviado, voltando à disputa. Ao desviar, o último toque passa para a equipe do goleiro para permitir a classificação posterior de escanteio. A retenção atual usa o modelo comum de posse e a saída existente do goleiro; **não representa ainda o estado original de bola nas mãos nem a animação específica de defesa**.

O gol lógico permanece nas duas extremidades do campo existente. Para ser contado, a bola inteira deve ultrapassar a linha e caber entre os limites lógicos e abaixo da altura provisória do travessão. Não há ainda colisão física com poste ou travessão: uma bola que não cabe na abertura segue para a classificação de saída. As dimensões da abertura, projeção do estádio, posição visual das traves, área de alcance e lógica de retenção/desvio ainda precisam ser medidas e comparadas com a ROM; os gráficos atuais do estádio não foram reposicionados nesta etapa. `node dist/test-goalkeeper-model.mjs`, `node dist/test-field-events.mjs` e `node dist/test-match-flow.mjs` verificam direção/altura, movimentação limitada, retenção/desvio, limites de gol e escanteio em cenários sintéticos; não validam fidelidade visual nem uma partida completa.

### Projeção das linhas no estádio exportado

No arquivo local `dist/assets/issd/stadium/layout-1.png`, a medição automatizada das linhas brancas encontrou os cantos `(158,190)`, `(2014,190)`, `(801,833)` e `(2657,833)`, em pixels da imagem de 2816×1280. As laterais seguem `x-y=-32` e `x-y=1824`; as linhas horizontais ficam em `y=190` e `y=833`. Essa evidência confirma que o campo mostrado é um paralelogramo inclinado, enquanto a partida desenha os jogadores e testa saídas em coordenadas retangulares. O descompasso explica por que uma mudança apenas em `field.goalH` não alinha os gols lógicos às traves visíveis.

O relatório com hash, contagem de pixels e limitações está em `docs/issd-stadium-projection-observation.json`; pode ser regenerado com `python tools/audit_issd_stadium_projection.py --image dist/assets/issd/stadium/layout-1.png --output docs/issd-stadium-projection-observation.json`. `dist/stadium-pitch-projection.mjs` e `node dist/test-stadium-pitch-projection.mjs` registram uma transformação afim e sua inversa para esse preview. A transformação **ainda não foi ligada à partida**: antes é necessário calibrar controles e direções de sprites na tela, os outros sete layouts, os pontos exatos das traves, a câmera e o sistema de coordenadas do jogo original. A medição da imagem exportada não comprova a transformação Mode 7 nem os limites de colisão da ROM.

#### Outros estádios e conversão dos controles

Uma revisão do detector também identificou as linhas do Japão (layout 0) e da Itália (layout 3), além dos EUA (layout 1). Os cinco demais foram explicitamente registrados como indeterminados; o algoritmo não encontrou bordas de grama suficientemente consistentes com sua hipótese. As coordenadas, hashes e motivos estão em `docs/issd-stadium-projections-observation.json`, regenerável com `python tools/audit_issd_stadium_projections.py --directory dist/assets/issd/stadium --output docs/issd-stadium-projections-observation.json`.

O módulo de projeção agora também converte entre posição do campo lógico e posição do Canvas, levando em conta o recorte do estádio, e calcula a transformação inversa de uma direção de tela para uma direção do campo. Os testes cobrem cantos, ida e volta e entrada vertical que continua vertical na tela para os três layouts. A prévia em `editor/locomotion-lab.html#pitch-projection-lab` desenha as linhas medidas sobre as imagens; ela não altera a partida. Os pontos laterais mostrados são centros geométricos do campo, não traves capturadas. Ainda faltam calibrar os outros estádios, a posição das traves e confrontar controles e ângulos dos sprites com a partida original antes da integração.

#### Medição por linhas e limitações dos previews

O auditor também procura trios simétricos de linhas diagonais e linhas horizontais cercadas por verde, sem exigir que a grama termine junto às laterais. Esse método mediu os layouts 4, 5, 6 e 7; junto dos três anteriores, há sete projeções disponíveis e visualizáveis no laboratório. `dist/test-stadium-pitch-projection.mjs` confere os cantos e a inversa em todos eles; `dist/editor/test-stadium-projection-lab.mjs` verifica a troca de estádio no painel.

Na etapa acima, o layout 2 ficou indeterminado porque sua imagem local tem perspectiva e estilo diferentes e não satisfez o detector de linhas paralelas a 45 graus; a medição posterior está descrita abaixo. O desenho do layout 6 apresenta regiões e elementos que precisam de inspeção visual adicional; detectar as linhas não valida a integridade dos demais gráficos. Nenhuma dessas medições confirma dimensões nativas da ROM, posições das traves ou a câmera Mode 7, e as projeções ainda não estão ligadas à partida. Relatório reproduzível: `docs/issd-stadium-projections-observation.json`; implementação auxiliar: `tools/audit_issd_stadium_line_votes.py`.

#### Preview com perspectiva e recorte corrigido

O arquivo atual `layout-2.png` mede 2816×1280 e tem limites RGB não pretos `(49,61)–(2816,953)`. O manifesto preservava medidas de uma imagem anterior, 3072×1280, e indicava um recorte que excedia a largura atual. O manifesto foi regenerado a partir dos arquivos presentes, resultando em recorte `(49,61,2767,892)`; `python tools/test_issd_stadium_manifest.py` verifica dimensões e recortes dos oito arquivos. A descrição do manifesto agora diz que a origem dos assets pode variar: a imagem atual não deve ser apresentada como gráfico original da ROM sem comprovação.

Um detector separado ajusta retas às duas laterais e mede as linhas horizontais no preview de perspectiva. Ele estimou os cantos `(233.628,207.5)`, `(1968.567,207.5)`, `(829.392,837)` e `(2667.131,837)`, com 1.765 e 1.730 amostras nas retas. A transformação e sua inversa usam uma homografia para este layout; a conversão de direção no Canvas aceita um ponto de referência, necessário porque a escala varia com a posição. As oito imagens atuais aparecem no laboratório, mas o layout 2 representa estimativas dessa imagem, não dados da ROM. Os testes conferem cantos e ida e volta para os oito layouts, inclusive a direção em um ponto projetado. O relatório completo é produzido por `tools/audit_issd_stadium_projections.py`; o detector é `tools/audit_issd_stadium_perspective.py`. A projeção, traves e câmera permanecem fora da partida até validação em gameplay.

#### Opção experimental na partida

Na configuração anterior à partida, **Alinhamento do campo → Projeção experimental** ativa a projeção medida dos previews internos. O padrão continua **Atual**. O novo adaptador `dist/pitch-view.mjs` projeta a posição de jogador, bola, sombra, indicador e alvo da câmera sem deformar os sprites; a direção do teclado é convertida de volta ao campo lógico, e as animações de movimento, passe e chute seguem a direção projetada na tela. A posse mantém separadamente a orientação no campo usada para posicionar a bola junto aos pés. Regras e colisões continuam em coordenadas lógicas.

Se a imagem não estiver disponível ou o estádio tiver ID personalizado, o adaptador conserva a apresentação anterior. As oito projeções se referem aos arquivos medidos: uma imagem alterada depois da medição pode invalidá-las mesmo tendo as mesmas dimensões. A abertura lógica do gol, a correspondência exata com as traves, a dinâmica Mode 7 e a escala dos sprites não foram validadas com a ROM nem corrigidas nesta etapa. A opção existe para experimentar a integração e não deve ser confundida com fidelidade comprovada. `node dist/test-pitch-view.mjs`, `node dist/test-projection-game-integration.mjs`, `node dist/test-player-drawing.mjs` e `node dist/test-stadium-pitch-projection.mjs` cobrem conversões, direções, desenho e reserva; ainda é necessário verificar a aparência e a jogabilidade em navegador com imagens reais.


#### Posição inicial da bola

O reinício do protótipo posiciona a bola no centro lógico do campo e coloca o jogador controlado de forma que seu ponto de contato coincida com esse centro. Isso vale tanto para o início quanto para o reinício atualmente usado após gol. A escolha da equipe que dá saída, a formação e a sequência original de saída permanecem pendentes de validação; o protótipo ainda utiliza a equipe humana nesse reinício. O teste `dist/test-match-flow.mjs` verifica o centro em diferentes dimensões de campo e a manutenção do contato com o cobrador.


#### Seleção do goleiro na escalação web

A escalação de partida e sua conferência agora usam o mesmo seletor: o primeiro jogador cadastrado como goleiro ocupa o primeiro slot e os dez slots restantes recebem jogadores de linha, incluindo reservas quando necessário. Se não existir goleiro cadastrado, é criado um goleiro temporário para a partida; se faltarem jogadores de linha, são preenchidos com reservas temporários. Isso evita que goleiros adicionais cadastrados em equipes editadas atuem como jogadores de linha. Os 36 elencos originais existentes preservam seus primeiros 11 jogadores na ordem original. Essa é uma regra do protótipo, não uma conclusão sobre seleção automática na ROM.


#### Busca por mergulho do goleiro

A defesa web continua provisória: o goleiro acompanha a bola e o contato produz retenção ou desvio, mas não aciona uma animação de mergulho. A pose `$E7C7` disponível é apenas um quadro capturado; não demonstra um ciclo de defesa e não foi usada como substituta do salto. O observador `tools/capture_issd_goalkeeper_transfers.lua` agora aceita `ISSD_KEEPER_GRAPHICS_FAMILY=dive` para capturar os scripts observados com gráficos nomeados de mergulho: `$E924`, `$E94B`, `$E996`, `$E9CD` e `$EA18`.

Uma partida automática isolada registrou 18.820 amostras de goleiro, sem ocorrência desses cinco scripts e sem capturas gráficas de mergulho. O relatório é `docs/issd-goalkeeper-dive-capture-search.json`. É apenas uma tentativa: não demonstra que os scripts não ocorrem. Falta obter uma situação de chute ao gol que os acione, correlacionar OAM/VRAM e tela por quadro e, então, implementar a reação visual com temporização e física separadamente identificadas.


#### Primeira reação visual de mergulho — replay sintético

Um estado salvo foi carregado em instância isolada e a posição do goleiro e a trajetória da bola foram ajustadas na memória do emulador para provocar a reação, sem alterar a ROM ou sobrescrever o estado salvo. O roteiro nativo percorreu `$E924/$CB42`, `$E94B/$CB4C` e `$E996/$CB56`. Para as três poses, o exportador `tools/export_issd_keeper_dive.py` conferiu ponteiro de pose da ROM, atribuição de peças à OAM, OAM da PPU, tiles da ROM contra VRAM e pixels da captura: 351, 283 e 331 pixels, respectivamente, todos coincidentes. A geometria dos pedaços foi observada na WRAM desse replay, não inferida de uma grade. Evidência em `docs/issd-keeper-dive-evidence.json`.

Os descritores permaneceram ativos 2, 7 e 28 quadros nesse caso, mas no primeiro quadro o ponteiro da pose ainda era antigo. A prévia usa somente o quadro inicial verificado e as duas poses posteriores, com duração 1/7/28; isso não prova a temporização geral do jogo. A orientação capturada está disponível na partida e no laboratório `#goalkeeper-lab`. A partida antecipa visualmente o mergulho em até dez quadros para chutes que alcançariam o goleiro na orientação de tela 6; esse disparo é heurístico, assim como a detecção de defesa já existente. Outras orientações conservam a apresentação anterior. A paleta por equipe é adaptada a partir da prévia do goleiro e não foi comparada visualmente para todas as equipes. A reação visual não altera altura nem deslocamento físico do goleiro e não comprova o comportamento original da IA, captura, rebote ou escanteio.

Para regenerar os dados locais, preservando a ROM fora da distribuição:

```powershell
python tools/export_issd_keeper_dive_directions.py --root analysis --rom 'International Superstar Soccer Deluxe/International Superstar Soccer Deluxe (USA).sfc' --output dist/assets/issd/native-keeper-dive-local.json --report docs/issd-keeper-dive-directions.json
```

Sem os dados locais o jogo preserva a animação anterior. Os scripts `tools/probe_issd_keeper_synthetic_shots.lua` e `tools/replay_issd_keeper_synthetic_shot.lua` são exclusivamente de experimentação e escrevem apenas na memória do emulador isolado.

O teste `tools/test_issd_keeper_dive_pixels.py` também compara a saída real do compositor JavaScript com a OAM e a paleta capturadas: os três quadros conferem, com tolerância de um nível RGB. Isso não valida a substituição de paleta nas demais equipes. Uma busca simétrica no segundo goleiro, com 36 trajetórias sintéticas, não ativou os scripts de mergulho procurados; aquela busca não validou a reação do segundo goleiro.


#### Orientação oposta do mergulho — captura com direção forçada

A ROM também contém as tabelas `$82:E9A6` e `$82:E9F1`; o observador inicial de mergulho não as incluía. Elas foram adicionadas ao conjunto de busca, junto com `$E96F`. Em replay isolado, a direção interna 4 e o bit de orientação do goleiro foram ajustados em memória antes da seleção de quadros. O motor original então produziu `$CB5B/$CB65/$CB6F`. A geometria observada, OAM, tiles e captura foram conferidos pelo exportador, com 352, 292 e 365 pixels candidatos coincidentes. O compositor JavaScript também foi comparado com a OAM da PPU para as três poses.

As duas orientações estão disponíveis no laboratório e na partida para chutes horizontais para esquerda ou direita na tela. A direção 4 foi forçada no teste: não demonstra que o goleiro adversário naturalmente selecionaria essa sequência na mesma situação. A associação à direção de tela, a antecipação do chute, duração de retenção e paletas de outras equipes continuam provisórias; a animação não move o goleiro fisicamente. Chutes diagonais ainda não têm reação visual de mergulho validada. Evidências: `docs/issd-keeper-dive-directions.json`.


#### Duas orientações diagonais de mergulho

Dois replays isolados com direção interna forçada 3 e 7 produziram, respectivamente, `$CBBF/$CBC9/$CBD3` e `$CB10/$CB1A/$CB24`. Para cada sequência, o exportador verificou ponteiros da ROM, OAM e VRAM, e a comparação com a captura confirmou todos os pixels candidatos: 1.189 na primeira e 1.219 na segunda. A saída do compositor JavaScript também coincidiu com a PPU. A direção e o bit de orientação foram ajustados em memória; os scripts e os quadros foram executados pela ROM, sem alteração da ROM ou estado salvo. Em uma captura natural anterior, ambas as direções foram observadas com o mesmo bit de orientação, mas isso não estabelece todos os contextos em que devem ser usadas.

As duas sequências estão no laboratório e são usadas experimentalmente para chutes nas diagonais cima-direita e baixo-esquerda. A associação entre direção de tela e sequência ainda é provisória. A classificação visual da reação usa razão de eixos 2 para reconhecer o vetor diagonal produzido pelo modelo atual de chute, cuja componente vertical é reduzida; essa razão não foi extraída da ROM. A previsão da defesa e a física continuam provisórias, e as diagonais cima-esquerda e baixo-direita ainda não contam com reação visual validada. Relatório: `docs/issd-keeper-dive-directions.json`.


#### Demais diagonais e tile preservado

Replays sintéticos adicionais forçaram as direções internas 1 e 5; seus bits de orientação foram escolhidos conforme amostras naturais dessas direções, embora não necessariamente do mesmo evento de mergulho. Para a direção 1, `$CB74/$CB7E/$CB88` passaram nas verificações de ROM, OAM, VRAM e imagem; os 1.040 pixels candidatos coincidiram. Para a direção 5, `$CBF1/$CBFB/$CC05` produziram 1.061 pixels candidatos coincidentes.

No quadro `$CBFB`, o tile 20 na VRAM não corresponde ao tile 20 decodificado do descritor atual; seus 32 bytes coincidem exatamente com o tile 20 do descritor anterior `$CBF1`, também extraído da ROM. O exportador só usa essa correspondência quando existe a pose anterior e a igualdade com a VRAM é exata; qualquer outro desencontro é rejeitado. Isso reproduz a imagem observada, mas a causa da permanência do tile na VRAM ainda não foi identificada. A saída do compositor JavaScript foi comparada com a PPU em ambas as direções.

As quatro diagonais e as duas direções horizontais agora têm reação visual experimental em partida e prévia no laboratório. A associação entre entrada de tela e pose, os disparos e a física permanecem provisórios. Orientações verticais de tela 0 e 4 ainda não foram adicionadas, e a força ou o alcance da defesa não foram calibrados a partir dessas capturas. Evidência: `docs/issd-keeper-dive-directions.json`.


#### Orientações verticais do mergulho

Dois replays sintéticos com direções internas forçadas 2 e 6 e bit de espelhamento desativado, como observado nessas direções no trace natural, produziram `$CBA6/$CBB0/$CBBA` e `$CB29/$CB33/$CB3D`. Passaram nas verificações de ponteiros da ROM, OAM, VRAM, captura e compositor JavaScript: 1.077 e 1.141 pixels candidatos, respectivamente, sem divergências. As oito orientações estão disponíveis no laboratório e no compositor experimental da partida.

A associação das direções nativas às da tela continua uma hipótese de integração, pois os replays de coleta forçaram a orientação. A previsão do goleiro e a física da defesa continuam heurísticas. No controle web de chute, pressionar somente cima ou baixo ainda introduz um componente horizontal na direção de ataque: assim, a presença das poses verticais não comprova que esse comando irá selecioná-las. Não foi feita alteração nessa mecânica de chute sem evidência adicional. Relatório: `docs/issd-keeper-dive-directions.json`.


#### Orientação do chute sem direcional

O auditor `tools/audit_issd_shot_facing.py` compara oito replays locais: em cada um, o ator `$1900` estava vinculado a `$00A6`, o segundo controle acionou X sem direcional, o ator entrou em `$D007` e houve liberação subsequente da bola. A direção interna observada acompanhou a orientação capturada em cada caso. Por exemplo, na orientação visual registrada como cima, a direção nativa era 6 e os words de velocidade observados na liberação foram `(-4,-4,-7)`; para direita, direção nativa 0 e `(7,0,-7)`. Os eixos e valores são nativos e não equivalem diretamente às velocidades de tela. Um replay por orientação e um estado salvo não provam todos os contextos de comando. Evidência e hashes: `docs/issd-shot-facing-replays.json`.

Na web, quando existe entrada direcional, `planShot` usa seus componentes em vez de adicionar automaticamente o sentido de ataque ao apertar só cima ou baixo. Sem entrada, usa a última orientação visual do jogador; o sentido de ataque é reserva apenas quando essa orientação não está disponível. A escolha visual do chute também usa a mesma classificação de setores usada pela reação experimental do goleiro. Os valores de força, peso do eixo vertical, altura e gravidade continuam provisórios, assim como a conversão de coordenadas e os efeitos de pressionar direcional durante o chute no original. Testes verificam oito orientações, comandos verticais e projeção nos oito layouts.


#### Ordem vertical do chute em voo

Um replay isolado com comando X produziu bola tipo 3. O observador de `$83:941F/$83:942E/$83:882A/$83:8863/$83:8865` foi comparado com um replay anterior da mesma entrada: 325 amostras de campos registrados coincidiram. Na janela próxima à liberação, 61 atualizações aéreas verificadas somaram primeiro `$0458` à velocidade vertical 16.16 e depois somaram a nova velocidade à altura. O word de aceleração observado foi 7168 (`$1C00`), em unidades nativas. O auditor verifica também os opcodes da ROM e rejeita resultados divergentes; evidência e hashes em `docs/issd-shot-airborne-audit.json`. É uma trajetória, um ator, uma condição de campo e uma direção; a verificação cobre somente o voo de tipo 3, não o solo ou o quique.

A versão web agora usa essa ordem ao atualizar a altura de uma bola livre identificada pelo protótipo como chute; outros modos preservam a ordem anterior. A aceleração, velocidade inicial, escala entre unidades, contato com jogadores e solo e restituição do quique continuam provisórios, portanto a ordem comum não torna a trajetória fiel por completo. O teste da partida verifica o primeiro passo aéreo e que o modo de passe preservou seu comportamento. Reproduzir auditoria: `python tools/audit_issd_shot_airborne.py --root analysis/shot-airborne-vertical --baseline analysis/shot-body-replay --rom 'International Superstar Soccer Deluxe/International Superstar Soccer Deluxe (USA).sfc' --output docs/issd-shot-airborne-audit.json`.


#### Dois caminhos de quique após chute

Em replays instrumentados do comando X, uma trajetória diagonal manteve bola livre de tipo 3 nas 64 amostras registradas antes do primeiro impacto. No quadro 4407, com clima 1 e flags 0, `$83:895D` reduziu a velocidade vertical 16.16 à metade, `$83:8883` inverteu seu sinal e `$83:89AF` reduziu as componentes horizontais positivas para a soma de metade e quarto. O parâmetro observado passou de 11 para 7. Os campos registrados coincidiram com um replay anterior da mesma entrada; os dados intermediários não registrados não são comprovados. Evidência: `docs/issd-shot-bounce-audit.json`.

Em outro replay, de chute para a esquerda, a bola foi liberada como tipo 5 e atingiu o solo no quadro 4354. Nesse caso, `$83:8962` aplicou a soma de metade, quarto e oitavo à velocidade vertical; `$83:89CE` e seus auxiliares reduziram as componentes horizontais negativas pela mesma proporção. O parâmetro observado passou de 5 para 3. Evidência: `docs/issd-shot-type5-bounce-audit.json`. As duas auditorias verificam opcodes da ROM, estado dos registros de entrada, contexto e resultado. `tools/audit_issd_shot_bounce.py` reproduz ambas usando `--type 3` ou `--type 5` e os replays locais correspondentes.

`observedType3ShotBounce` e `observedType5ShotBounce` em `dist/native-ball-fixed.mjs` reproduzem apenas os valores exatos capturados, rejeitando outros casos. As duas observações não estabelecem como o navegador deve selecionar o tipo nativo, nem a conversão de velocidade, os limiares ou o comportamento em outros climas e impactos. Por isso, nenhuma delas substitui ainda o quique provisório da partida. Teste: `node dist/test-native-ball-fixed.mjs`.

### Alinhamento do campo e dos goleiros no navegador

O estádio USA apresenta linhas inclinadas no arquivo de imagem, enquanto as coordenadas da simulação permanecem retangulares. Antes, a projeção visual medida era opcional e estava desativada no online: o goleiro podia defender o gol lógico distante da trave desenhada. A apresentação medida de `dist/stadium-pitch-projection.mjs` agora é o padrão para imagens originais dos oito layouts, inclusive no online; a opção retangular anterior permanece disponível no jogo local. Imagens personalizadas ou não carregadas mantêm a apresentação de reserva. A física, os limites e as posições de repouso do goleiro não foram alterados. O jogador e a bola do lateral também usam a posição projetada, preservando sua montagem capturada.

Para o layout USA, o teste `node --test dist/test-goalkeeper-stadium-alignment.mjs` verifica que ambos os goleiros, com a bola no centro, aparecem à frente das linhas laterais medidas e na altura central do campo desenhado. `node dist/test-pitch-view.mjs`, `node dist/test-projection-game-integration.mjs`, `node dist/test-goalkeeper-model.mjs`, `node dist/test-field-events.mjs` e os testes de partida/lateral em dois navegadores verificam conversões e regressões. A medição usa linhas da imagem exportada: os pontos exatos dos postes, a altura da trave, colisões e a câmera Mode 7 ainda não estão validados contra a ROM; o alinhamento é uma correção visual, não prova de fidelidade física.

### Auditoria de geometria do gol — comparação com a ROM USA

`node tools/audit_issd_goal_geometry.mjs` lê a ROM local e confere os 16 words de dimensões em `81:EC47` e os 32 limiares em `81:A833/A843/A853/A863`. Os resultados dos oito índices e das fronteiras imediatas estão em [issd-goal-geometry-audit.json](issd-goal-geometry-audit.json). A ROM não é copiada nem distribuída. Na rotina `83:8BAB..8BC8`, a região central tem largura 96 unidades nativas, com outras duas faixas de 8 unidades. A entrada central leva a verificações adicionais em `83:8D76..8DA0`; não é suficiente para declarar gol nem identifica isoladamente os postes.

Para o estádio de índice 1, H nativa é 640 e a altura lógica do campo web é 523. **Sob a hipótese ainda não validada de escala linear compartilhada**, a faixa central corresponderia a 78,45 unidades web; a largura de abertura `field.goalH` usada pelo navegador é 168, aproximadamente 2,14 vezes esse valor. A comparação revela uma divergência que merece investigação, não estabelece que a faixa central seja a abertura da trave nem autoriza substituí-la. A imagem de estádio local mostra a rede direita incompleta, portanto não é referência suficiente para localizar ambos os postes com precisão.

Verificações executadas: `node tools/audit_issd_goal_geometry.mjs`, `node dist/test-native-goal-bands.mjs`, `node dist/test-field-events.mjs` e `node --test dist/test-goalkeeper-stadium-alignment.mjs`. Os dois últimos verificam coerência do protótipo, não comportamento nativo. Para validar a jogada completa faltam capturas isoladas em torno das duas bordas e do travessão, estados e trajetórias antes/depois de `83:8BC8`, correlação com `83:8D76..8DA0` e o resultado visual/placar. A altura, o rebote e a colisão física dos postes permanecem pendentes; a física do navegador não foi alterada nesta auditoria.

### Sondagem dinâmica isolada das faixas do gol

`tools/probe_issd_goal_boundaries.lua` restaura o mesmo estado de partida a cada cenário e prepara uma bola sintética na RAM do emulador isolado, sem modificar a ROM nem o estado salvo. A entrada usa a inversa de `80:D31A`: `$0C=$2C-$009A` e `$08=$2A+$2C-$0098`; velocidade, gravidade e intervenções do jogo podem alterar a bola antes da comparação. Foram executados 72 cenários (duas extremidades, nove offsets e quatro alturas iniciais), 24 quadros cada, no estádio nativo de índice 1. O traço local `analysis/goal-boundary-probe/trace3.jsonl` não integra a distribuição.

`python tools/audit_issd_goal_boundary_probe.py analysis/goal-boundary-probe/trace3.jsonl docs/issd-goal-boundary-probe.json` verificou 1.728 quadros e 675 entradas em `83:8BAB`. Os valores efetivos de `$2C,x` no momento do callback levaram exatamente ao caminho previsto em todos os casos: 320 entradas para `83:8DDC` (fora), 16 para `83:8BC8` (bordas) e 339 para `83:8D76` (centro). O registrador X era `$0400` e os limites externos eram 264 e 376. Foram observados acessos a `86:D98C` em nove cenários de cada lado, mas a entrada nessa rotina por si só não prova gol. Relatório: [issd-goal-boundary-probe.json](issd-goal-boundary-probe.json).

O primeiro experimento colocou coordenadas de tela diretamente nos campos `$08/$0C`: isso não posicionou `$2A/$2C` nas faixas desejadas; ele foi descartado e corrigido com a transformação acima. A auditoria considera os valores efetivos capturados, pois os offsets iniciais mudam durante a simulação. As capturas são sintéticas e não registram placar, pixels da trave nem o resultado posterior completo. Portanto, não validam postes, travessão, rede, colisão ou gol por si só. A assimetria de cobertura (17 cenários com entrada na rotina de faixa à esquerda e 33 à direita) também impede inferir equivalência entre os dois lados. Próximo passo: preservar velocidade e posição por quadro perto da linha e correlacionar caminhos completos, placar e imagem, incluindo situações de borda e altura, antes de alterar a física web.

### Correlação entre rotina de gol e placar em sondagem isolada

A sondagem foi repetida com `ISSD_GOAL_FOCUSED=1`, `ISSD_GOAL_FRAMES=120` e `ISSD_GOAL_SCREENSHOT_DIR` apontando para uma pasta local. Foram 20 cenários sintéticos, cinco offsets (`-49`, `-48`, `0`, `47`, `48`), duas alturas iniciais (`0`, `-56`) e os dois lados, com 120 quadros cada. Além dos hooks, cada amostra registra `$042A/$042C`, `$0410`, os placares `$0DA2/$0EA2` identificados em `RAM_Map_ISSD.asm` e `$14D6`. `python tools/audit_issd_goal_outcomes.py analysis/goal-outcome-probe/trace.jsonl analysis/goal-outcome-probe docs/issd-goal-outcome-probe.json` confere a integridade, os deltas de placar e a ocorrência anterior da rotina para cada caso.

Em 12 cenários, o placar mudou de `0–0` para `0–1` na esquerda ou `1–0` na direita, e `86:D98C` foi observada no mesmo quadro amostrado. Nos cenários centrais com altura inicial zero, o callback ocorreu com `$2C=319`, altura zero, e `$2A=-7` à esquerda ou `$2A=1860` (`W+4`) à direita. Isso é compatível com os limites do helper `83:8D61`, mas os callbacks não estabelecem sozinhos toda a ordem de escrita do placar. Em cenários iniciados a `-56`, a altura efetiva no callback era `-55`; os valores de entrada não devem ser confundidos com os do evento.

As imagens locais `goal-05-040.png` e `goal-15-040.png` exibem, respectivamente, as mensagens “GOAL” e “OWN GOAL”; seus hashes estão no relatório, enquanto as imagens e a ROM permanecem locais. O placar gráfico pode ser atualizado em momento diferente da amostra dos words internos. Estes casos foram injetados na RAM de um único estado, portanto demonstram correlação para essas condições, não todas as regras. Os oito casos sem mudança de placar não provam colisão com a trave: alguns sequer atingiram o caminho desejado. Ainda falta medir e validar impactos físicos dos postes e do travessão, geometria e simulações naturais antes de substituir a física do navegador.

### Resposta de velocidade na região lateral do gol

O observador `tools/probe_issd_goal_boundaries.lua` aceita `ISSD_GOAL_EDGE=1` e `ISSD_GOAL_FRAMES=32`. Com o mesmo estado de partida isolado, foram executados 96 cenários sintéticos: dois lados, oito offsets iniciais e seis alturas iniciais. A captura acrescenta hooks em `83:8BF8`, `83:8C3B`, `83:9073`, `83:90CB` e `83:A90E`, com os dois words de cada componente de velocidade e a direção. O traço local não acompanha a distribuição.

A auditoria `python tools/audit_issd_goal_edge_velocity.py analysis/goal-edge-probe/trace.jsonl docs/issd-goal-edge-velocity.json` verificou 3.072 quadros, 30 entradas em `83:8BF8` e 30 pares em cada um dos dois trechos de velocidade. Nas 30 ocorrências observadas, na extremidade direita, o word combinado `$0428:$0426` passou de `-373` para `+93` (valor inteiro com fração de 16 bits): inversão e divisão por quatro com truncamento, compatíveis com `83:9073..839089` para a direção observada. O componente `$0424:$0422` permaneceu em `-129953` nas 30 amostras, conforme a guarda de `83:90CB` para o word alto `-2`. Os pares são leituras anteriores às instruções dos hooks no mesmo quadro; a comparação encontra os próximos hooks consecutivos. `python tools/test_issd_goal_edge_velocity.py` verifica limites e arredondamento da tradução isolada, inclusive ramos não exercidos pela captura.

A amostra dinâmica repetiu somente uma combinação efetiva de velocidade/direção, não observou `83:8D23` e não prova que a resposta seja contato com um poste. O desenho da trave, o som e os estados posteriores precisam ser correlacionados; tampouco há evidência suficiente para copiar esses valores diretamente para a física web. Ver [issd-goal-edge-velocity.json](issd-goal-edge-velocity.json).

**Observação do usuário:** durante a investigação, o usuário relatou ter ouvido o som característico de bola atingindo a trave ou o travessão. Isso fornece uma indicação adicional de contato com a estrutura em alguma execução; não foi informado o identificador do cenário, quadro ou lado, e não há gravação de áudio correlacionada ao traço. Portanto, ainda não é possível associar o som especificamente aos 30 pares de velocidade acima nem distinguir poste de travessão. A próxima captura deve registrar áudio, quadro, parâmetros e callbacks juntos, preservando essa observação para confronto.

### Correlação preliminar com a fila de áudio

A sonda de borda foi repetida com hooks adicionais em `83:A000`, `A4:9AF2` e `80:BF05`, registrando o acumulador antes da execução. No disassembly, `80:BF05` coloca o byte em uma fila em `$7E:E680`; `80:BE95` retira dados dessa fila e escreve na porta zero da APU. A fila registra comandos, não uma gravação do som emitido. Já `83:A000` encaminha a `A4:9AF2`, que escolhe dados por tabela e prepara outro efeito: não foi demonstrado que seja áudio e seu argumento não deve ser chamado de código de som.

Nos 96 casos sintéticos (3.072 quadros), foram observados 30 eventos `83:8BF8` e 12 eventos `86:D98C`. Nos quadros destes 12 últimos, a fila recebeu os bytes `$09` e `$4C` 12 vezes cada, coerente com as duas chamadas no caminho `83:8DA0` antes de `86:D98C`. Não foi registrado `80:BF05` no quadro dos 30 eventos de borda nem nos quatro quadros seguintes. A chamada `83:A000` ocorreu seis vezes com argumento `$09`, em casos posteriores ao gol, sem vínculo comprovado com a batida na trave. Auditoria reproduzível: `python tools/audit_issd_goal_audio_queue.py analysis/goal-audio-probe/trace.jsonl docs/issd-goal-audio-queue-probe.json`; a ROM, o estado e o traço ficam locais.

Isso não contradiz o som relatado pelo usuário: as situações observadas são sintéticas, o enquadramento dos eventos de borda ficou fora da tela e algumas chamadas possuem guardas relativas à posição. Tampouco exclui áudio fora da janela de quatro quadros ou um caminho diferente. A próxima captura deve levar a câmera até o impacto, acompanhar a fila e o resultado da APU em uma janela maior e gravar áudio junto da imagem; até lá, não há identificação comprovada do som de poste/travessão.

### Tentativa de enquadramento da borda direita

Uma nova sonda isolada restaura o estado para cada uma de quatro combinações e mantém uma bola sintética a 180 unidades nativas da linha direita por 150 quadros antes de cada lançamento. O objetivo era deixar a câmera acompanhar a jogada. O resultado não alcançou esse objetivo: a imagem local `analysis/goal-visible-probe/goal-02-004.png` mostra outra região do campo; os 107 callbacks `83:8BF8`, em três cenários, tinham `$0408` entre 1595 e 1778. Não há indicação de que esses callbacks sejam impactos independentes: a rotina pode ser chamada repetidamente enquanto a bola permanece na região.

A captura registra 160 quadros após os pré-aquecimentos e nenhuma chamada observada a `80:BF05` no mesmo quadro ou nos quatro seguintes aos callbacks de borda. As condições são as desta tentativa e não excluem o som de trave relatado pelo usuário. As imagens, o estado, a ROM e o traço são mantidos locais. Reproduzir a auditoria: `python tools/audit_issd_goal_camera_attempt.py analysis/goal-visible-probe/trace.jsonl analysis/goal-visible-probe/goal-02-004.png docs/issd-goal-camera-attempt.json`. A opção `ISSD_GOAL_CAMERA_WARMUP=1` no script de sondagem reproduz a tentativa, mas não garante alinhamento da câmera. Relatório: [issd-goal-camera-attempt.json](issd-goal-camera-attempt.json).

Para concluir a correlação com áudio e imagem é necessário identificar os alvos reais da câmera e obter um estado em que a bola e a trave estejam visíveis, preservando os parâmetros e os comandos da APU. Não se deve interpretar as repetições como confirmação de colisões ou alterar a física web a partir delas.

### Investigação do enquadramento e da posição da bola

`tools/probe_issd_camera_writes.lua` observa em um emulador isolado as escritas em `$0098/$009A`, `$13A0/$13B0` e `$0408/$040C`. A captura local `analysis/camera-target-probe/trace-inject.jsonl` tem 90 quadros de linha de base e 90 de tentativa de reposicionamento. Os três primeiros quadros da segunda fase registram uma leitura imediatamente após a escrita sintética: a inversa de `80:D31A` realmente colocou a bola nas coordenadas nativas solicitadas `(1676,320)` naquele instante. Nas amostras ao final desses quadros, `$042A` voltou a valores próximos de `122`, e o objetivo não foi preservado.

Nos 180 quadros observados, `$13A0 - $0098 = 176` e `$13B0 - $009A = 208`, em aritmética de 16 bits. Isso é uma relação observada no estado e não demonstra que os dois primeiros words sejam, isoladamente, os alvos da câmera. Os callbacks registraram PCs retornados `83:CFC4` e `83:CFCB` nas escritas em `$0098/$009A`; o trecho `83:CFBD..CFE5` subtrai os deslocamentos globais e os aplica à bola e aos atores. Os PCs registrados pelos callbacks para `$0408/$040C` incluem `83:8A08/83:8A18` e `83:CFE1/83:CFD7`, em ambas as fases. Os callbacks capturam somente os endereços registrados, e sua temporização não identifica por si só todos os escritores; não é possível atribuir ainda a restauração da bola a uma instrução específica.

Reprodução: `python tools/audit_issd_camera_writes.py analysis/camera-target-probe/trace-inject.jsonl docs/issd-camera-target-observation.json`. A ferramenta valida as três escritas imediatas, as 180 amostras e relata os PCs, sem distribuir estado ou ROM. A próxima investigação deve identificar o estado de posse e os pontos do ciclo que precedem a integração da bola; uma captura com a bola efetivamente livre e a câmera na extremidade é necessária para correlacionar imagem e som do contato. Relatório: [issd-camera-target-observation.json](issd-camera-target-observation.json).

### Delimitação da mudança após a escrita sintética

Uma segunda observação do mesmo estado incluiu hooks de entrada em `83:89E3`, `83:89FB`, `83:8A65`, `83:8D08`, `83:CFBD`, `83:CFCB` e `80:D31A`, além das escritas no System Bus nos bytes vizinhos de `$0408/$040C` e seus aliases `$7E:xxxx`. Nos três primeiros quadros de injeção, a leitura imediata de `$0408` foi 1641, 1640 e 1639; na entrada seguinte observada em `83:89E3`, era respectivamente 101, 100 e 99. Em cada um desses três pares, o valor coincidia com o snapshot `$19E0`, mas não houve callback de escrita nos endereços monitorados entre os dois registros. A igualdade com o snapshot é correlação, não prova de que uma rotina o tenha restaurado.

A auditoria `python tools/audit_issd_ball_injection_order.py analysis/camera-target-probe/trace-cpu.jsonl docs/issd-ball-injection-order-observation.json` confirma os três pares e os 180 quadros. Os callbacks são limitados ao System Bus, aos endereços selecionados e à temporização do BizHawk; acesso por outro alias, cópia interna do core e limites da instrumentação permanecem hipóteses. É incorreto concluir que `83:8A65` foi responsável apenas pela semelhança com `$19E0`. A próxima verificação deve comparar a mesma injeção logo após carregar o estado e após um quadro, usando observadores de entrada de quadro e de memória do core, antes de alterar novamente a câmera. Relatório: [issd-ball-injection-order-observation.json](issd-ball-injection-order-observation.json).

### Momento da injeção e reposicionamento observado

`tools/probe_issd_injection_timing.lua` comparou quatro replays isolados do mesmo estado: injeção antes do avanço ou no callback de início de quadro, cada uma logo após carregar o estado ou após dois quadros normais. Nos dois casos imediatamente após carregar, `$0408` ainda tinha o valor injetado em `83:89E3`, e `$042A` terminou o quadro em `1676`. Nos dois casos após dois quadros, a entrada em `83:89E3` já mostrava a posição anterior, embora a injeção também tivesse sido lida corretamente no instante da escrita. O callback de início de quadro não resolveu a diferença.

Antes da injeção, o estado imediato apresentava `$00A6=0` e `$0430=3`; após dois quadros, apresentava `$00A6=$0500` e `$0430=14`. A presença do goleiro como portador e a mudança do tipo da bola são correlações relevantes, mas ainda não foram isoladas causalmente. Hooks em `80:D31A` ocorreram nos casos imediatos e não nos tardios no primeiro quadro observado. A instrução que substitui a posição nos casos tardios ainda não foi identificada.

Uma terceira fase de `tools/probe_issd_camera_writes.lua`, ativada por `ISSD_CAMERA_FRESH=1`, restaura o estado e começa a injeção imediatamente. Das 90 amostras finais de quadro, 80 apresentaram `$042A=1676`; apesar disso, a imagem local `fresh-3.png` não mostra a trave direita. Logo, manter a bola distante nesse ensaio não demonstrou que a câmera a acompanha. A imagem e o estado continuam locais.

`python tools/audit_issd_injection_timing.py analysis/ball-timing-probe/trace-fields.jsonl analysis/camera-target-probe/trace-fresh.jsonl analysis/camera-target-probe/fresh-3.png docs/issd-injection-timing-observation.json` valida os quatro casos, os quadros e as leituras; também foi executada a compilação sintática do auditor. Os resultados ainda não estabelecem o alvo da câmera nem permitem identificar o som de trave. Próximo passo: isolar o efeito da posse e rastrear a seleção da câmera sem supor que seja a bola. Relatório: [issd-injection-timing-observation.json](issd-injection-timing-observation.json).

### Alvo da câmera e resposta de borda em cena enquadrada

A rotina `8B:81BA..825A` consulta condições de fase, `$00A4/$00A6` e outros estados; no caminho observado, usa o ator indicado por `$00A6` quando presente e, no caminho alternativo aplicável, `$0400` para a bola. `tools/probe_issd_camera_target.lua` observou a entrada em `8B:825A` em dois replays do mesmo estado: em 60 amostras de linha de base, com `$00A6=$0500`, X foi `$0500`; em 60 amostras com bola sintética livre e `$00A4/$00A6=0`, X foi `$0400`. Isso confirma a seleção nesses contextos, não todas as condições de câmera da ROM. Um replay estendido manteve a bola distante e mostrou que o deslocamento da câmera ocorreu gradualmente.

Com `ISSD_GOAL_CAMERA_LONG=1`, a sonda de gol mantém a bola sintética perto da extremidade direita por 2.100 quadros antes de um único ensaio de borda. As imagens locais `goal-01-004.png` e `goal-01-008.png` mostram trave e bola na cena; no quinto quadro, a bola entrou em `83:8BAB → 83:8BC8 → 83:8BF8`. No caminho seguinte, os hooks `83:90B3` e `83:A900` registraram a componente `$0424:$0422` antes e depois da sub-rotina: `257634 → -128817` em inteiro fixo 16.16, isto é, inversão e divisão por dois neste caso. Sub-rotinas posteriores modificaram novamente a velocidade. Não foi observada chamada `80:BF05` durante os 40 quadros deste ensaio; isso não identifica nem descarta o som relatado pelo usuário em outra situação.

`python tools/audit_issd_camera_goal_edge.py analysis/camera-selection-probe/trace.jsonl analysis/goal-camera-long-detail/trace.jsonl analysis/goal-camera-long-detail/goal-01-004.png analysis/goal-camera-long-detail/goal-01-008.png docs/issd-camera-goal-edge-observation.json` valida as 120 seleções, a sequência de hooks, a inversão e os hashes das imagens. A cena é sintética: a presença visual da trave e a resposta de borda no mesmo ensaio ainda não medem o ponto de contato pixel a pixel, e nenhuma gravação PCM foi obtida. Não se pode aplicar diretamente a resposta à física web sem mapear unidades, outras velocidades e a decisão entre poste, rede e demais limites. Relatório: [issd-camera-goal-edge-observation.json](issd-camera-goal-edge-observation.json).

Em uma comparação adicional, restaurar isoladamente `$1B90` ao valor observado no estado recém-carregado não impediu a mudança da posição da bola depois de dois quadros, tanto para injeção antes do avanço quanto no início do quadro. Isso descarta apenas a suficiência dessa alteração isolada no estado sintético; a origem completa da mudança continua pendente.

### Bola alta, resposta de borda e comando de áudio `$2C`

A matriz `ISSD_GOAL_MATRIX=1` prepara a câmera na extremidade direita por 2.100 quadros, salva um estado **temporário local** e o restaura para cada uma de 25 combinações de cinco offsets e cinco alturas iniciais. `ISSD_GOAL_MATRIX_REUSE=1` permite repetir a instrumentação a partir desse estado; nem ele nem a ROM são distribuídos. A captura detalhada monitora `83:8AFF`, `83:8B47`, `83:8B75`, `80:BF05` e as sub-rotinas de resposta.

Nos três casos centrais iniciados nas alturas `0`, `-55` e `-56`, o placar passou de `0–0` a `1–0` e foi observado `86:D98C`. Nos dois casos centrais iniciados a `-63` e `-64`, não houve gol nos 40 quadros; no terceiro quadro, com `$2A=1855` (campo de largura 1856) e `$2C=320`, o fluxo observado foi `83:8AFF → 83:8B47 → 83:8B75 → 80:BF05 → 83:8B85 → 83:8D08 → 83:8C51 → 83:90B3 → 83:A900`. A fila da APU recebeu `$2C`; a velocidade `$0424:$0422` passou de `259438` a `-129719` em inteiro fixo 16.16 entre a entrada de `83:90B3` e a entrada de `83:A900`, exatamente inversão e metade nesse valor observado. As imagens locais dos quadros 1 e 4 incluem a trave e a jogada.

O disassembly em `83:8B47..8B75` limita esse caminho central a alturas nativas `[-64,-56)` e proximidade da linha, sujeito aos demais desvios, velocidade e estado. A matriz mostra uma distinção reproduzível entre gols e resposta alta com um comando de áudio, **compatível com a hipótese de travessão e com o relato do usuário**. Não foi gravado o áudio PCM nem verificado o ponto de contato em pixels; portanto não identifica definitivamente o som ou a estrutura em todas as situações. Alturas informadas na preparação não substituem as alturas efetivas nos hooks, e outros lados, velocidades, unidades e situações naturais ainda precisam ser validados antes de aplicar a física ao navegador.

`python tools/audit_issd_high_ball_goal.py analysis/goal-camera-matrix-detail/trace.jsonl analysis/goal-camera-matrix-detail/goal-14-001.png analysis/goal-camera-matrix-detail/goal-14-004.png docs/issd-high-ball-goal-observation.json` verifica as 25 combinações, os três gols centrais, as duas respostas altas, `$2C`, a inversão e os hashes das imagens locais. Relatório: [issd-high-ball-goal-observation.json](issd-high-ball-goal-observation.json).

### Bola alta em três velocidades e tentativa na extremidade esquerda

A sonda `ISSD_GOAL_VARIATION=1` experimentou velocidades horizontais iniciais de 2, 4 e 6 unidades por quadro, nas alturas iniciais `-56`, `-63` e `-64`, usando offset central. Na direita, o estado de câmera já preparado foi restaurado em cada um dos nove casos. Os três iniciados a `-56` marcaram gol; os seis iniciados a `-63/-64` passaram por `83:8B75`, colocaram `$2C` na fila da APU e não marcaram gol nos 40 quadros observados.

Nos seis casos altos à direita, os pares efetivos de velocidade `$0424:$0422` na entrada de `83:8C51` e na entrada posterior de `83:A900` foram, em inteiro fixo 16.16: `126562 → -65536`, `259438 → -129719` e `391412 → -195706` para as velocidades iniciais 2, 4 e 6, respectivamente; os mesmos pares ocorreram nas duas alturas iniciais. Para o valor menor, `83:8C51` seguiu a guarda do word alto menor que 2 e atribuiu velocidade mínima; para os outros, o trecho `83:90B3` inverteu e dividiu por dois. Os resultados se referem aos valores **efetivos nos hooks**, não necessariamente aos da injeção.

Uma câmera independente foi preparada para a esquerda, também com nove casos. Nesse estado, a posição inicial injetada não permaneceu até o primeiro quadro: a bola apareceu em `$2A≥32`, e os casos não acionaram `83:8B75`. Portanto, **não há comparação válida do lado esquerdo** e a ausência do som ou do gol não é evidência sobre a física. A hipótese de travessão continua compatível com a resposta e o relato auditivo do usuário, mas a identificação do áudio PCM, o contato visual exato e a conversão para unidades web seguem pendentes.

`python tools/audit_issd_high_ball_speeds.py analysis/goal-velocity-right/trace.jsonl analysis/goal-velocity-left/trace.jsonl docs/issd-high-ball-speed-observation.json` valida os 18 cenários, as seis respostas direitas e o limite da tentativa esquerda; `python tools/test_issd_goal_edge_velocity.py` cobre as guardas e o arredondamento da tradução isolada. Os estados temporários, imagens e ROM continuam locais. Relatório: [issd-high-ball-speed-observation.json](issd-high-ball-speed-observation.json).

### Bola alta nas duas extremidades

A tentativa inconclusiva da esquerda foi repetida com `ISSD_GOAL_VARIATION_FRESH=1`: cada ensaio restaura o estado inicial original imediatamente antes da injeção, sem usar o estado da câmera que já havia mudado a posse. O replay foi comparado com os nove casos previamente capturados à direita. Foram 18 casos de 40 quadros: dois lados, três velocidades horizontais iniciais (2, 4, 6) e três alturas iniciais (-56, -63, -64), sempre com offset central. Os três casos de cada lado iniciados em `-56` marcaram gol; os seis de cada lado iniciados em `-63/-64` acionaram `83:8B75`, colocaram `$2C` na fila da APU e não marcaram gol na janela observada. As imagens dos dois lados são locais.

Na esquerda, os valores efetivos `$0424:$0422` observados antes de `83:8C51` e depois na entrada de `83:A900` foram `-129207 → 64603`, `-261025 → 130512` e `-392470 → 196235` em inteiro fixo 16.16, para as velocidades iniciais 2, 4 e 6, nas duas alturas altas. Na direita foram `126562 → -65536`, `259438 → -129719` e `391412 → -195706`. No caso mais lento à esquerda, o word alto negativo é `-2`; a rotina toma a magnitude de 2 antes da comparação e segue o ramo de inversão e divisão. À direita, o word alto positivo é `1`, acionando o ramo de velocidade mínima. Isso é uma consequência das operações e dos valores capturados, não evidência de que os dois gols tenham regras diferentes em qualquer condição.

`python tools/audit_issd_high_ball_both_goals.py analysis/goal-velocity-right/trace.jsonl analysis/goal-velocity-left-fresh/trace.jsonl analysis/goal-velocity-left-fresh/goal-05-004.png docs/issd-high-ball-both-goals.json` verifica os 18 casos, seis gols, 12 respostas e os comandos `$2C`. A evidência reforça a hipótese de travessão nos contextos sintéticos, mas ainda não identifica o PCM ouvido nem mede o contato físico e a conversão das unidades para a web. Relatório: [issd-high-ball-both-goals.json](issd-high-ball-both-goals.json).

**Confirmação do usuário:** o usuário identificou o som ouvido como impacto no **travessão**. Essa identificação, combinada com os ensaios sintéticos de bola alta nos dois lados, fortalece a associação do caminho `83:8B47 → 83:8B75` e do comando `$2C` com o travessão. A confirmação é auditiva e não foi vinculada a um arquivo PCM ou quadro específico; os ensaios registraram o comando, mas não gravaram o áudio. A conversão para coordenadas e velocidade web, o ponto visual de contato e outras condições de jogo continuam a validar antes da aplicação.

### Modelo isolado do candidato de travessão

`dist/native-crossbar.mjs` traduz o ramo central `83:8AFF / 83:8B47..8B75` em words nativos: seleção pela faixa central por estádio, altura `[$FFC0,$FFC8)`, limites imediatamente adjacentes às linhas e a guarda do comando `$2C` (`$24,x != 0` e `$00BA == 0`). Essa função identifica apenas o ramo estudado; os demais caminhos de borda, rede e saídas não são decisões de gol deduzidas por ela.

A função `nativeCrossbarHorizontalResponse` traduz isoladamente `83:8C51..8C78 / 83:90B3..90C2`, preservando a comparação do word alto, o sinal do outro componente e a inversão/deslocamento do valor 16.16. O contrato exige o estado **após `83:8D08`** e não inclui efeitos das rotinas anteriores ou posteriores. `node --test dist/test-native-crossbar.mjs` verifica limites, arredondamento e velocidade mínima; quando os traços locais estão presentes, compara o modelo com pares de hooks dos dois gols e com os desvios `83:8B47` da matriz de 25 casos. `node dist/test-native-goal-bands.mjs` também confirma os limiares contra a ROM local.

Este módulo não está ligado à partida web: a transformação nativa para as unidades da bola web, a altura do travessão e os limites visuais ainda não foram validados. A identificação auditiva do usuário foi registrada acima; os testes de replay observam o código de áudio, não PCM. Nenhuma regra de colisão do protótipo foi alterada nesta etapa.

### Altura nativa e deslocamento vertical observado na imagem

A matriz de chutes enquadrados permite comparar imagens com a mesma posição horizontal da bola e alturas diferentes. Nos casos 11, 12 e 13, as amostras de estado do terceiro quadro possuem os mesmos `$0408/$040C` e `$042A/$042C`; as alturas são 0, -55 e -56. Na captura de imagem solicitada no quarto passo, as duas maiores regiões de diferença entre cada par exibem deslocamentos verticais de 55 e 56 pixels, respectivamente, na imagem SNES de 256×224. Ao transladar as regiões superiores por esses valores, 30 de 30 e 28 de 28 pixels alterados coincidem com a região inferior correspondente. A correspondência temporal com o terceiro quadro é observada **nestes dois pares**; não prova uma latência geral do pipeline.

Isso fornece evidência de aproximadamente um pixel da imagem nativa por unidade de altura nesses casos sintéticos, sem depender da imagem de estádio exportada. Não estabelece que um pixel nativo equivalha a uma unidade do mundo web: a escala dos atletas, o recorte, a proporção de tela, a câmera e a projeção do navegador ainda precisam ser associados. Tampouco mede a altura física do travessão ou o raio de colisão. Portanto, o modelo isolado de travessão ainda não foi conectado à partida.

Reproduzir: `python tools/audit_issd_ball_height_pixels.py analysis/goal-camera-matrix-detail/trace.jsonl analysis/goal-camera-matrix-detail docs/issd-ball-height-pixels.json`. O auditor exige Pillow, compara os valores registrados e as duas maiores regiões conectadas de diferença em cada par, e guarda hashes; imagens, estado e ROM permanecem locais. Relatório: [issd-ball-height-pixels.json](issd-ball-height-pixels.json).

### Diagnóstico de escala nativa e altura do chute web

`node tools/audit_issd_native_web_scale.mjs` lê o recurso local de locomoção, os parâmetros atuais do renderizador e as funções reais do chute web. As oito células capturadas de caminhada e as oito de corrida têm altura 52; o corpo de referência e ações nativas são dimensionados com `actorVisual.player.h=38`, resultando em `38/52 ≈ 0,73077` unidade de desenho web por pixel da célula capturada. O resultado inclui transparência da célula e não prova que todas as reservas visuais usem a mesma geometria.

**Se** o deslocamento de um pixel nativo por unidade de altura observado na seção anterior for convertido pela mesma proporção, os valores nativos 56 e 64 corresponderiam a aproximadamente 40,92 e 46,77 unidades de altura web. Essa hipótese é apenas um diagnóstico visual: a observação por pixels cobriu as alturas 55 e 56, e a extrapolação até 64 e a equivalência com unidades físicas permanecem não validadas. Para comparação, o chute alto web atual, integrado livremente em ciclos fixos com `vz=-2,8` e gravidade `0,125`, atinge pico aproximado de 29,98 unidades no quadro 22 e retornaria ao solo no quadro 44 sem colisões. Portanto, sob essa hipótese, a trajetória livre atual não alcançaria a faixa candidata; isso não descreve toda jogada com quique ou outras interações.

As razões de campo web/nativo do estádio índice 1 também são distintas nos eixos: `1150/1856` e `523/640`. São escolhas de escala do protótipo, não comprovação do Mode 7. Nenhuma dessas razões autoriza alterar por si só a física, altura da trave ou abertura do gol. O relatório [issd-native-web-scale-diagnostic.json](issd-native-web-scale-diagnostic.json) inclui parâmetros, hash do recurso e limitações; a ROM permanece local. O modelo nativo de travessão continua isolado até comparar trajetória, dimensão da bola e geometria do gol em estados e capturas compatíveis.

### Subida observada da bola nativa até o pico

`tools/audit_issd_natural_shot_peak.py` amplia a auditoria do replay de uma ação com botão X e bola nativa tipo 3: verifica novamente a ROM e os campos comparados com o replay de referência, e acompanha 64 atualizações consecutivas registradas desde o primeiro passo aéreo até o pico. A velocidade vertical inicial observada foi `-7,0` unidades nativas por atualização e a aceleração foi `7168/65536 = 0,109375`; a maior altura observada foi `220,5` unidades nos quadros 4342 e 4343. O quadro 4280 não possui os hooks, mas os valores antes/depois das atualizações registradas permanecem consecutivos; o auditor não interpola uma atualização para esse quadro.

Os 64 conjuntos de valores estão em [issd-natural-shot-peak.json](issd-natural-shot-peak.json), e `node dist/test-native-shot-peak.mjs` compara cada um deles com `advanceNativeAirborneHeight`, a implementação isolada em ponto fixo. Também foi executado `node dist/test-native-ball-fixed.mjs`. O relatório anterior da subida tinha validado somente uma janela de 61 atualizações; esta auditoria estende essa janela até o pico, sem concluir que a sequência posterior inteira ou o contato com o solo sejam idênticos.

A relação visual hipotética `38/52` aplicada ao pico produziria aproximadamente `161,13` unidades web, mas **não é uma calibração de física**. O replay representa uma ação X, com um atleta, direção, condição e tipo de bola; não foi demonstrado que seja o mesmo comando ou a mesma força do chute alto web. O pico web livre de aproximadamente `29,98` registrado na seção anterior, portanto, revela uma diferença a investigar, não um multiplicador que possa ser aplicado indiscriminadamente. A mudança de direção vertical posterior no mesmo trace também deve ser investigada separadamente antes de atribuí-la a quique, contato ou outra ação.

Reprodução: `python tools/audit_issd_natural_shot_peak.py --root analysis/shot-airborne-vertical --baseline analysis/shot-body-replay --rom 'International Superstar Soccer Deluxe/International Superstar Soccer Deluxe (USA).sfc' --output docs/issd-natural-shot-peak.json`. As capturas e a ROM permanecem locais.

### Contexto da ação X e contador de carga

Foram repetidos dois replays isolados do mesmo estado e do ator `$1900`, com botão X e preparações de direção diferentes. Cada novo replay teve **325 amostras comparáveis** iguais aos respectivos replays de referência nos campos registrados. `tools/probe_issd_shot_charge.lua` observou a entrada das rotinas de liberação e a atualização do contador `+$82`.

No caso preparado para a direita, a rotina chegou a `85:F871` com X=3, Y=11, contador zero e botão X ainda pressionado; no trecho `85:F694`, o bit `$0800` em `+$6E` estava limpo. Esse é o caminho de parâmetro fixo 11 do tipo 3, coerente com a trajetória alta posteriormente auditada. No caso preparado para a esquerda, o bit `$0800` estava ligado, o contador subiu de 0 a 5 com máscara `$0040` e parou ao soltar X; a rotina chegou a `85:F89B` com X=5, Y=5 após a liberação do botão. Os dois contextos diferem em flags, tempo e caminho, além da preparação de direção: **não se pode atribuir a diferença somente à direção** nem concluir uma regra universal do botão.

`dist/native-action-charge.mjs` traduz isoladamente `80:DA68..DA7B` sobre words de entrada: incrementa enquanto o botão mascarado está ativo e o contador é menor que 11; caso contrário, limpa a máscara e conserva o contador. `node --test dist/test-native-action-charge.mjs` cobre os limites e, quando o trace local está disponível, compara a sequência observada de X. A frequência de chamada, o remapeamento de controles, os demais ramos e a relação com o comando web ainda não estão completos; o módulo não altera a jogabilidade.

`python tools/audit_issd_shot_release_context.py analysis analysis/shot-body-replay/issd-auto-probe-20261105-141300.jsonl analysis/shot-facing-Left/issd-auto-probe-20261105-142106.jsonl docs/issd-shot-release-context.json` confere os replays e hooks; relatório: [issd-shot-release-context.json](issd-shot-release-context.json). Capturas, estado salvo e ROM permanecem locais.

### Duração de X no caminho de bola tipo 5

Para comparar a duração sem depender de partidas diferentes, `tools/probe_issd_shot_charge.lua` salvou um estado local imediatamente antes da ação observada do ator `$1900`, com posse e direção nativa 4. `tools/probe_issd_shot_hold_durations.lua` restaurou esse mesmo estado para cada ensaio e manteve X por 1, 3, 6, 10, 15 ou 20 quadros, seguido de entrada neutra. Os seis casos produziram bola tipo 5. As velocidades abaixo são amostras 16.16 **ao final do quadro da liberação**, em unidades nativas; não são necessariamente os valores na instrução exata de inicialização.

| Quadros de X enviados | Contador observado na liberação | Velocidade vertical observada | X ainda pressionado na liberação |
|---:|---:|---:|:---:|
| 1 | 0 | -0,25 | Não |
| 3 | 2 | -0,50 | Não |
| 6 | 5 | -1,50 | Não |
| 10 | 9 | -2,25 | Não |
| 15 | 11 | -2,50 | Não |
| 20 | 11 | -2,50 | Sim |

Nesse contexto, as componentes horizontais amostradas na liberação permaneceram `-7,8125` e `-0,2734375`; as alturas variaram conforme o contador. O caso de 20 quadros liberou a bola no passo 16 mesmo com o botão mantido, depois de o contador atingir 11. Isso é uma observação desse caminho e estado, não prova de que todo chute no ISSD carregue da mesma forma, de que 11 ciclos correspondam a 11 quadros em qualquer contexto ou de que o botão X nativo corresponda diretamente à tecla X web. A relação entre o contador e valores intermediários não foi interpolada.

`python tools/audit_issd_shot_hold_durations.py analysis/shot-hold-duration/trace-fixed.jsonl analysis/shot-charge-seed/shot-start.State docs/issd-shot-hold-durations.json` valida os seis casos e o hash do estado; `node --test dist/test-native-action-charge.mjs` verifica a regra isolada de contagem. A ROM, o estado salvo e o trace ficam locais. O motor web permanece inalterado até mapear os demais contextos, o controle e a conversão de unidades. Relatório: [issd-shot-hold-durations.json](issd-shot-hold-durations.json).

### Tabela nativa de velocidade vertical da bola tipo 5

A varredura `ISSD_HOLD_SWEEP=1` repetiu a ação anterior com 15 durações, cobrindo todos os parâmetros observados de 0 a 11. O disassembly explica a origem: o despacho `83:956E` encaminha a bola tipo 5 a `83:96E7`, que chama `83:9702`. Essa rotina usa `$0456` como índice de 12 words em `81:A24B` (parte inteira de `$0436`) e `81:A263` (parte fracionária de `$0434`). A auditoria confirmou os 24 words na ROM USA e comparou os 15 lançamentos; nas condições capturadas, os valores no fim do quadro da liberação coincidiram com as tabelas.

| Parâmetro nativo | Velocidade vertical inicial 16.16 |
|---:|---:|
| 0, 1 | -0,25 |
| 2 | -0,50 |
| 3 | -0,75 |
| 4 | -1,25 |
| 5 | -1,50 |
| 6 | -1,75 |
| 7, 8 | -2,00 |
| 9, 10 | -2,25 |
| 11 | -2,50 |

`dist/native-shot-type5.mjs` disponibiliza apenas essa consulta por parâmetro nativo, retornando os dois words, sem supor qual comando web a seleciona ou como converter suas unidades. `node --test dist/test-native-shot-type5.mjs` testa os 12 valores, rejeita parâmetros inválidos e, quando presentes localmente, confere a ROM e os 15 lançamentos. A auditoria reproduzível é `python tools/audit_issd_type5_vertical_table.py 'International Superstar Soccer Deluxe/International Superstar Soccer Deluxe (USA).sfc' analysis/shot-hold-full/trace.jsonl analysis/shot-charge-seed/shot-start.State 'YFs_InternationalSuperstarSoccerDeluxe_Disassembly/International_Superstar_Soccer_Deluxe/Routine_Macros_ISSD.asm' docs/issd-type5-vertical-table.json`.

A tabela é uma parte da inicialização tipo 5, não a física completa ou uma regra universal de X: direção, outras flags, aceleração, quique, origem do parâmetro em outros contextos e escala web continuam a ser validados. À época dessa análise a implementação estava isolada; posteriormente houve a integração provisória descrita abaixo. A ROM, o estado salvo e os traces não são distribuídos. Relatório: [issd-type5-vertical-table.json](issd-type5-vertical-table.json).

### Campos auxiliares da inicialização tipo 5

No mesmo caminho, `83:96D8` extrai o nibble inferior de `$12DC` e o limita a 9. `83:96E7` usa esse índice na tabela de dez words em `81:A293`; depois `83:9702` troca o índice pelo parâmetro `$0456`. A rotina compartilhada `83:9686` grava em `$0458` o word correspondente de `81:A27B` e em `$0454` a soma dos words de `81:A293` e `81:A233`. Os endereços são offsets `0x00A293`, `0x00A27B` e `0x00A233` na ROM USA sem cabeçalho. Os dois últimos usam índice de 0 a 11; nenhuma extrapolação para índices maiores foi feita.

`nativeType5AuxiliaryFields` em `dist/native-shot-type5.mjs` reproduz esses cálculos de words, inclusive o limite do nibble. O teste `node --test dist/test-native-shot-type5.mjs` compara 192 combinações diretamente às três tabelas da ROM local quando disponível e testa entradas inválidas. Esta verificação confirma a transcrição da lógica e das tabelas, mas não prova uma relação direta com velocidade horizontal. A investigação posterior identificou o uso de `$0458` como aceleração vertical e integrou-o provisoriamente à partida, conforme descrito nas seções seguintes; a função de `$0454`, a seleção da direção e a conversão para unidades web continuam pendentes.

### Aceleração vertical observada no tipo 5

Na rotina `83:941F`, quando a posição ou a velocidade vertical é diferente de zero, o caminho `83:942E` soma `$0458` à parte fracionária de `$0434/$0436` e propaga o carry. Portanto, nesse caminho, `$0458` atua como aceleração vertical 16.16. A tabela de inicialização `81:A27B` fornece `0x1000` para parâmetros 0–5, `0x1C00` para 6–7 e `0x2000` para 8–11. Isso explica a aceleração, não a velocidade horizontal; a função esportiva de `$0454` permanece pendente.

`tools/audit_issd_type5_acceleration.py` confronta a tabela e o trecho do disassembly com os 15 ensaios locais anteriores. Entre pares consecutivos de quadros com bola tipo 5 livre e velocidade vertical negativa em ambos, encontrou **182 incrementos** iguais ao valor da tabela e **196 pares sem mudança**, cobrindo os 12 parâmetros. Os quadros inalterados são relatados, sem atribuir uma causa ou supor que a rotina rode em todo quadro. As amostras são valores ao fim de cada quadro; não comprovam altura, pouso, quique, outras direções ou conversão para a web. Reproduzir: `python tools/audit_issd_type5_acceleration.py 'International Superstar Soccer Deluxe/International Superstar Soccer Deluxe (USA).sfc' analysis/shot-hold-full/trace.jsonl 'YFs_InternationalSuperstarSoccerDeluxe_Disassembly/International_Superstar_Soccer_Deluxe/Routine_Macros_ISSD.asm' docs/issd-type5-acceleration-observation.json`. A ROM e o trace continuam locais.

### Aplicação provisória à partida web

O chute controlado pelo usuário em `dist/shot-model.mjs` agora obtém velocidade vertical inicial e aceleração das tabelas nativas tipo 5. Como a web ainda oferece apenas chute baixo e chute alto, usa provisoriamente os parâmetros nativos 2 e 11, respectivamente; essa escolha não está comprovada como equivalência dos controles originais. Ambos os valores verticais são multiplicados por `2.8/2.5`, escolhido para preservar a velocidade inicial do chute alto existente no navegador, não como medição de escala. O resultado é baixo `vz=-0.56`, gravidade `0.07`, e alto `vz=-2.8`, gravidade `0.14`, por passo do protótipo. A ordem de atualização aérea já usada pelo jogo foi mantida.

Essa integração aplica dados da ROM, mas **não comprova fidelidade da trajetória**: parâmetros de controle, escala, avanço temporal, movimento horizontal, contato e quique ainda precisam de calibração. Inicialmente a CPU manteve sua trajetória anterior; a integração posterior está descrita abaixo. Os testes `node dist/test-goalkeeper-model.mjs`, `node dist/test-human-actions.mjs`, `node dist/test-projection-game-integration.mjs` e `node dist/test-match-flow.mjs` cobrem os valores do chute, sua direção, integração do comando e comportamento relacionado do goleiro.

### Velocidade horizontal na varredura de carga

Na mesma varredura de 15 lançamentos tipo 5, os quatro words da velocidade horizontal no fim do quadro de liberação foram iguais em todos os ensaios: `$0424/$0422 = FFF8:3000` e `$0428/$0426 = FFFF:BA00`, ou `-7,8125` e `-0,2734375` em 16.16. A auditoria `tools/audit_issd_type5_vertical_table.py` agora verifica e registra esses words, e `node --test dist/test-native-shot-type5.mjs` também compara as 15 observações locais. Isso sugere que variar a carga nesse estado específico não mudou o vetor horizontal inicial; não demonstra uma regra geral nem determina sua escala web, evolução posterior ou relação com outras direções. A velocidade horizontal da partida não foi modificada com base nesse único cenário.

O teste anterior da sala online foi repetido após gerar a identidade atualizada e passou, assim como os 11 testes da suíte do servidor. A falha ocorria quando o servidor calculava a identidade do código alterado e o teste de interface ainda importava a identidade anterior. O comando `npm run test:server` agora executa `build:identity` automaticamente antes dos testes para evitar esse desencontro.

### Evolução horizontal nas capturas tipo 5

`tools/audit_issd_type5_horizontal_flight.py` examina pares consecutivos após a liberação nos 15 ensaios locais, enquanto a bola está livre e permanece tipo 5. Foram 453 pares sem mudança nas componentes horizontais e dois com mudança. Nos dois, as componentes passaram de `FFF8:3000 / FFFF:BA00` para `FFF9:2A00 / FFFF:C2C0`; a velocidade vertical também passou de positiva para negativa no mesmo intervalo. O resultado é compatível com os registros de redução em um quique tipo 5 descritos acima, mas estes quadros não registram altura nem hook de impacto: não identificam por si só o ponto ou a causa exata da mudança.

A partida web já mantém o vetor horizontal durante o voo livre; o teste de integração em `dist/test-goalkeeper-model.mjs` agora verifica cinco passos consecutivos. A redução horizontal no impacto ainda não foi aplicada, pois a regra depende de tipo, clima e flags, que o protótipo ainda não associa com fidelidade. Reprodução: `python tools/audit_issd_type5_horizontal_flight.py analysis/shot-hold-full/trace.jsonl docs/issd-type5-horizontal-flight.json`. A conclusão limita-se a um estado salvo, uma direção e uma condição de campo; o trace permanece local.

### Modelo vertical compartilhado com a CPU

Os chutes da CPU agora usam a mesma consulta de velocidade vertical e aceleração tipo 5 que os chutes do usuário. Enquanto não há mapeamento das decisões e cargas originais da CPU, o protótipo escolhe provisoriamente o parâmetro 4 para finalizações direcionadas ao gol e 11 para afastamentos. A escolha de direção e a velocidade horizontal existentes da CPU foram preservadas. Para a finalização, o parâmetro 4 também mantém a trajetória abaixo do travessão provisório no cenário de regressão existente; isso não valida a decisão da ROM nem a escala de campo. `node dist/test-match-flow.mjs` verifica a aplicação e o gol nesse cenário; `node dist/test-goalkeeper-model.mjs` verifica os dois planos e o compartilhamento da trajetória alta. A conversão de unidades, a escolha da força, o quique e as demais condições seguem pendentes de calibração.

### Bola verticalmente parada

O modelo isolado `advanceNativeAirborneHeight` foi corrigido para respeitar a guarda de `83:941F`: quando os quatro words da altura e velocidade vertical são zero, a rotina não soma `$0458`. Antes, o modelo aplicava aceleração também nesse caso. `node dist/test-native-ball-fixed.mjs` cobre a condição parada e a validação das entradas; `node dist/test-native-shot-peak.mjs` continua conferindo 64 atualizações da captura de chute e `node --test dist/test-native-throwin-flight.mjs` verifica a trajetória nativa de lateral. Essa correção é do modelo de investigação e não altera por si só a física da partida web; o tratamento de solo, posse e quique continua separado.

### Recuperação no quadro inicial do quique web

No protótipo, o impacto fixa `z=0` e inverte a velocidade vertical; nesse mesmo quadro, a bola pode já estar subindo (`vz<0`). Antes, a recuperação local tratava esse estado como bola no chão. No lateral online, além da recuperação, ele também recebia atrito de rolagem. A recuperação terrestre local agora aguarda `vz>=0`, e o lateral online não aplica atrito nem recuperação terrestre no quadro em que o quique começa. A recepção aérea anteriormente disponível continua ativa para `z<0`.

Essa é uma correção de consistência do protótipo, não uma regra de contato validada na ROM. `node dist/test-match-flow.mjs` cobre o caso local e a recuperação parada; `node --test dist/test-online-ball.mjs` cobre o impacto, manutenção da velocidade horizontal, recepção aérea e recuperação após o repouso. As alturas, restituição e elegibilidade completas de recepção ainda requerem comparação com a referência.
