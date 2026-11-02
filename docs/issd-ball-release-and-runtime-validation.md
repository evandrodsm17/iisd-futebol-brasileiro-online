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

### Busca de correspondência com dumps OAM — 02/11/2026

`tools/audit_charge_graphics_overlap.py` comparou os descritores dos três
trechos de `docs/issd-charge-animation-runs.json` com os 135 registros de
`docs/issd-native-action-oam.jsonl`. **Nenhum descritor coincidiu nessa
coleção específica.** O resultado e hash do índice estão em
`docs/issd-charge-graphics-overlap.json`.

Isso não prova que não existam imagens ou capturas correspondentes em
outras coleções. Mesmo uma coincidência de descritor exigiria verificar
frame, ator, VRAM, paleta e agrupamento OAM antes de validar a montagem.
O teste `test_charge_graphics_overlap.py` cobre a detecção de coincidência
e arquivos ausentes; auditoria documental passou. Nenhum asset foi removido,
gerado ou incorporado ao jogo nesta investigação. Próximo passo: examinar
outros índices e dumps disponíveis, sem solicitar nova sessão manual enquanto
houver evidências locais a processar.

### Sequências individuais observadas — 02/11/2026

`tools/report_charge_animation_sequences.py` separou trechos por ator,
interrompendo o trecho quando o ator some, muda de estado/script ou há
lacuna na amostragem. `docs/issd-charge-animation-runs.json` preserva os
frames e descritores sem completar poses intermediárias:

| Ator | Frames amostrados | Direção nativa | Descritores distintos observados |
| --- | --- | --- | --- |
| `$1800` | 1764–1778 | 4 | A749, A752, A75B, A764, A76D |
| `$1100` | 8446–8456 | 7 | A701, A70A, A713, A71C |
| `$1800` | 10810–10824 | 4 | A749, A752, A75B, A764, A76D |

O trace registra uma amostra a cada dois frames; não é possível afirmar
que os descritores acima sejam todas as poses executadas ou determinar
o frame exato de cada troca. A captura analisada não contém os campos de
cursor e timers esperados pelo relatório; eles aparecem como `null`, sem
valores inventados. Também não foram pareados VRAM/CGRAM/OAM por frame,
logo esta etapa não valida a aparência nem autoriza uma spritesheet final.

Dois testes verificam separação por lacuna/ator ausente e rejeição de frames
fora de ordem. Auditoria documental passou. Próximo passo: procurar dumps
gráficos já existentes correspondentes aos descritores e preservar a
incerteza temporal onde não houver pareamento por frame.

### Cruzamento por ator nas capturas existentes — 02/11/2026

`tools/analyze_charge_animation_trace.py` processou quatro capturas existentes
por ator e frame, filtrando `$0430/$0438/$0440/$0460/$0468/$0470`.
O resultado reproduzível, com hashes das entradas, está em
`docs/issd-charge-animation-trace-summary.json`.

Na captura natural de 9.000 amostras foram observadas 248 amostras de ator
em `$0430` e 58 em `$0460`, todas com script `$D69A`. Nos estados seguintes,
houve 16 amostras em `$0438` e 6 em `$0468`, todas com `$CF9F`.
Estas 22 amostras incluem descritores das listas `82:CFD7/CFC7` e índices
direcionais nativos 4 e 7. Foram observadas duas transições amostradas
`0430→0438` e uma `0460→0468` para o mesmo endereço de ator; a captura lê
um frame em cada dois, portanto outras mudanças podem ter ocorrido entre
amostras e não há prova de duração exata. As outras três capturas analisadas
não apresentaram esses estados nos atores incluídos pelo filtro.

Isso correlaciona estados e descritores existentes, sem identificar o botão,
nome esportivo ou composição visual completa. O filtro de captura omite
alguns atores e os dados não validam sozinhos OAM/paleta. Não foi gerada
spritesheet ou alterado o jogo web. Dois testes cobrem filtro, transições
amostradas e rejeição de frames repetidos; a auditoria documental passou.
Próxima etapa: verificar as sequências individuais e parear com OAM/VRAM
disponíveis antes de concluir duração ou aparência.

### Cursor final e evidência existente de CF9F — 02/11/2026

O estado `$0460` foi agora conferido diretamente na ROM no offset LoROM
`00C1B8`: as palavras são `AD28,AD22,C379,0430`. O verificador
`tools/verify_issd_action_charge_route.py` testa as entradas `$0430/$0460`;
o teste automatizado cobre alterações em ambas e ROM com/sem header.

Em `84:E68F`, após carregar a palavra da lista direcional, uma palavra com
bit `$8000` ativo segue o caminho negativo: incrementa `+$1A` duas vezes e
passa a palavra em X para `84:E6C7`. Uma palavra sem esse bit segue
`84:E6A3`: zera `+$1A`, restaura `$8000` com OR e passa a palavra a
`E6C7`. Assim, a última palavra marcada com `^$8000` no assembly é usada
como descritor com o bit restaurado e reinicia o cursor; não significa
que o descritor final seja ignorado. A duração depende das chamadas ao
handler e do contador `+$16`; a sequência de frames visíveis ainda exige
correlação com a captura.

O relatório existente `docs/issd-action-trace-report.json` registra 4.024
amostras de ator para `$CF9F` e descritores das cinco listas; registra também
oito índices de direção. A maior parte está em estado `$0038` (3.864), com
outras amostras em `$00D8/$00E0` e dois estados adicionais. Portanto a
presença de CF9F não identifica por si só a rota `$0430/$0460` nem um
evento esportivo. Esses números são amostras agregadas, não uma validação
de duração, composição OAM ou da ação de cada jogador.

Fonte: `Routine_Macros_ISSD.asm`, `81:BD58`, `84:E68F..E6C7`, e relatório
de captura citado. Testes de bytes e auditoria documental passaram; não
houve alteração web. Próximo passo: cruzar registros por ator e frames com
estado `$0430/$0460` ou seus estados posteriores, incluindo descritores e
capturas gráficas pareadas, antes de nomear a animação.

### Estrutura dos dados de animação do contador — 02/11/2026

A tabela de estados no assembly associa `$0460` aos handlers `84:AD28`,
`84:AD22` e `84:C379`, com flags `$0430`. Esse registro ainda não foi
conferido byte a byte na ROM. O caminho de `AD28` pode chegar a `AD5E`
e, sob as condições descritas anteriormente, a `ADB9`.

Foram extraídas e conferidas na ROM sete tabelas da animação preparada por
`84:AC1E`: `82:CF9F`, `82:CFAF` e `82:CFB7/CFC7/CFD7/CFE7/CFF7`.
`82:CF9F` contém oito ponteiros direcionais para cinco listas distintas,
com reutilização de listas. `82:CFAF` contém os bytes `4,3,3,3,4,3,3,3`.
Cada uma das cinco listas possui oito palavras; a última é armazenada com
`^$8000` no assembly. Os valores e offsets estão em
`dist/data/issd-charge-animation.json`.

Em `84:E600`, o índice `+$1A` é zerado, Y é salvo em `+$1C` e A em
`+$18`. `84:E645` divide `+$1A` por dois e lê um byte de `($18),Y`;
`E68F` o grava em `+$16`, seleciona uma lista por `+$2E` através de
`+$1C` e lê uma palavra pelo cursor `+$1A`. Isso fundamenta o papel das
tabelas, mas não prova ainda a duração em frames visíveis nem uma sequência
completa de poses. Os descritores apontados e sua composição OAM não foram
validados nesta etapa; não foi gerada spritesheet nem alterado o navegador.

Reprodução: `python tools/extract_issd_charge_animation.py <ROM>`. O teste
`test_charge_animation.py` cobriu as sete tabelas, a palavra final, header
de 512 bytes e rejeição de byte alterado; auditoria da documentação passou.
Próximo passo: conferir `$0460` na ROM, analisar a leitura da palavra final
e correlacionar os descritores com OAM já capturada.

### Rotas de entrada e preparação de animação — 02/11/2026

A entrada `$0430` de `81:BD58`, no offset LoROM `00C188`, contém
`84:AB65`, `84:AB59`, `84:C3B9` e flags `$0430`. Os oito bytes foram
conferidos na ROM local. Os dois primeiros handlers podem chegar a
`84:AB99`; após os gates locais, o teste `BIT $0026,X` com resultado não
zero encaminha `84:AC0C` e, daí, `80:DA3C`.

Outra rota entra em `84:AD28` e, após testes de `$12FA`, `$00E8` e do
registro de controle, chega a `84:AD5E`. Seu teste `BIT $0026,X` pode
encaminhar `84:ADB9`, que também chama `DA3C`. O valor em A e os testes
anteriores dependem do caminho; não se deve substituir esse trecho por
um único botão físico fixo.

`AC0C` continua em `AC10` com Y=`$20`. `ADB9` continua em `ADBD` com
Y=`$24`, chama adicionalmente `80:E1DF` e calcula `+$70` a partir do
resultado deslocado duas vezes. Ambos convergem em `AC1E`, que chama
`84:8548` para avançar o estado em oito, executa rotinas adicionais,
deriva `+$84` e passa `82:CFAF` e `82:CF9F` a `84:E600`. Essa rotina
zera `+$1A`, grava Y em `+$1C` e A em `+$18`; o nome e a correspondência
visual dos dados ainda exigem inspeção e captura pareada.

`tools/verify_issd_action_charge_route.py` verifica a entrada `$0430` na
ROM e quatro sequências no assembly. O teste automatizado detecta alteração
dos bytes e cobre ROM com e sem header. A auditoria documental passou.
Nenhuma animação ou mecânica foi aplicada ao navegador. Próximo passo:
identificar a entrada de estado de `AD28` e decodificar os dados
`82:CFAF/CF9F` com sua temporização antes de associá-los a uma ação.

### Inicialização do contador e controles remapeáveis — 02/11/2026

Foram encontradas duas chamadas diretas a `80:DA3C`: `84:AC0C` e
`84:ADB9`. Após inicializar o contador, elas seguem caminhos distintos
(`AC10` usa Y=`$20`; `ADBD` usa Y=`$24` e também chama `80:E1DF`).
Essas diferenças não bastam para atribuir nomes de ações aos caminhos.

`83:8000` resolve as máscaras lógicas `$0080/$8000/$0040/$4000` usando
`83:8059` e as configurações do controle, gravando os resultados em
`+$16/+$18/+$1A/+$1C` do registro. Assim, `80:DA3C` consulta máscaras
remapeadas, não bits físicos fixos. Se várias entradas estiverem presentes,
testa `+$16` primeiro e `+$18` depois; o terceiro campo é o caminho padrão.
Em cada caso limpa os bits `$7420` de `+$6E`, aplica respectivamente
`$2000/$4000/$1000`, zera `+$82` e copia a máscara escolhida para `+$80`.

`initialize_control_charge` modela essa prioridade e preservação de bits,
sem identificar o botão ou o tipo de evento. Seis testes de
`test_ball_release.py` passaram, incluindo entradas simultâneas e máscaras
remapeadas. A primeira versão do valor esperado no teste de flags estava
incorreta e foi corrigida para `$ABDF` após conferir a máscara de 16 bits.
O modelo continua isolado do navegador. Fonte: `Routine_Macros_ISSD.asm`,
`83:8000/8059`, `80:DA3C`, `84:AC0C` e `84:ADB9`.
Próximo passo: rastrear como os handlers chegam a AC0C/ADB9 e validar a
relação com animações e resultado da bola em captura pareada.

### Origem do contador `+$82` — 02/11/2026

Em `80:DA3C`, o jogo zera `+$82`, limpa bits `$7420` de `+$6E` e escolhe
um entre os campos `+$16/+$18/+$1A` do registro de controle apontado por X,
conforme sua interseção com `+$14`. O valor escolhido é gravado em `+$80`;
um dos bits `$2000/$4000/$1000` é definido em `+$6E` conforme o ramo.
Não atribuímos nomes de botão a esses campos sem fechar o mapeamento.

`80:DA65` carrega X de `$0088`; em `DA68`, enquanto `+$12,X & +$80` for
não zero e `+$82 < 11` (comparação sem sinal), incrementa `+$82`. Caso
contrário, zera `+$80` e preserva o contador. `84:86CA` chama `80:DA65`
quando o bit `$0010` de `+$60` está ativo. Portanto, o valor pode refletir
chamadas com um controle mantido, mas a frequência do chamador ainda não
estabelece uma duração em segundos.

O caminho automatizado `84:C223` também incrementa `+$82` quando o bit
`$0010` de `+$60` está ativo, o contador não é 11 e o decremento de `+$8A`
permanece positivo. Nos demais ramos desse teste, zera `+$80`. Isso não
prova tempos equivalentes entre humano e CPU nem que todos os escritores
de `+$82` pertencem à mesma ação. `85:FC16` ainda pode reduzir valores
maiores ou iguais a 8 para 8, dependendo de testes adicionais.

`update_control_charge` modela apenas `DA68` sobre palavras brutas; cinco
testes de `test_ball_release.py` passaram, incluindo limite e liberação do
controle. Fonte: `Routine_Macros_ISSD.asm`, `80:DA3C..DA79`, `84:86CA`,
`84:C223` e `85:FC16`. O modelo não está conectado ao jogo web. Próxima
etapa: rastrear os chamadores de `DA3C`, os campos de remapeamento e o
significado do caminho `FC16` antes de classificar a ação ou calibrar tempo.

### Tipos e parâmetros após contato — 02/11/2026

`85:F45F` encaminha tipo 2, Y=11 a `F871` quando `+$6E & $1000` está
ativo e `+$6E & $0800` está limpo. Com ambos os bits ativos, encaminha
tipo 29 (`$001D`), Y=11 a `F89B`. Em outros ramos, `85:F75F` encaminha
tipo 3, Y=`+$82` a `F871`; `85:F70C` encaminha tipo 5, Y=`+$82` a `F89B`;
o caminho anterior a `F6DD` pode encaminhar tipo 6, Y=`+$82` a `F89B`.
Os parâmetros de tipo 5/6/3 dependem do valor efetivo de `+$82` e não
devem ser substituídos por um valor fixo.

Em `83:94D4`, Y é mascarado com `$000F` e limitado a 11; o tipo salvo em
`$0000` é multiplicado por 16 e somado ao parâmetro para indexar bytes de
`81:A367`. A leitura resultante é gravada em `$0464`. O extrator agora
inclui exemplos conferidos na ROM: tipos 2, 3 e 29 com Y=11 selecionam
índices 43, 59 e 475, respectivamente; os três bytes são 125. Não há
evidência suficiente para chamar 125 de velocidade ou converter unidades.

`ball_parameter` modela máscara, limite e índice de 16 bits sobre a tabela
fornecida, rejeitando índices fora dos dados verificados. Quatro testes de
`test_ball_release.py` passaram, incluindo máscara, limite, ROM com/sem
header e byte alterado. A inicialização completa depende ainda do ângulo,
dos ramos `$00AC/$00AE` e dos efeitos posteriores; nenhuma regra foi
aplicada ao navegador. Próximo passo: rastrear as entradas variáveis `+$82`
e a integração da bola após a inicialização.

### Inicialização posterior ao contato — 02/11/2026

`85:F871` zera `$00B4/$19D8` e segue para `85:F877`. Esta rotina zera
`$12DC/$12DA/$00AE`, grava X em `$0000/$12F4` e testa `$00D0`. Se não
zero, desvia a `85:F86D`, que copia a página direta para X e retorna carry
set. Caso contrário, guarda A em `$0002`, copia a página direta para
`$00EC` e X, limpa o bit `$4000` de `$11FA` e vai a `85:F8D6`.

`85:F89B` também zera `$00B4/$19D8`, grava X em `$0000/$12F4` e usa o
mesmo bloqueio por `$00D0`. No caminho liberado, guarda A em `$0002`,
registra a página direta em `$19B8/$00EC` e X, e segue para `F8D6`.
Diferentemente de `F877`, o trecho não zera `$12DC/$12DA/$00AE` nem
limpa diretamente o bit `$4000` de `$11FA`.

Como documentado anteriormente, `85:F8D6` zera `$00A4/$00A6`, troca a
página direta para zero e chama `83:94A4`, que inicializa o registro da
bola a partir dos valores guardados. Isso confirma uma ligação estática
entre os destinos pós-contato e a inicialização da bola quando `$00D0=0`;
os valores passados e os efeitos dos ramos alternativos devem ser tratados
separadamente, sem atribuir automaticamente passe, chute ou desarme.

Fonte: `Routine_Macros_ISSD.asm`, `85:F871..F8D6` e `83:94A4`.
O verificador `tools/verify_issd_contact_destinations.py` agora confere seis
sequências; o teste de mutação e a auditoria documental passaram. A ROM e
o motor web não foram alterados. Próxima etapa: rastrear as tabelas e
parâmetros que selecionam o tipo de bola nesses caminhos, incluindo os
desvios quando `$00D0` bloqueia a inicialização.

### Destinos após o contato — 02/11/2026

Em `85:F45F`, o caminho chama `80:D5BC` e `80:E3CE`, grava `$00FF` em
`+$3E` e consulta os bits `$1000/$0800` de `+$6E`. Se `$1000` estiver
ativo e `$0800` limpo, zera `$00AE`, obtém um valor direcional de
`81:9632` e encaminha `85:F871` com X=2 e Y=11. Se ambos estiverem ativos,
chama `80:E7B0` e encaminha `85:F89B` com X=`$001D`, Y=11. Esses destinos
não foram classificados como ações específicas.

`80:E3CE` usa `+$9A` como base em Y. Compara a página direta atual com
os campos `+$EC`, `+$C0` e `+$D8` desse registro; para cada igualdade,
grava `$FFFF` respectivamente em `+$EE`, `+$C2` ou `+$DA`. Isso demonstra
atualização condicional de três campos do registro referenciado; suas
semânticas permanecem pendentes.

Em `85:F66B`, o jogo zera `$17CA`, grava `$00FF` em `+$3E` e examina
`$00B4`. Se não zero e `$19D6 == +$9A`, vai a `85:F767`; se diferentes,
zera `$00B4`. `F45F` também chega a esse teste por `F498` quando o bit
`$1000` não está ativo. Em `F767`, lê `+$2C` do registro apontado por X e
o copia para `$00AC/$00D8/$00DE`, chama `80:D5DF/80:E63B` e zera `$00B4`.
O tipo de evento e a consequência completa das chamadas ainda não estão
confirmados. `80:D5BC` escolhe Y=`$18` para clima 0/1 ou `$25` para os
demais e passa pelo gate `$00BA`; isso não prova alteração de física.

Fonte: `Routine_Macros_ISSD.asm`, rótulos `85:F45F`, `85:F66B`, `85:F767`,
`80:E3CE` e `80:D5BC`. `tools/verify_issd_contact_destinations.py` confere
quatro sequências e `tools/test_contact_destinations.py` confirma que uma
mutação é detectada. As verificações são estáticas e não substituem captura.
Próxima etapa: rastrear `85:F871/F877/F89B` e os campos do registro `+$9A`
antes de conectar os efeitos ao motor web.

### Modelo dos desvios iniciais F438/F617 — 02/11/2026

`contact_dispatch` em `tools/issd_contact_volume.py` modela somente os
desvios de `85:F438` e `85:F617` até `F45F`, `F66B`, `F458` ou `F63E`.
Recebe o resultado de carry do volume apenas quando esse caminho é alcançado.
O modelo preserva uma diferença importante: `F617` rejeita o bit `$0400`
antes de testar igualdade de ator, enquanto `F438` testa igualdade primeiro.
Quando o teste de volume tem carry limpo, o modelo registra o bit `$0400`
que `FAF1` define. Ele não executa as rotinas posteriores nem classifica
o evento como recepção ou desarme.

Sete testes de `test_issd_contact_volume.py` passaram, incluindo igualdade
de ponteiros, vínculo ocupado, aceitação/rejeição do volume e a diferença
entre os dois pontos de entrada. Auditoria da documentação também passou.
A comparação com execução da ROM e os efeitos após os destinos continuam
pendentes; o protótipo web não foi modificado. Próxima etapa: rastrear os
destinos `F45F/F66B` e identificar uma captura que registre as variáveis
necessárias para comparar o modelo com o processador.

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
