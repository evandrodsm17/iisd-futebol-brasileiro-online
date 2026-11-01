# Roteamento dos estados de bola relativa ao ator — 01/11/2026

## Contrato recuperado

`84:854E` grava o valor de A em `+$32` e o usa como **offset em bytes**
da tabela `81:BD58`. Copia as quatro palavras da entrada para
`+$90/+$92/+$94/+$60`. Portanto `$00B8/$00C0/$00C8` não são índices
consecutivos: são offsets de entradas de oito bytes.

| Estado | Handler 0 | Handler 1 | Handler 2 | Flags |
| --- | --- | --- | --- | --- |
| `$00B8` | `84:8E1C` | `84:C13F` | `84:C26A` | `$0320` |
| `$00C0` | `84:8ECD` | `84:8ECD` | `84:C2AC` | `$8320` |
| `$00C8` | `84:8E8E` | `84:8E8E` | `84:C293` | `$0320` |

Não atribuímos significado humano/CPU às colunas sem rastrear o dispatcher.
As três entradas foram conferidas byte a byte na ROM USA, nos offsets LoROM
`00BE10/00BE18/00BE20`, sem header. Extrator:
`tools/extract_issd_ball_states.py`; manifesto:
`dist/data/issd-ball-state-routing.json`, contendo hash e trechos originais.

## Entrada, direção estável e giro

`84:8DD1` compara a página direta com o absoluto `$00A6`. Se diferentes,
vai para `84:878A`; se iguais, testa `$00D0`. Quando `$00D0` não é zero,
limpa `$00A6` e também retorna a `878A`. Quando zero, segue `8DE9`, inicializa
`+$70=$0060` e instala estado `$00B8`, script `82:D320` e dado `82:E404`
com a transformação de bit mostrada no assembly.

No primeiro handler de `$00B8`, `84:8E1C`, `80:DD31` lê o controle apontado
pelo absoluto `$0088`. A palavra `+$13,X`, mascarada com `$000F`, é zero?
Retorna carry limpo. Caso contrário, traduz pela tabela `81:9613` e retorna
carry set. Isso prova um teste de direcional, não um botão de ação nomeado.

Sem direcional, `8E22` exige novamente `DP == $00A6` e chama `80:DE3D`:
bola = posição do ator + par direcional de `81:97C2`. Com direcional igual
ao `+$2E`, `8E3D` segue `8EA9/8EB2`: seleciona `82:CEF8/82:E34A`,
inicializa os deslocamentos em `80:DEA5`, chama `80:DDBE` com Y=`$001E`
e instala estado `$00C0`. O significado físico/unidade desse Y não é
promovido a velocidade Canvas.

Em `$00C0`, `8ECD` volta a testar direção. Sem direção, retorna `8DD1`.
Com direção, testa a interseção dos campos de controle `+$12,X` e `+$1C,X`;
se não zero, desvia para `8F6A` (ação ainda não nomeada). Se zero e direção
igual, chama `80:DF00` (oito fases de posição da bola), depois `84:E683`
(timer de animação separado). Logo, fase de deslocamento da bola e cursor
de sprite não são automaticamente o mesmo contador.

Na mudança de direção, `8E58` instala `$00C8`, contador 4 e escolhe
`+$78=+1/-1` pela tabela `81:9629`. Seu handler `8E8E` chama `80:DE6D`
para mover a bola na trajetória de giro; ao zerar o contador, ajusta a direção
por `80:DD47` e reavalia o controle. A sequência completa de mudanças e os
outros handlers ainda precisam ser recuperados.

## Preservação do ator em 85:F8B9

`85:F8C5` copia DP para X (`TDC; TAX`). `F8D6` limpa `$00A6`, muda DP para
zero e chama `83:94A4`. Essa rotina guarda X com `PHX` em `94B9`; os caminhos
locais de `$00AC/$00AE` convergem para `95:3F` **no banco 83** (`83:953F`),
onde `PLX; RTL` restaura X. Após o retorno, `85:F8D6..F91B` não escreve X,
restaura DP com `TXA` seguido de `TCD` e retorna carry limpo.

Assim, nos caminhos normais de retorno dessas rotinas, `85:ECC3` pode
gravar X em `$00A6` após `JSL 85:F8B9`, restaurando o vínculo com o ator
chamador. O handler indireto chamado por `83:956E` é tratado pelo contrato
normal de retorno e pilha; não foi feita prova formal de todos os seus destinos.
Isso sustenta o vínculo neste caminho, não a equivalência universal
`$00A6 = posse` em todos os estados do jogo.

## Testes, limites e retomada

Executados: comparação das três entradas com a ROM original; testes de
header ausente/presente (512 bytes) e rejeição de divergência; auditoria da
documentação. Nenhuma alteração da ROM ou física web.

Próximo passo: rastrear a seleção entre `+$90/+$92/+$94`, recuperar os outros
handlers desses três estados e o desvio `84:8F6A`. Só depois definir quais
caminhos são comuns ao humano e à CPU e qual vínculo realmente libera a bola.
Não é necessário pedir nova captura para essa investigação estática.
