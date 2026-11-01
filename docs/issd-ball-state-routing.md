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
| `$00D8` | `84:8FA8` | `84:8FA8` | `84:C2E6` | `$8122` |
| `$00E0` | `84:9047` | `84:9047` | `84:C306` | `$8127` |
| `$00E8` | `84:90C0` | `84:90C0` | `84:C315` | `$8322` |

Não atribuímos significado humano/CPU às colunas sem rastrear o dispatcher.
As seis entradas foram conferidas byte a byte na ROM USA, nos offsets LoROM
`00BE10/00BE18/00BE20/00BE30/00BE38/00BE40`, sem header. Extrator:
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
locais de `$00AC/$00AE` convergem para `83:953F`,
onde `PLX; RTL` restaura X. Após o retorno, `85:F8D6..F91B` não escreve X,
restaura DP com `TXA` seguido de `TCD` e retorna carry limpo.

Assim, nos caminhos normais de retorno dessas rotinas, `85:ECC3` pode
gravar X em `$00A6` após `JSL 85:F8B9`, restaurando o vínculo com o ator
chamador. O handler indireto chamado por `83:956E` é tratado pelo contrato
normal de retorno e pilha; não foi feita prova formal de todos os seus destinos.
Isso sustenta o vínculo neste caminho, não a equivalência universal
`$00A6 = posse` em todos os estados do jogo.

## Testes, limites e retomada

Executados: comparação das seis entradas com a ROM original; testes de
header ausente/presente (512 bytes) e rejeição de divergência; auditoria da
documentação. Nenhuma alteração da ROM ou física web.

Próximo passo: rastrear a seleção entre `+$90/+$92/+$94`, recuperar os outros
handlers desses três estados e o desvio `84:8F6A`. Só depois definir quais
caminhos são comuns ao humano e à CPU e qual vínculo realmente libera a bola.
Não é necessário pedir nova captura para essa investigação estática.

## Continuação: dispatch e estado D8

Os destinos indiretos das colunas estão localizados:

| Campo do ator | Dispatcher | Evidência |
| --- | --- | --- |
| `+$90` | `84:8739` | `TDC; TAX; JMP ($0090,X)` |
| `+$92` | `84:BD0A` | `TDC; TAX; JMP ($0092,X)` |
| `+$94` | `84:C25E` | `TDC; TAX; JMP ($0094,X)` após ajuste de flags |

Não são três categorias mutuamente exclusivas humano/CPU. Em `84:86F6`,
o caminho que normalmente termina em `8739` pode desviar para `BD0A` quando
`$00D0` é não zero ou por condições de flags e contador locais.

Em `84:8056`, o sinal de `+$2E` do registro de controle escolhe duas rotas.
Na rota não negativa, `8064/8073` lê os símbolos de botões pressionados e
mantidos (`RAM_ISSD_Global_PressedButtonsLoP1/HeldButtonsLoP1`), escreve
`+$14/+$12` do registro e entra em `848571` com DP do ator. Na rota negativa,
`8096` zera esses campos e entra em `84:C197`, que pode chegar ao dispatcher
de `+$94`. Isso distingue entrada física de outra rota de controle; o escritor
do bit de sinal ainda precisa ser rastreado para rotular todos os modos.

### 8F6A não prova liberação

`84:8F6A` limpa bit `$0010` de `+$9E`, chama `80:DFD9`, seleciona script
`82:CF9F` e `82:E34A`, inicializa `+$74=$10`, copia byte baixo de `+$66`
para `+$72`, chama cálculo de movimento `80:DDBE` com Y=`$22` e inicializa
os deslocamentos por `80:DEA5`. Finalmente instala `$00D8`.

O handler `8FA8` continua consultando direção e interseção `+$12,X & +$1C,X`.
Enquanto segue pelo ramo `8FD3`, chama **`80:DF00`**, mantendo a bola relativa
ao ator. Portanto não há evidência de chute/passe apenas por entrar em D8.
Não há limpeza direta de `$00A6` no trecho de entrada `8F6A..8FA5`.

O terceiro handler de C0, `84:C2AC`, chama `C456` para atualizar parâmetros,
compara `+$84` com a direção e, quando coincidem, testa o sinal de `+$54`:
negativo → `8F6A`; não negativo → `DF00` e `E683`. O handler de controle
`8ECD` chega ao mesmo `8F6A` por interseção dos campos de botão. As duas
rotas convergem na mesma inicialização; não são prova de velocidades iguais
em todos os contextos, pois os parâmetros e atributos ainda variam.

Ao deixar de cumprir os testes iniciais de D8, `8FA5` encaminha `84909D`,
que prepara `82:CEF8`, usa Y=`$1E` em `80:DDC6`, contador `$10` e estado
`$00E8`. O término completo de E8 ainda não foi classificado.

**Retomada atualizada:** rastrear o escritor do sinal do registro de controle,
os estados E0/E8 e os pontos que realmente limpam `$00A6` ou transferem
movimento à bola. Não interpretar a transição C0→D8 como liberação.
Nenhum parâmetro do navegador foi alterado nesta continuação.

### Continuação posterior: liberação e modos confirmados

[issd-ball-release-and-runtime-validation.md](issd-ball-release-and-runtime-validation.md)
fecha a inicialização do sinal dos controles nos nove modos, rastreia a
liberação `85:F3CC → 85:F8C5 → 83:94A4` e compara as tabelas com 18.000
frames já capturados. Esse documento contém o ponto de retomada atualizado.
