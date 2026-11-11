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
