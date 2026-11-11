# Investigação da cobrança lateral do ISSD

## Referência e cenário reproduzível

Na ROM americana identificada por SHA-256
`d2fe66c1ce66c65ce14e478c94be2e616f9e2cad374b5783a6a64d3c1a99cfa9`,
o cenário original 5 anuncia lateral da Turquia contra a Suécia. A entrada
da tabela está no offset PC `0x5FD34`; seu resumo textual está em
`0x3EF1B`. O auditor `tools/audit_issd_throwin_scenario.py` verifica a
identidade e os dados sem alterar nem distribuir a ROM. O editor de referência
`analysis/reference-issd-studio/src/rom/scenario-position.mjs` documenta o
formato das posições; a rotina `CODE_8BDA6A` no disassembly carrega os dados
do cenário. Os arquivos de captura e o estado do emulador ficam em `analysis/`,
fora da distribuição.

## Observação controlada

Uma instância isolada do BizHawk abriu o cenário 5 e salvou um estado antes
da cobrança. Cinco reexecuções partiram desse mesmo estado, observando 150
quadros; os botões A, B, X, Y ou nenhum foram aplicados nos passos 60–65.
Na imagem original, o cobrador segura a bola acima da cabeça. Nesta amostra,
`$00A6` apontou ao cobrador em `$0600`; `$1AFC` apontou a outro ator e não
deve ser usado para identificar o cobrador.

* Com A ou B, a fase em `$00C0` passou de 3 a 0 no passo 70. O tipo da
  bola em `$0430` passou de 14 para 20 com A e para 15 com B; as velocidades
  observadas diferem. Não está comprovado que esses valores definam
  universalmente o tipo de cobrança.
* Sem botão ou com X ou Y, nenhuma dessas transições ocorreu nos 150 quadros
  observados. Isso é uma observação do cenário, não uma regra geral.
* Na execução com A, o estado do ator em `$0632` foi `0x0408` no passo 60,
  `0x0410` no 64 e `0x0418` no 66. Os descritores em `$0614` observados nos
  passos 60, 66, 70 e 74 foram respectivamente `0xAA07`, `0xA9FE`,
  `0xAA10` e `0xAA19`. Esses pontos não estabelecem, por si só, a sequência
  completa nem a duração de todos os quadros.

A captura é reproduzível com `tools/capture_issd_throwin_replay.lua` e um
estado local da cobrança, informando `ISSD_THROW_STATE`, `ISSD_THROW_OUTPUT`
e `ISSD_THROW_BUTTON`. Não se deve confundir os valores de RAM aqui observados
com offsets de ROM.

## Pendente

Capturar e validar OAM, VRAM e paletas do cobrador durante toda a preparação
e soltura; identificar todas as poses e durações; testar direcionais e o
outro lado do campo; identificar atribuição da cobrança, alvo, velocidade,
altura, recepção e retomada. Depois integrar a composição validada ao
laboratório e ao jogo web. O reinício atual da versão web é provisório e
ainda não implementa a bola nas mãos ou o arremesso original.

## Direcionamento e captura gráfica complementar

Novas reexecuções do mesmo estado mantiveram A nos passos 60–65. Os quatro
direcionais foram testados tanto somente nos passos 60–65 quanto desde o
passo 0 até o 65. O campo `$0020` confirmou que cada comando chegou ao jogo.
Ao iniciar o direcional apenas no passo 60, a trajetória registrada da bola
foi idêntica à execução sem direcional nos 150 passos. Mantendo o direcional
desde o passo 0, houve alterações: no passo 80, as coordenadas brutas X/Y da
bola foram `88/86` (cima), `127/101` (baixo), `123/100` (esquerda) e
`126/92` (direita). O campo de direção do cobrador também mudou em algumas
execuções. É evidência de direcionamento anterior ao arremesso nesse cenário;
a janela mínima e a conversão de direções para o campo ainda não foram
determinadas. Não se deve assumir que esses números valem para os dois lados
do campo, outros cenários ou outros botões.

A captura opcional `ISSD_THROW_GRAPHICS=1` registrou, em 31 passos consecutivos
(55–85), a OAM, VRAM, CGRAM, tela e metadados do ator apontado por `$00A6`
antes da soltura. O validador `tools/validate_issd_native_action_oam.py`
confirmou integridade de todos os 31 registros. Isso **não** valida ainda quais
entradas OAM pertencem ao cobrador nem a reconstrução visual. A ferramenta
`validate_issd_action_descriptor_capture.py` requer `uniform_selector` e
`parts`, ausentes nessa captura bruta; sua validação permanece pendente.

Para reproduzir os experimentos, `ISSD_THROW_DIRECTION` aceita `Up`, `Down`,
`Left`, `Right` ou `NEUTRAL`; `ISSD_THROW_DIRECTION_START` define o primeiro
passo em que o direcional é mantido (padrão 60). Os dados locais contêm
gráficos da ROM e não devem ser incluídos na distribuição.

## Validação da geometria do corpo

Uma nova execução controlada capturou os eventos da rotina de desenho em
`$80:95E3`, acompanhando o ator `$0600` identificado pela ligação da cobrança.
A ferramenta existente `capture_issd_slide_replay.lua` foi reutilizada como
instrumentação de OAM para essa execução, apesar do nome. O novo auditor
`tools/audit_issd_throwin_body.py` compara geometria em `$88` da ROM, os
slots emitidos, espelho OAM e OAM da PPU; depois compõe os pixels dos slots
com VRAM e CGRAM e compara cada pixel com a captura do emulador.

Foram validados 24 quadros do corpo, com **8.448 pixels candidatos e zero
divergências**. Os descritores observados foram `$AA07` (5 quadros), `$A9FE`
(4), `$AA10` (4) e `$AA19` (11). Seis quadros intermediários (2262–2267
na contagem dessa execução) não têm sequência de eventos de desenho completa
e foram explicitamente marcados como ausentes; a causa ainda não foi
determinada. Os números não estabelecem a duração integral das poses.

A validação cobre apenas as partes de corpo visíveis nessa execução, uma
direção e o cenário 5; não comprova cabelo ou composição para outros
uniformes. Ainda não foi produzida uma spritesheet ou aplicada ao jogo: é
necessário obter a transição faltante, confirmar a cadência e verificar as
outras orientações. Os dados brutos e o relatório de auditoria permanecem em
`analysis/throw-in-draw-a/`, ignorados pelo Git.

Auditoria reproduzível, usando a ROM local e a captura original:

```sh
python tools/audit_issd_throwin_body.py analysis/throw-in-draw-a --rom "caminho/para/rom.sfc" --actor 0x600 --output analysis/throw-in-draw-a/audit.json
```

## Tabelas nativas e investigação da lacuna

A captura foi repetida a partir do mesmo estado sem screenshots nem dumps
por quadro, preservando apenas os hooks de desenho. A interrupção nos
eventos reapareceu nos mesmos quadros e a divisão da lista entre os quadros
2265 e 2266 também se repetiu. Isso enfraquece a hipótese de que a gravação
de imagens, sozinha, causou a lacuna; não prova invisibilidade nem a causa.

O disassembly identifica as tabelas de seleção por índice direcional:
`$82:D606` para as poses de espera; `$82:D65E` para a pose selecionada na
transição; e `$82:D66E` para os ponteiros das três poses da soltura. São oito
entradas, com reutilização de sequências entre índices. Os valores lidos da
ROM verificada estão em [issd-throwin-rom-tables.json](issd-throwin-rom-tables.json)
e podem ser reproduzidos com `tools/audit_issd_throwin_tables.py`. O índice 2
selecionou a sequência `$A9FE`, `$AA10`, `$AA19`, compatível com a captura
dessa cobrança. A orientação visual e o espelhamento dos outros índices
ainda precisam de validação dinâmica.

No disassembly, `CODE_84AE1B` consulta entradas para a cobrança e, sem
acionamento, atualiza direção em intervalos condicionados pelo contador
global. `CODE_84AEB1` seleciona a transição em `$82:D65E`; `CODE_84AF23`
inicia a sequência `$82:D66E` e define contador 4; `CODE_84AF3F` decrementa
esse contador e chama `CODE_85EF51` quando chega a zero. A associação da
chamada com a soltura observada no replay é consistente com os tempos
registrados, mas a rotina da bola e sua física ainda precisam ser auditadas.
Os bytes de temporização das tabelas foram registrados sem atribuir significado
a cada valor sem prova.

Para diagnosticar sobrecarga de captura, `ISSD_SLIDE_DRAW_ONLY=1` desativa
os dumps de quadro no coletor de eventos e `ISSD_THROW_SCREENSHOTS=0`
desativa screenshots adicionais do replay. Ambos são opcionais; os padrões
originais permanecem ativos.

## Novas direções e rotina da bola

Repetimos o mesmo cenário com A e os quatro direcionais mantidos desde o
começo, acompanhando `$0600` e verificando os fragmentos contra geometria da
ROM, espelho OAM, OAM da PPU e pixels da tela. Foram validados 99 quadros,
com 33.912 pixels sem divergência. No instante observado da soltura, os
comandos produziram os índices nativos 3 (cima), 2 (baixo), 3 (esquerda) e
1 (direita). Essa correspondência é específica do cenário e instante, e
não deve ser tratada como um mapeamento universal de controles.

As poses `$A9D1`, `$A9C8`, `$A9DA` e `$A9E3` também foram confirmadas
visualmente em quadros dessas execuções; a sequência `$A9C8`, `$A9DA`,
`$A9E3` é compatível com as tabelas dos índices 1 e 3. Em cada execução
cinco amostras não possuíam eventos completos de desenho. Além disso, no
comando para cima, um quadro tinha 18 pixels divergentes de 404; ele foi
excluído da validação, pois a causa da divergência ainda não foi comprovada.
O auditor permanece estrito por padrão; `--skip-screen-mismatch` registra
quadros divergentes à parte, sem tratá-los como validados.

Na rotina original `CODE_85EF51`, observamos por leitura estática a limpeza
da fase da cobrança e a seleção de dois valores para o estado da bola:
`$0014` no caminho sem o bit `$4000` de `$6E`, `$000F` no caminho com esse
bit. Ela chama `CODE_85EFB4`, que limita uma direção de acordo com `$00BE`,
e `CODE_85EFAB`, que impõe um mínimo de 4 ao valor em Y antes de seguir para
`CODE_85F8B9`. Os valores 20 e 15 coincidem com os tipos observados nas
reexecuções A e B; o significado completo de Y, a possível escolha de alvo e
as velocidades resultantes ainda exigem rastreamento dinâmico.

Esses resultados ampliam a evidência das poses, mas não comprovam todas as
oito direções nem o cabelo e os uniformes de outros jogadores. A cobrança
com as mãos e a física correspondente continuam pendentes no jogo web.

## Galeria local no laboratório

A seção `#throwin-lab` do laboratório apresenta amostras individuais do
corpo, geradas apenas a partir de quadros que passaram pela auditoria de
ROM, OAM e comparação exata de pixels. Ela permite inspecionar as capturas
feitas com cada comando direcional. Os nomes dos comandos descrevem apenas
a entrada usada no teste, não uma orientação universal do sprite.

São 19 amostras de corpo: não incluem bola, cabelo ou uma sequência animada,
e não representam uniformes de outras equipes. As imagens e o manifesto
são gerados localmente na pasta ignorada `dist/assets/issd/slide-lab-local/`
e não são distribuídos. Para regenerá-los a partir das capturas existentes:

```sh
python tools/export_issd_throwin_gallery.py --captures analysis/throw-in-body-directions --rom "caminho/para/rom.sfc" --output dist/assets/issd/slide-lab-local/throwin-gallery
```

A exportação reexecuta a auditoria e não inclui quadros com comparação de
tela divergente. O painel não preenche as lacunas nem supõe a cadência do
arremesso. Um teste de navegador sem interface verificou o carregamento das
19 amostras e a troca da seleção.

## Lateral inferior: experimento controlado

O cenário 5 da ROM é o único cenário original identificado que começa com
lateral. Para observar a outra borda sem alterar a ROM, o experimento
`tools/capture_issd_throwin_opposite_experiment.lua` executou esse cenário e
interceptou a inicialização em `$86:D200`. Alterou somente na memória do
emulador o valor de Y do reinício de `$FFFF` para `$02C1`: uma unidade além
da largura `$02C0` do estádio 2. Essa posição é sintética; a movimentação,
as poses e o arremesso subsequentes foram executados pelo jogo original. O
estado e os arquivos gráficos resultantes permanecem locais em `analysis/`.

A imagem da execução mostra o jogador de costas na borda inferior. Nos quatro
comandos direcionais foram obtidos 46 quadros de corpo com comparação exata
ao emulador: 14, 2, 15 e 15 para cima, baixo, esquerda e direita. Foram
excluídos 53 quadros com divergências de pixel e 21 sem eventos completos de
desenho; a causa das divergências ainda não foi provada. Os descritores
validados incluem `$A980`, `$A989`, `$A9AD` e `$A9B6`.

A galeria ganhou sete amostras individuais da lateral inferior, totalizando
26 entre as duas bordas. Como antes, são corpos isolados, sem bola ou cabelo,
e não uma animação completa. Para regenerar ambas as bordas, acrescente
`--lower-captures analysis/throw-in-lower-directions` ao comando de exportação
acima. A validação em navegador confirmou o carregamento e a seleção da
amostra inferior. As poses em que a bola ou outras camadas possam interagir
ainda precisam de análise antes da reconstrução integral.

## Bola como objeto separado na lateral inferior

Nos quadros anteriormente divergentes das execuções inferior/cima, esquerda
e direita, o evento de desenho identificou o objeto `$0400` (bola) antes do
cobrador `$0600`. Ao compor os slots OAM dos dois objetos na ordem capturada,
30 quadros adicionais coincidiram integralmente com a imagem original. A
geometria e os atributos do corpo foram comparados à ROM e à OAM, mas pixels
do corpo encobertos pela bola não são diretamente verificáveis na tela.

A opção `--validate-ball-overlay` do auditor realiza essa comparação conjunta
e continua descartando quadros divergentes. Os 23 quadros divergentes da
execução com comando para baixo permanecem pendentes: apenas a sobreposição
da bola não explica a imagem. A galeria agora contém 34 amostras individuais,
incluindo nove da borda inferior em que a bola foi validada sobre o jogador.
Não se trata ainda de uma sequência animada completa nem de validação de
cabelo, outros uniformes ou física.

O teste em navegador verificou uma pose da borda inferior com bola; um teste
do auditor verificou que a opção recupera 10 quadros em cima mantendo fora
os demais divergentes. Todas as imagens geradas seguem locais e ignoradas.

## Prévia de trecho contínuo no laboratório

A partir das capturas já auditadas, foram exportados dois trechos contínuos
de 20 quadros preparados consecutivos, 2267–2286, a 60 quadros por segundo:
a cobrança da borda superior com entrada `Down` e a experiência da borda
inferior com entrada `Left`. Cada quadro é revalidado contra ROM, OAM e tela
antes da exportação; o exportador rejeita qualquer intervalo que contenha
quadro ausente ou divergente. A âncora de apresentação usa a posição de
desenho capturada do ator para manter os quadros alinhados.

O laboratório permite alternar a borda, pausar e selecionar um quadro. É
apenas o trecho observado: a preparação completa, cabelo e trajetória da
bola após deixar as mãos não estão incluídos. A bola aparece apenas quando
sua sobreposição foi validada com o corpo. A reprodução em loop é uma escolha
de apresentação do laboratório, não uma afirmação sobre o ciclo do jogo.
A borda inferior continua sendo proveniente do experimento sintético de
posicionamento descrito acima.

Para reconstruir os dados locais, execute para cada captura:

```sh
python tools/export_issd_throwin_excerpt.py --capture analysis/throw-in-lower-directions/Left --rom "caminho/para/rom.sfc" --output dist/assets/issd/slide-lab-local/throwin-excerpt/lower --first 2267 --last 2286
python tools/export_issd_throwin_excerpt.py --capture analysis/throw-in-body-directions/Down --rom "caminho/para/rom.sfc" --output dist/assets/issd/slide-lab-local/throwin-excerpt/upper --first 2267 --last 2286
```

Teste negativo confirmou rejeição de intervalo contendo lacuna; teste de
navegador confirmou carregamento, pausa, seleção do quadro e troca de borda.
Os PNGs gerados continuam locais e não são versionados.

## Bola nos trechos contínuos

A limitação da seção anterior sobre ausência da trajetória da bola foi
superada para os dois trechos de 20 quadros. O exportador agora identifica
o objeto `$0400` em cada lista de desenho, obtém seus slots OAM e compõe
bola e jogador na ordem capturada. A composição conjunta deve coincidir
com a imagem original em cada quadro; a exportação falha se a bola estiver
ausente, se faltar a lista de desenho ou houver divergência de pixels.

As prévias usam uma área de 160×128 pixels alinhada à origem capturada do
jogador para comportar o deslocamento observado da bola. Essa apresentação
reproduz apenas os quadros capturados, sem extrapolar a trajetória nem
comprovar a física de voo, a recepção ou o restante da cobrança. O cenário
da borda inferior continua sendo o experimento sintético documentado acima.

A exportação foi reexecutada para as duas bordas: 20 composições validadas
em cada uma. Testes verificaram a presença da bola em todos os quadros e
carregaram as duas prévias no navegador. Os gráficos continuam locais.

## Vetor horizontal da soltura

Novas reexecuções instrumentaram `CODE_85EF51`, `CODE_85F8B9` e as rotinas
de vetor `$83:9E32`, `$83:9E92`, `$83:9EC3` e `$83:953F`. O controle sem
botão não chamou a rotina de lançamento na janela capturada. Para seis
combinações de botão e direcional, o produto dos coeficientes em `$81:A5D7`
pela magnitude e a correção de sinal coincidiram com as palavras 16.16
gravadas na bola. Os casos e hashes dos traços estão em
[issd-throwin-vector-audit.json](issd-throwin-vector-audit.json).

Neste cenário, o caminho acionado por A utilizou magnitude nativa 64 e tipo
de bola 20; o caminho B utilizou 56 e tipo 15. Para os ângulos observados,
os coeficientes lidos da tabela foram: 3 → `(3951,1196)`, 8 → `(1992,1992)`,
13 → `(597,1907)` e 30 → `(2899,579)`. A função
`dist/native-throwin-vector.mjs` reproduz somente os seis pares observados,
incluindo sinal e fração; entradas não verificadas retornam `null`. As
coordenadas nativas ainda não foram convertidas à escala do navegador e a
função **não está ligada à partida**.

Essa medição não estabelece a velocidade vertical, o quique, a escolha do
recebedor nem uma regra geral para todas as direções, lados, jogadores ou
condições. O cenário testado foi o original da lateral superior.
`tools/capture_issd_throwin_release.lua` permite repetir os hooks nessa mesma
janela de replay e `tools/audit_issd_throwin_vectors.py` verifica a ROM e os
seis traços; os arquivos brutos continuam locais. Testes automatizados cobrem
os seis vetores e rejeitam casos não observados.

## Altura e impactos em replays prolongados

Foram executados seis replays de 400 quadros: quatro do cenário superior
original e dois da borda inferior sintética, com A e B. O coletor agora
registra as palavras inteiras e fracionárias de posição e velocidade da bola;
o tamanho é configurável por `ISSD_THROW_FRAMES` (150 por padrão, máximo
1800). Os traços e estados seguem locais.

A auditoria [issd-throwin-flight-audit.json](issd-throwin-flight-audit.json)
identificou 241 transições contínuas em voo em que a velocidade vertical
recebe `$0000:2000` e a posição é atualizada com a nova velocidade. Três
impactos observados corresponderam a dois estados verticais distintos:
no tipo 20, `FFFF:8000 / 0003:A000` passou a `0000:0000 / FFFE:2000`;
no tipo 15, `0000:4000 / 0002:E000` passou a `0000:0000 / FFFE:8000`.
Os pares indicam posição Z e velocidade Z, respectivamente. São exemplos
medidos, não uma lei geral de colisão.

`dist/native-throwin-flight.mjs` utiliza a operação nativa de voo já existente
e reproduz apenas os dois impactos exatos, retornando `null` para outros
impactos. Uma verificação percorreu os seis traços e comparou os 241 passos
de voo e os três impactos à implementação. Mudanças posteriores no vínculo
`$00A6` foram observadas, mas não provam sozinhas quem recebeu a bola nem
a regra de recepção.

A conversão ao navegador continua pendente: `dist/native-field.mjs` usa
proporções do estádio e uma escala de Canvas expressamente provisória;
ela ainda não valida velocidades ou eixo Z. Portanto, os novos cálculos
ainda não foram conectados à partida, e não são uma física web completa.
É necessário verificar contato/recepção e relacionar posição e velocidade
nativas à projeção e ao campo web antes da integração fiel.
