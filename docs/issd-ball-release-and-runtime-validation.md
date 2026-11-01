# Liberação da bola e validação com captura existente — 01/11/2026

## Resultado e escopo

Foram verificadas 16 tabelas diretamente na ROM USA e seis entradas de estado.
Uma captura existente de 18.000 frames foi reprocessada com coordenadas
compatíveis. Isso fornece evidência estática de um caminho de liberação e
evidência dinâmica de deslocamentos da condução. Não é uma reprodução completa
da física e não altera constantes do navegador.

Artefatos:

- `dist/data/issd-ball-release.json`: tabelas verificadas, nove modos de controle,
  oito combinações direcionais da liberação, trechos de assembly e SHA-256.
- `dist/data/issd-ball-state-routing.json`: entradas B8/C0/C8/D8/E0/E8.
- `docs/issd-ball-attachment-observations.json`: resultados da captura,
  offsets observados por estado/direção, transições, hashes e limitações.

## Rota comprovada de liberação

No caminho `84:9017`, o jogo chama `85:F3CC`, depois `84:8548`, que soma
oito ao estado local. Quando parte de D8, chega a E0. Há também entrada
`84:901E`, que chama a mesma rotina e instala E0 por `9022/902A`.

`85:F3CC` chama `F3E6`, lê o byte de `81:DAFE` indexado pela direção
`+$2E` e segue para `F3D4`. Este mascara o byte para Y, lê `81:9632` para
A e passa **X=7** a `85:F8C5`.

`85:F8C5` guarda 7 em `$0000/$12F4`, guarda A em `$0002`, copia a página
direta do ator para X e segue `F8D6`, que zera **`$00A4` e `$00A6`**.
Com DP zero, chama `83:94A4`. Esta rotina:

1. Grava o ângulo de seis bits em `$0452`.
2. Quando `$00BA=0` e X não é `$0400`, registra X em `$045C`.
3. Mascara Y para quatro bits e limita valores >=12 a 11, gravando `$0456`.
4. Copia o tipo anterior `$0430` para `$0474` se não zero e grava o tipo 7
   em `$0430/$0476`.
5. Lê `81:A367[tipo*16 + parâmetro]` para `$0464`.
6. No ramo `$00AC=$00AE=0`, chama `83:9E32`, que usa o multiplicador Mode 7,
   e transfere os resultados às palavras `$0422/$0424/$0426/$0428` da bola.
   Os ramos alternativos vão a `83:D322/83:D2EE`; não são tratados como
   equivalentes sem análise adicional.
7. O handler do tipo 7, na tabela `83:957D`, é `83:9755`, que escreve
   `$0436=$FFFF`, `$0434=$8000` e `$0454=2`.

Ao retornar a `85:F3D4`, `STX $00A4` guarda o ator de origem. Este caminho
não repõe `$00A6`: há separação comprovada entre vínculo do ator e movimento
da bola. `$00A4` aqui é referência após a liberação, não posse universal.
O nome esportivo exato da ação (por exemplo, toque adiantado) ainda não está
confirmado por referência visual. Não chamá-la automaticamente de passe/chute.

| Direção nativa | `$0452` | `$0456` | `$0464` |
| --- | --- | --- | --- |
| 0 | 0 | 11 | 120 |
| 1 | 4 | 11 | 120 |
| 2 | 8 | 3 | 88 |
| 3 | 24 | 3 | 88 |
| 4 | 32 | 11 | 120 |
| 5 | 36 | 11 | 120 |
| 6 | 40 | 3 | 88 |
| 7 | 56 | 3 | 88 |

`$0464` é um parâmetro nativo para o cálculo, **não velocidade Canvas**.
Fontes: `81:9632` (offset `009632`), `81:DAFE` (`00DAFE`) e a linha 7 de
`81:A367` (`00A3D7`). `85:F3E6` também escolhe Y=`$1D` para os valores de
clima 0/1 e `$27` para os demais, mas entrega-o a `80:D5D3`; isso não prova
que clima altere a velocidade desta liberação.

## Modos de controle fechados estaticamente

`83:8080` lê o setting de número de jogadores, indexa `81:9BA7` e percorre
pares de palavras até um terminador zero. Os registros começam em `$1AA0`,
com passo `$30`. Se a primeira palavra tem bit `$8000`, ele é removido do
valor armazenado em `+$00`, e o bit `$8000` é escrito em `+$2E` do controle.
`84:8056` consulta exatamente esse sinal: a rota negativa zera botões e
chama `84:C197`; a positiva lê botões físicos e chama `84:8571`.

Os nomes de modos abaixo vêm de `Misc_Defines_ISSD.asm`, linhas 110–118;
os pares de palavras foram confrontados com a ROM, sem presumir papéis a
partir de uma coluna do dispatcher.

| Modos | Definição | Registros automatizados |
| --- | --- | --- |
| 0–3 | 1/12/123/1234 × CPU | Último registro; anteriores físicos |
| 4–7 | 1×2, 13×2, 13×24, 134×2 | Nenhum |
| 8 | CPU × CPU | Ambos |

`81:9BA7` está no offset `009BA7`; os nove blocos ficam de `009BB9` a
`009C35`. Valores-fonte como `dw $7ED57A` são truncados a 16 bits pelo
assembly; o extrator reproduz isso e verifica os bytes, não interpreta
essas diretivas como endereços de jogador. O seletor de lado usa a segunda
palavra; o bit `$4000` do registro recebe ainda um bit de `$0DE0/$0EE0`.

## Condições após a liberação e diferenças entre handlers

O handler automatizado de E0, `84:C306`, consulta `$00B6`, chama `80:F1E3`
e `84:C456`, depois entra no mesmo `84:905B` usado pela rota física.
Nesse trecho compartilhado, seguir para `84:8FD7` exige:

- `$00C0=0` e a página direta do ator igual a `$00C8`;
- ator igual a `$00A4` (referência registrada após liberar);
- `$046C < $40` em comparação sem sinal;
- carry set no teste angular `80:F402`.

Se as condições não forem atendidas, há caminhos para `84:9072`, que zera
`$00A4` e vai a `848905`, ou o desvio condicionado para `84:A736`.
Os significados de `$046C` e `$11F9` não são inferidos aqui.

`80:F46D` obtém a direção relativa à bola e a grava em `+$7E` antes do
teste. `80:F402` calcula `r = (7E - DATA_819491[2E]) & $3F` e executa
`CMP #$20`: o ramo permitido em `849078` é `r >= 32`. A tabela verificada
no offset `009491` é `16,20,24,40,48,52,56,72`. Essa condição é angular;
não é um limiar de distância, nem prova uma retomada imediata de posse.

O caminho `8FD7` usa `80:DD9F`: decrementa `+$72`; enquanto não negativo,
retorna carry set. Quando negativo, só incrementa `+$64` se este for menor
que `+$62`, recarregando `+$72` com byte baixo de `+$66`. Retorna carry
limpo e o novo `+$64`, ao qual o chamador soma `$22` antes de `80:DDBE`.
Isso recupera uma progressão parametrizada de movimento, sem atribuir
unidades ou significado de atributo a `$62/$66` nesta etapa.

**E8 não tem temporização idêntica nas duas rotas.** A entrada `8490A1`
inicializa `+$72=16` e `+$74=0`. O handler físico `8490C0` decrementa
`+$72`, testa direção e pode reentrar em D8; ao zerar o contador escolhe
`8EB2` ou `8DD1`. O handler automatizado `84:C315` incrementa `+$74` e,
quando igual a 6, vai a `8DD1`; nas demais chamadas segue `8490EC` para
`DF00/E683`. Não converter essas contagens em segundos sem confirmar a
frequência de execução, nem concluir vantagem de velocidade da CPU.

## Validação dinâmica existente

Entrada: `docs/issd-motion-constraints-20261029-113515.jsonl`, 18.000 frames.
O coletor original preserva `$0408/$040C` e `+$08/+$0C` dos 22 atores,
com estado e direção. O analisador subtrai palavras com wrap de 16 bits.
Não usa as coordenadas derivadas `+$2A/+$2C` nem escolhe um portador.

| Estado | Amostras de ator | Coincidências com ciclo de 8 fases | Coincidências com trajetória de giro |
| --- | ---: | ---: | ---: |
| B8 | 56 | 32 | 18 |
| C0 | 2.025 | 1.933 | 240 |
| C8 | 929 | 154 | 796 |
| D0 | 111 | 21 | 77 |
| D8 | 1.948 | 1.848 | 283 |
| E0 | 2.823 | 154 | 0 |
| E8 | 284 | 284 | 0 |

As colunas podem se sobrepor: não são uma classificação exclusiva.
O ciclo usa `81:9842` e oito seletores a partir de `81:9623`, atravessando
os dois primeiros bytes do próximo rótulo `81:9629`. Bits `$80/$40`
invertem X/Y. A trajetória usa os 16 pares de `81:9802` e suas negações,
32 candidatos. Não foi inferida fase exata apenas pela coincidência do par.

Separando frames consecutivos com mesmo estado e direção, C8 tem 666/697
pares da trajetória de giro e apenas 2/697 do ciclo. E8 tem 236/236 pares
do ciclo. Isso é compatível com os handlers recuperados. B8 não apresenta
nenhuma amostra consecutiva estável nesse critério; as oito coincidências
com a tabela fixa de B8 não bastam para validar seu comportamento completo.

Há 102 transições D8→E0 entre frames consecutivos do mesmo ator. Isso é
consistente com o caminho estático, mas **não comprova o instante de liberação**:
a captura antiga não tem `$00A6`, tipo da bola ou timers de deslocamento.
As divergências restantes não foram descartadas nem explicadas por hipótese.

## Instrumentação preparada, sem nova sessão manual

`capture_issd_motion_constraints.lua` passa ao schema 2 e acrescenta
`$00A4/$00A6`, altura, tipo, palavras de velocidade e parâmetros da bola;
nos atores, fase/timers/deslocamentos/direção-alvo; nos cinco registros
possíveis de controle, botões, ator e flags. Mantém os campos anteriores,
nome único, 30 segundos de preparação e cinco minutos de captura.
Essa alteração **ainda não foi executada no BizHawk**. Nada foi iniciado na tela.

## Reprodução e testes

```powershell
python tools/extract_issd_ball_release.py "International Superstar Soccer Deluxe/International Superstar Soccer Deluxe (USA).sfc"
python tools/extract_issd_ball_states.py "International Superstar Soccer Deluxe/International Superstar Soccer Deluxe (USA).sfc"
python tools/analyze_issd_ball_attachment_trace.py docs/issd-motion-constraints-20261029-113515.jsonl "International Superstar Soccer Deluxe/International Superstar Soccer Deluxe (USA).sfc" --output docs/issd-ball-attachment-observations.json
python -m unittest discover -s tools -p "test_ball_*.py" -v
python tools/verify_issd_documentation.py
```

Testes cobrem sinais e espelhamento, diferenças com wrap, exclusão de
transições entre frames não consecutivos, frames duplicados, header de
512 bytes, truncamento de diretivas `dw`, roteamento dos nove modos e
rejeição de alteração de byte da ROM. Os testes que precisam da cópia local
são marcados como ignorados quando ROM/disassembly não estão disponíveis.

## Próximo passo ao retomar

### Tabelas de deslocamento e volume dos caminhos F438/F617

Conferidas byte a byte na ROM local duas tabelas usadas juntas por
`85:F438` e `85:F617`: `81:CEF6` (offset LoROM `00CEF6`) contém os bytes
`08 00 05 02 00 04 05 02 00`; `81:CF47` (`00CF47`) contém as palavras
`0018,0030,0010,0020,0008,0010`. Os valores brutos estão no manifesto
`dist/data/issd-contact-volume.json`, regenerado por
`python tools/issd_contact_volume.py <caminho-da-ROM>`.

Nos dois caminhos, `85:FA91` recebe Y=`81:CEF6` e `85:FAF1` recebe
Y=`81:CF47`. Em `F438`, igualdade da página direta com `$00A4` ou `$00A6`
desvia diretamente para a escrita do bit `$0400`, sem executar esse volume;
se não houver igualdade e `$00A6` não for zero, retorna carry set. Em
`F617` há ainda teste inicial do bit `$0400`. Estes ramos não devem ser
ignorados quando o volume for integrado: uma avaliação geométrica isolada
não representa o caminho completo.

Os seis testes de `test_issd_contact_volume.py` e a verificação das tabelas
passaram com a ROM de referência. A captura disponível não registra todos
os campos intermediários, e o teste ainda não foi comparado à execução do
processador. Nenhuma mudança foi feita na mecânica web. Próximo passo:
modelar os ramos de `F438/F617`, preservando a diferença entre eles, e
validá-los com evidência de execução antes da integração.

### Testes de volume e condições auxiliares

`85:FAEA` recusa com carry set se o bit `$0400` de `+$6E` estiver ativo;
em seguida `85:FAF1` também recusa se `$00C0 != 0` ou se `$11FA` for
negativo. Caso contrário, testa três eixos relativos à bola: altura usa
`+$10`, `+$3C` e `$0410`; os outros usam `+$08/+$38/$0408` e
`+$0C/+$3A/$040C`. Y aponta para seis palavras consecutivas, duas por
eixo. Se algum teste terminar com carry set, retorna por `85:FB36`; se os
três terminarem com carry limpo, define `$0400` em `+$6E` e retorna.

Cada eixo usa a sequência de instruções `CLC; ADC; CLC; ADC; SBC; SEC;
SBC`. O primeiro `SBC` consome o carry do `ADC` anterior; não pode ser
substituído por uma comparação geométrica comum sem preservar o carry e
wrap de 16 bits. Isso é relevante para reconstrução e testes de borda.
`81:CF5F` contém `0010,0020,0010,0020,0010,0020`; `81:CF83` contém
`0010,0020,0010,0020,001C,0038`. São parâmetros brutos, não metros.

`85:FA91` prepara `+$38/+$3A/+$3C`: lê um byte assinado do registro em Y,
seleciona dois bytes via tabela de direção `81:9623`, e aplica inversões
conforme bits da seleção. O caminho que inicializa esses campos deve ser
confirmado para cada chamada a `FAEA/FAF1` antes de simular o volume.

`80:D985` escolhe zero ou `$12A2` conforme bit baixo de `+$6E` e aplica
dois testes com limites `$0180/$0300` e `$00C0/$0180`, usando `+$2A/+$2C`
e `$12D8`. Também preserva carry entre o primeiro ADC e SBC. Não há prova
de que seja, isoladamente, um teste de impedimento ou de área.

`85:FB37` combina uma saída mascarada de `80:E8AD`, `$12DA`, uma tabela
de ponteiros `81:DB82` selecionada por `+$E2` do registro em `+$9A`, e
bits baixos de `$0078`; retorna um byte da tabela. O resultado alimenta os
desvios de `85:EC25`. Não se deve chamá-lo de probabilidade de desarme sem
resolver seus insumos e a tabela efetivamente selecionada.

Fontes: `Routine_Macros_ISSD.asm`, `85:FA91..FB70`, `80:D985..D9AD` e
`81:CF5F/CF83`. Valores foram lidos da disassembly; ainda falta conferi-los
contra bytes da ROM e construir testes de borda antes de aplicá-los ao jogo.

**Continuação:** `tools/issd_contact_volume.py` agora confere as duas tabelas
contra a ROM local e publica `dist/data/issd-contact-volume.json`, com hash da
ROM e limitações. A função `axis_carry` reproduz a sequência aritmética de um
eixo com wrap de 16 bits. `tools/test_issd_contact_volume.py` testa limites,
carry do segundo ADC, ROM com e sem header e rejeição de byte alterado.
Os testes verificam alguns casos de borda, não uma comparação exaustiva com
o processador em execução. Falta integrar os três eixos e seus gates com o
contexto correto antes de considerar uma aplicação na partida web.

**Modelo integrado:** `contact_volume` em `tools/issd_contact_volume.py`
agora executa os gates de `85:FAEA/FAF1` e testa altura, X e Y nessa ordem,
retornando o carry e uma cópia atualizada dos flags do ator. Os dados de
entrada são palavras brutas de 16 bits; a função não escreve na memória.
O gate anterior de `85:FAE5` para `$00A6` não está incluído, pois depende
do ponto de entrada. Quatro testes cobrem rejeição em cada eixo, gates,
carry, entrada inválida e correspondência das tabelas com a ROM. O modelo
ainda não foi comparado contra execução do processador e não foi ligado ao
motor web; deslocamentos e seleção do ponto de entrada continuam necessários.

**Correção e avanço posteriores:** existem chamadas diretas a `85:FAF1`
que não passam pelo gate `+$6E & $0400` de `85:FAEA`. O modelo anterior
aplicava esse gate a todas as chamadas; agora exige a seleção explícita
entre `FAE5`, `FAEA` e `FAF1`, mantendo `FAEA` como padrão. `FAE5` também
testa `$00A6`, `FAEA` testa o bit `$0400`, e `FAF1` começa nos gates de
fase e `$11FA`. Por exemplo, `85:F438` prepara os deslocamentos com
`85:FA91` e chama `FAF1` diretamente. `85:F617` também usa esse caminho,
mas executa seu próprio teste de `+$6E` antes da chamada.

`prepare_offsets` modela a leitura dos bytes assinados de `85:FA91`,
índice direcional e inversões dos eixos. Testes sintéticos cobrem os quatro
casos de espelhamento, extensão de sinal e os três pontos de entrada.
As seis verificações automatizadas passam. A seleção das tabelas e a
execução do processador no contexto original continuam não validadas; as
funções permanecem isoladas da partida web.

### Continuação: substituição do vínculo existente

Em `85:EC98`, o código lê o antigo `$00A6` em X. Se for zero, segue
diretamente a `85:ECC3`. Se não for zero, compara o campo `+$9A` do ator
antigo com o `+$9A` do ator atual. Quando iguais, troca temporariamente a
página direta para o ator antigo e chama `85:854E` com A=`$0008`. Quando
diferentes, aplica `$0200` ao campo `+$6E` do ator antigo, grava `$8002`
em seu `+$78` e grava a página direta do ator atual em seu `+$76`.

Depois, `85:ECC3` chama `85:F8B9` com X=`$000E` e grava X retornado em
`$00A6`; a preservação de X como ator atual nesse caminho está documentada
em [issd-ball-state-routing.md](issd-ball-state-routing.md). Portanto o
vínculo é substituído após tratamento condicional do ator anterior. A
comparação de `+$9A` indica igualdade de referência, mas sua interpretação
como posse, roubo ou falta exige rastrear os chamadores e o contexto.

Outros caminhos: `85:EE94` usa igualmente tipo `$000E` e repõe `$00A6`;
`85:EEC3` usa `F8C5` com tipo `$000E`, enquanto `85:EECE` usa tipo zero,
ambos restaurando o vínculo em `$00A6`. Estes trechos comprovam diferenças
de inicialização, não o nome esportivo de cada evento. Fonte:
`Routine_Macros_ISSD.asm`, rótulos `85:EC98`, `85:ECC3`, `85:EE94`,
`85:EEC3` e `85:EECE`. Nenhuma alteração ao motor web.

Próxima investigação: rastrear as condições anteriores a `85:EC4D/EC77`
e os consumidores dos campos escritos no ator anterior; correlacionar com
capturas que registrem `$00A6` antes de atribuir uma ação esportiva.

### Condições anteriores à atribuição — análise estática

`85:EC06` chama `85:ED3A`: carry set retorna imediatamente; com carry
limpo, chama `85:FAEA` com Y=`81:CF83`. Somente carry limpo nessa segunda
chamada leva a `85:EC4D`. Em `EC4D`, carry set de `80:D985` desvia para
`EC4A`; carry limpo prossegue até o tratamento de `$00A6` em `EC98`.
Antes dele, se o campo `+$C2` do registro apontado por `+$88` for menor
que `$0080`, o código grava `$4000` ou `$2000` em `$19D2` conforme o sinal
de `$0078`. Não foi atribuído significado esportivo a essas condições.

`85:EC15` começa com os mesmos testes `ED3A` e `FAEA`, mas o carry limpo
de `FAEA` leva a `EC25`. Ali, `DATA_81:DB50[$12DC]` é comparado com
`$046C`; um resultado menor desvia para `EC77`. Caso contrário, o caminho
testa `80:D985` e `85:FB37` antes de escolher `EC77`, `EC4A`, `ECE7` ou
retornar carry set. Em `EC77`, após uma chamada com DP temporariamente zero,
o fluxo segue a `EC98` e pode substituir o vínculo anterior.

O ramo `85:EE57` exige `$00A6=0` e carry limpo de `85:FAF1` com
`81:CF5F`. A partir daí, a tabela `81:DB1E`, `$046C`, o campo `+$E2`
da referência `+$9A`, `80:EE97` e o sinal de `$0078` escolhem entre
`EE94`, retorno com carry set e `ECE7`. `EE94` inicializa tipo `$000E`
e grava o ator retornado em `$00A6`.

Esses fatos são caminhos estáticos; as semânticas de `FAEA`, `FAF1`,
`D985`, `FB37` e dos limiares ainda não foram fechadas. Comparações e carry
não demonstram por si só desarme, interceptação ou recepção. Fontes:
`Routine_Macros_ISSD.asm`, rótulos `85:EC06..EC77` e `85:EE57..EE94`.
Próximo passo: recuperar os contratos dessas subrotinas e suas tabelas antes
de implementar uma transição de posse no navegador.

1. Rastrear os escritores de `$00A4/$00A6` em disputa da bola e o desvio
   `84:A736`; o filtro angular de E0 já está recuperado acima.
2. Fechar os ramos alternativos de `83:94A4` e a integração do tipo 7;
   preservar o contrato exato do multiplicador antes de converter unidades.
3. Usar futura captura schema 2 para ordem das fases, cadência e frame exato
   da liberação. Não é necessário repetir caminhada/corrida apenas para
   obter sprites: o objetivo desses campos é validar o vínculo e a física.
