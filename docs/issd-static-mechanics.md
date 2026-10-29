# Mecânica estática confirmada — ISS Deluxe

Esta referência foi extraída sem executar a ROM: usa `Routine_Macros_ISSD.asm`
e `issd_symbols.h` do disassembly/nativo local.

## Dispatch de fase

`CODE_83CF7D` lê `$7E:00C0`, desloca o índice uma vez (`ASL`) e salta por
`DATA_83CF86`. A tabela possui 15 entradas (`0..14`). Na versão examinada,
o estado `3` aponta para `CODE_83CFA4`; os demais apontam para
`CODE_83CFAA`. Esses destinos são portas de guarda que retornam `carry`, não
uma descrição semântica suficiente para nomear cada fase. Portanto os nomes de
kickoff, lateral, falta etc. permanecem pendentes de correlação de fluxo.

O gate `CODE_83:CF7D` é usado para filtrar atores dentro desse fluxo. Para os
14 índices comuns, ele retorna carry apenas se o campo local `$30` do ator for
`0001`. O índice 3 aponta para `CFA4`, que aceita adicionalmente quando o
acumulador/direct page é zero e igual a `$11E8`; caso contrário cai no teste
comum. `tools/extract_issd_phase_actor_gate.py` gera
`dist/data/issd-phase-actor-gate.json` e valida essa exceção. Nem os índices
de fase nem os campos de ator foram nomeados por essa evidência isolada.

`CODE_83:C532` atualiza o ponteiro global `$11E8` a partir de campos do ator e
tabelas associadas. Se o slot resultante tiver `$0030 = 0`, `CODE_83:C524`
percorre slots com passo negativo de `$0100`, começando em `$0F00` ou `$1A00`,
até encontrar `$0030` não-zero; o resultado é copiado ao local `$A6`.
`tools/extract_issd_active_actor_selection.py` produz
`dist/data/issd-active-actor-selection.json`. O fato de ser um ponteiro de
ator ativo é comprovado pelo fluxo; ele não é rotulado como jogador humano
controlado sem captura que confirme essa associação.

## Programa de handlers do jogador

`DATA_81:BD58` contém 242 registros contíguos de oito bytes: três ponteiros de
handler e uma palavra de configuração. `CODE_84:8548` avança `$32` em oito,
enquanto `CODE_84:854E` carrega as quatro palavras do registro indexado para
`$90`, `$92`, `$94` e `$60`, respectivamente. Isso comprova uma tabela nativa
de programas de handler; não comprova o papel de cada uma das três colunas nem
transforma o índice em nome de estado de jogo.

`tools/extract_issd_player_handler_program.py` publica cada registro intacto
em `dist/data/issd-player-handler-program.json`, inclusive os que contêm
`CODE_84:B91E`, `CODE_84:B999` e `CODE_84:B9C6`. Assim, as transições de
levantar e seleção de chute já conhecidas podem ser relacionadas a linhas
nativas sem inventar uma máquina de estados web. A semântica dos bits de
configuração e dos chamadores continua pendente.

### Ponte inicial de registros após `$D320`

O fallback comum que seleciona `$82:D320` pode instalar o registro `$0010`.
As três linhas seguintes da tabela de programas são estruturais e foram
extraídas em `dist/data/issd-idle-handler-bridge.json`: `$0010` contém
`CODE_84:87B8`, `$0018` contém `CODE_84:8819` e `$0020` contém
`CODE_84:8859` (com alternativas distintas nas outras duas colunas).

Há duas transições comprovadas, mas não rotuladas: o caminho carry de
`80:DD31` em `87B8`, quando diverge de `$2E`, volta a despachar `$D320` e
instala `$0018`; o caminho correspondente de `8819`, depois de um teste de
bit do ator, despacha `$82:CEF8` e instala `$0020`. `8859` retorna à rota
comum `878A` quando `80:DD31` não retorna carry. Não se deve converter esses
três offsets em “parado/caminhar/correr” sem correlacionar o helper e a
telemetria de entrada.

O helper `CODE_80:DD31` agora possui contrato cru em
`dist/data/issd-locomotion-nibble-gate.json`: ele toma o ponteiro de ator de
`$0088`, mascara o nibble baixo de `ator+$0013` e retorna carry limpo se ele
é zero. Para valores não-zero, retorna carry setado e o byte correspondente
de `81:9613` (`00,00,04,00,02,01,03,02,06,07,05,06,00,00,04,00`). Isso elimina
a ambiguidade de “teste misterioso” dos handlers, mas não autoriza chamar o
nibble de input, direção ou velocidade.

O mesmo nibble também é consumidor de projeção em `CODE_80:E7F8`. A rota usa
`81:9A26` quando o carry de `$6E` está limpo, e `81:9A16` quando está setado,
gravando seus resultados derivados em `$00AE/$00B0`. As duas tabelas de 16
bytes e as operações de base foram extraídas em
`dist/data/issd-actor-nibble-projection.json`. Isso comprova reutilização do
campo em uma rota de projeção, sem rebatizá-lo como direção nem assumir que os
dois destinos são coordenadas finais de tela.

Há uma correção estrutural importante para esse offset: `ator+$0013` é uma
leitura de word desalinhada, não um campo próprio de word. Em modo de
acumulador de 16 bits do 65C816, seu byte baixo é justamente o byte alto do
word em `ator+$0012`; `CODE_86:8036` inicializa esse word a partir de `Y`, e
`CODE_80:DD31` mascara o nibble desse byte baixo. O wrapper normal
`CODE_86:8000` fixa `Y = 0` antes de entrar em `8006`; só a entrada interna
preserva `Y` do chamador. A fronteira byte a byte está em
`dist/data/issd-actor-offset13-overlap.json`. Isso prova a sobreposição e
evita modelar `$0013` como estado isolado; os escritores posteriores ainda
precisam de rastreamento.

O inventário de entradas não-padrão está em
`dist/data/issd-actor-direct-initializer-calls.json`: há cinco chamadas
estáticas para `CODE_86:8006`. Só `CODE_86:8499` configura os dois registros
imediatamente antes da chamada (`X=$1C`, `Y=$1E`); duas fixam apenas `X` e as
demais dependem de helpers/contexto. Isso delimita onde um byte não-zero pode
entrar, sem afirmar que esses atores sejam jogadores de campo nem que `Y`
represente direção.

O outro resultado do mesmo teste em `8819` alcança `CODE_84:88DE`: ele
despacha `$82:CF9F` usando `$82:E34A` e instala `$0038`, cujo primeiro handler
é `CODE_84:8914`. Essa é uma ligação estática direta à tabela de corrida e sua
tabela de direção/tempo já utilizadas pelo navegador. O bit que a seleciona
continua sem significado de controle nomeado; portanto a implementação web
usa a cadência extraída, mas não deve copiar este gate sem evidência de input.

### Ramo do handler instalado com `$CF9F`

O registro `$0038` entra em `CODE_84:8914`. O extrator
`tools/extract_issd_running_handler_branch.py` confirma dois ramos: se
`80:DD31` não retorna carry — ou se o teste de bit seguinte falha — a ROM
despacha `$82:CEF8` com `$82:E34A`, grava `$72 = $0010` e instala `$0040`.
Um ramo alternativo, condicionado pelo carry de `80:E49B`, instala `$0048` e
despacha `$82:D7AB/$82:D79B`. O handler de `$0040` decrementa `$72` e, quando
ele zera, escolhe `84884C` ou a rota comum `878A` conforme `80:DD31`.

O registro `$0048` entra em `CODE_84:8A34`: enquanto `84:E5D1` não retorna
zero ele apenas retorna; quando retorna zero, salta para a rota comum `878A`.
Logo, a sequência `$D7AB/$D79B` possui também uma saída estática comprovada,
sem que isso atribua a ela um nome de ação visual.

### Subgrafo de handlers `$0050/$0058/$0060`

`CODE_84:8A3D` inicia `$0050` e despacha `$82:DA56/$82:E3E4`. O artefato
`dist/data/issd-handler-subgraph-0050.json` confirma que um caminho de
`CODE_84:8A51` instala `$0058` com `$82:DA66/$82:E8C4`; em `$0058`, o caminho
sem carry de `80:DD31` instala `$0060`; e um caminho de término de
`CODE_84:8B15` retorna a `8A3D`, fechando o laço estrutural. Os testes de
carry, `$84` e `E5D1` permanecem condições nativas não rotuladas.

Esse registro de subgrafo permite reconstruir a ordem de decisões sem criar
uma interpretação fictícia de locomoção. A associação a input, física e pixels
depende das evidências separadas de telemetria, OAM, VRAM e CGRAM.

### Lookup de ator compartilhado em `80:E8AD`

`CODE_80:E8AD` salva `A`, escolhe uma base `$3F90` ou `$3FA4` conforme a faixa
do direct page, combina essa base com `$68`, usa os cinco bits baixos do word
resultante para indexar `DATA_81:95EB` e finalmente lê um word de WRAM. O
artefato `dist/data/issd-e8ad-actor-lookup.json` preserva a fórmula e os dois
biases (`$0000/$00C8`).

No seletor de `$D7AB`, o byte alto desse retorno é mascarado para selecionar
um dos cinco controles. Isso não torna o retorno uma direção ou input: é uma
dependência de dados em runtime que deverá ser correlacionada antes de ser
replicada como regra web.

`DATA_81:95EB` foi extraída em
`dist/data/issd-8195eb-lookup-table.json`: são 20 words, de `$3E00` até
`$3EBE`, com passo `$000A`. Além de `80:E8AD`, `CODE_83:DBDC` usa o mesmo
offset para uma leitura de byte em WRAM, com ajuste condicional de `$00C8`.
Esses usos confirmam que a tabela é uma ponte de offsets para dados runtime;
não autorizam rotular seus índices como jogador, posição ou input.

Essas ramificações são fluxo nativo confirmado. Não são uma taxonomia de
correr, virar ou desacelerar: os helpers e os campos de ator exigem correlação
com input e captura visual antes de receber nomes de mecânica web.

`CODE_80:DD47` contém um ajuste cíclico de oito valores, agora preservado em
`dist/data/issd-turn-index-adjustment.json`. Ele compara `A` com `$2E` modulo
8, escolhe incremento/decremento pela tabela crua `81:9629`, normaliza `$2E`
e atualiza o bit `$0040` de `$04` por `81:967A[(2E << 1) + 5A]`. A sequência é
uma regra nativa confirmada de índice/flags, mas o chamador de `A` ainda não
foi provado como controle humano; portanto não foi convertida em giro web.

O produtor mais recorrente desses índices é `CODE_80:DE36`: ele usa `Y` para
consultar `81:963A` e devolve somente o nibble baixo. A entrada vizinha
`80:DE35` apenas copia `A` para `Y` antes da mesma consulta. A tabela de 64
bytes e seus nibbles resultantes estão em
`dist/data/issd-index-nibble-lookup.json`. Ela explica a normalização que
precede vários chamados de `80:DD47`, mas ainda não identifica o índice de
origem como botão, vetor ou direção humana.

`CODE_80:F46D` é distinto: ele não consulta input, mas calcula um índice
angular nativo de seis bits a partir do vetor entre `$0408/$040C` e `$08/$0C`.
Após normalizar magnitudes e sinais, consulta `81:9B3F`, aplica a tabela de
quadrante `81:9B3B` (`00/10/30/20`) e mascara `$003F`. O contrato e as duas
tabelas estão em `dist/data/issd-target-vector-angle.json`. Isso fornece a
transformação angular verificável usada por rotas de alvo, sem inventar graus,
eixos web ou ligação direta ao controle do usuário.

Os destinos globais desse cálculo não são uma posição permanente de uma única
entidade. `tools/extract_issd_target_pair_writers.py` localiza 12 escritores
estáticos de `$0408`; 11 também escrevem `$040C` logo em seguida, enquanto
`83:FD6E` é uma rota de reset sem o par linear. O inventário está em
`dist/data/issd-target-pair-writers.json`. O destino é, portanto, scratch
compartilhado por múltiplas rotas. O navegador não deve usá-lo como fonte fixa
de bola ou jogador sem correlacionar o produtor do frame correspondente.

Duas das rotas produtoras são completamente tabulares. `80:DE3D/DE3F` e
`80:DE55` usam `$2E << 2` para escolher um dos oito pares em `81:97C2` ou
`81:97E2` e somá-lo a `$08/$0C` antes de gravar `$0408/$040C`. As fórmulas e
os pares com sinal nativos estão em `dist/data/issd-target-offset-setters.json`.
Elas recuperam offsets reutilizáveis sem declarar os oito índices como nomes
de direção ou o scratch como alvo permanente.

## Dispatches físicos

| Sistema | Tabela | Quantidade confirmada | Função de dispatch |
| --- | --- | ---: | --- |
| Colisão/modo da bola | `$83:D77F` | 8 | índice dobrado e salto indireto |
| Trajetória/rede/trave | `$83:D9A5` | 6 | índice dobrado e salto indireto |
| Mergulho de goleiro | `$83:DCAA` | 3 | índice dobrado e salto indireto |
| Captura de goleiro | `$83:DDA1` | 9 | índice dobrado e salto indireto |

As contagens acima são estruturais; não atribuem nomes humanos aos subestados
sem uma referência adicional. Elas delimitam, porém, cada máquina finita que
o navegador precisará reproduzir para substituir a física provisória.

### Contrato de inicialização da colisão

O estado 0 (`CODE_83:D78F`) foi detalhado em
`dist/data/issd-collision-state0-contract.json`. Ele parte do ponteiro de ator
`$00C6`, combina os words `+$002A/+$002C` com constantes e `CODE_80:E19B`,
limpa cinco words de trabalho, consulta duas portas (`83:DC1C` e `83:DC5D`) e,
no sucesso, avança `$32`, inicializa flags/campos locais e agenda duas tabelas.
Carry em qualquer porta desvia para `80:D6AB` com `A=$0100`.

O contrato não chama esses words de coordenadas, raio ou tipo de contato: ele
é um ponto de partida verificável para recuperar a física sem substituir
constantes nativas por valores escolhidos para o navegador.

O estado 1 (`CODE_83:D82C`) está em
`dist/data/issd-collision-state1-contract.json`: ele decrementa os locais
`$08/$0C`, deriva quatro bounds em `$08A8/$07A8/$08AC/$07AC` e compara um
word do ator com o limite local. Um ramo avança `$32` e agenda
`$82:ED71/$82:ED77`; o outro atualiza `$07A0/$08A0` pelas tabelas
`81:B03D/B031`. As expressões foram preservadas literalmente, sem declarar
eixos, hitboxes ou resultado semântico de colisão.

O estado 2 (`CODE_83:D881`) está em
`dist/data/issd-collision-state2-contract.json`. A cada execução ele chama
`84:E8A0`, usa `$1A` para gravar valores de `81:B051/B047` em
`$07A0/$08A0` e, somente em `$1A = 6`, incrementa o estado, limpa `$36` e
agenda `$82:C5BB`. O limiar seis é um fato de fluxo; não é uma fase física
nomeada.

O estado 4 (`CODE_83:D8A9`) está em
`dist/data/issd-collision-state4-contract.json`. Retorno não-zero de `84:E8A0`
atualiza `81:B051/B047` e possui uma guarda única em `$36` para `$1A = 8`;
retorno zero avança o estado, agenda `$82:ED5D/$82:ED63` e entra no update
compartilhado. A guarda é control-flow nativo, não um efeito físico nomeado.

O estado 5 (`CODE_83:D8E6`) decrementa os mesmos locais, deriva bounds e grava
`$08 + 8` e `$0C + 12` no ator apontado por `$00C6`. Em seguida, compara o
word do ator `+$002C` com `$FFF0`: abaixo segue a rota de avanço; caso
contrário reutiliza o update compartilhado. O contrato está em
`dist/data/issd-collision-state5-contract.json`; os campos continuam sem
projeção espacial inferida.

O estado 6 (`CODE_83:D910`) primeiro delega literalmente ao estado 2
(`CODE_83:D881`) e, no retorno, entra em `CODE_83:D914`. Esse trecho indexa
`DATA_81:B05D` por `$1A` e grava o word resultante em `+$0010` do ator em
`$00C6`. A tabela crua é `0000/FFF0/FFF8/0000/FFF8/FFF0`; ela não foi
promovida a deslocamento, velocidade ou dimensão. O contrato reproduzível
está em `dist/data/issd-collision-state6-contract.json`, gerado por
`tools/extract_issd_collision_state6_contract.py`.

As rotas compartilhadas agora têm um contrato separado em
`dist/data/issd-collision-shared-routes.json`. `CODE_83:D841` chama `84:E894`
e atualiza `$07A0/$08A0` por `81:B03D/B031[$1A]`. `CODE_83:D873` incrementa
`$32`, agenda `82:ED71/ED77` e entra na cauda que escreve
`81:B051/B047[$1A]`; quando `$1A = 6`, a cauda incrementa novamente `$32`,
zera `$36` e agenda `82:C5BB`. São rotas de controle verificadas, não nomes de
colisão, animação ou evento de futebol.

### Porta temporal compartilhada pelos estados

`CODE_84:E8A0`, chamado pelos estados 2 e 4, é somente o wrapper longo de
`CODE_84:E5D1`. A rotina decrementa `$16`: se o resultado não é zero, retorna
imediatamente; se é zero e `$18` não é negativo, coloca `$0000` em `A` e
retorna. Para `$18` negativo ela consulta um word pelo cursor `$1A >> 1`,
atualiza flags nativas e entrega o byte baixo ao restante do dispatcher. O
contrato literal está em `dist/data/issd-animation-timer-gate.json`. Portanto,
os branches zero/não-zero dos estados são uma porta temporal/script confirmada,
mas ainda não equivalem automaticamente a “fim de animação” no navegador.

## Índices de dispatch observáveis

O prólogo de `CODE_83:D774` instala o direct page `$06A0` e lê `$32`; logo, o
índice da máquina de colisão está em `$7E:06D2`. `CODE_83:D980` chama a máquina
de trajetória para direct pages `$08A0` e `$08D0`, cujos índices `$2E` são
respectivamente `$7E:08CE` e `$7E:08FE`. O capturador passivo registra agora
esses três words como `collision_mode`, `trajectory_left` e
`trajectory_right`; seus valores continuam sem rótulos semânticos até serem
correlacionados com uma transição real de partida.

`tools/report_issd_match_phases.py` resume os quatro índices (fase, colisão e
as duas trajetórias) e suas transições sem exigir que todo campo exista. O
relatório de compatibilidade `docs/issd-match-dispatch-report.json`, gerado do
traço anterior, registra cobertura zero para os novos índices — uma ausência
esperada, não um valor de estado da ROM.

## Próximo trabalho offline

1. Percorrer chamadas e gravações do índice de cada dispatch.
2. Extrair constantes e registros RAM usados por cada handler.
3. Cruzar descritores de animação já resolvidos com os handlers, quando ambos
   coexistirem na telemetria natural arquivada.

## Registros recorrentes por subsistema

| Subsistema | Operandos WRAM mais recorrentes | Interpretação segura |
| --- | --- | --- |
| Colisão | `$00C6`, `$0008`, `$000C` | pertencem a handlers de colisão; sem nome semântico final ainda |
| Trajetória | `$0008`, `$08A0` | pertencem a handlers de trajetória; requerem rastreamento de leitura/escrita |
| Mergulho GK | `$0D00`, `$0E00` | aparecem em dois handlers de mergulho; provavelmente operam atores de goleiro, ainda pendente |
| Captura GK | `$0001`, `$0008`, `$19B2` | usados pela máquina de retenção; sem promover significado antes de análise de fluxo |

Os dados brutos estão em `docs/issd-handler-ram.json`. A regra é manter esses
endereços como observações de dependência, não convertê-los em campos de jogo
com nomes especulativos.

## Portas estáticas de regras da partida

Estas são condições de branch recuperadas diretamente de
`Routine_Macros_ISSD.asm`. Elas provam que a configuração participa da lógica;
não provam ainda o significado de todos os flags temporários usados em volta
dela nem a polaridade que a interface exibirá.

| Regra | Registro lido | Rotina | Condição confirmada | Limite atual |
| --- | --- | --- | --- | --- |
| Impedimento | `$7E:1E4A` (`CurrentOffSideSetting`) | `CODE_80:D5DF` | após um `BEQ` dependente do chamador, `LDX` seguido de `BNE CODE_80:D5EB` pula a chamada de `CODE_80:D627` quando o setting é não-zero; zero continua para o auxiliar | o predicado de entrada e o significado de `carry` em `D627` ainda exigem fluxo/captura |
| Falta | `$7E:1E50` (`CurrentFoulSetting`) | `CODE_80:EED3`, `80:EF83`, `80:F005` | três portas lêem o mesmo word e desviam antes de alterar os estados locais de árbitro/ator | os bits locais `$11F9/$11FA`, `$78` e `$6E` não foram rotulados como uma decisão de falta completa |
| Cartão amarelo | `$7E:1E52` (`CurrentYellowCardSetting`) | `CODE_80:F076` e `80:F09E` | valor não-zero pula o bloco que consulta os estados de cartão e seleciona as sequências seguintes | ainda falta correlacionar o resultado visual e a transição de fase |
| Clima | `$7E:1E4C` (`CurrentWeather`) | `CODE_80:D587`, `80:D5AC`, `80:D5BC` | `0` e `1` escolhem o mesmo valor `Y`; o terceiro valor segue ramos separados | os valores em `Y` são parâmetros internos, não uma equivalência de física sem execução |

O navegador não deve transformar essas portas em regras jogáveis até recuperar
os auxiliares, os estados locais e pelo menos uma transição observada para cada
caso. O mapa automático em `dist/data/issd-match-setting-consumers.json`
continua sendo a fonte para expandir essa análise sem depender de controle
manual da ROM.

## Auxiliar de impedimento

`CODE_80:D627` já permite uma descrição estrutural mais precisa do teste que
fica atrás da porta acima:

1. escolhe o ator-base por `$88` e pelo ponteiro/índice em `$00C6`; a
   coordenada comparada está no deslocamento `$002A` desse ator;
2. usa `$6E` bit 0 para selecionar uma das duas orientações do campo;
3. combina a coordenada do ator-base com os limites `$12F2` e `$042A`,
   aplicando uma margem de `12` ou `24` unidades em `$40`;
4. compara o resultado com `$002A,Y` e retorna `carry` limpo ou setado.

Na orientação com bit 0 limpo, o caminho calcula um extremo superior e soma a
margem; na outra, calcula o extremo inferior e subtrai a margem. Os dois
únicos retornos são `CLC` em `CODE_80:D657` e `SEC` em `CODE_80:D67E`.
`tools/extract_issd_offside_boundary_predicate.py` publica essa aritmética em
`dist/data/issd-offside-boundary-predicate.json`, incluindo a escolha de limite
e a margem em cada orientação. O artefato registra apenas o contrato de carry:
ele não afirma que `SEC`, isoladamente, seja uma infração ou um reinício.
`CODE_80:D5DF` não agenda diretamente uma interrupção de jogo. Ao receber o
primeiro `SEC`, salva `Y` em `$00C4`, entra em `CODE_80:DCA9` e calcula os
temporários locais `$2C = $009A + $0C` e `$2A = $0098 + $08 - $2C`.

A etapa seguinte agora está recuperada: `CODE_A4:A424` chama
`CODE_A4:A442`, que percorre exatamente 11 slots com stride `$0100`, a partir
de `$D4 - $0100`. Ela ignora slots cujo `$0030` é zero, compara `$002A` e,
conforme o sinal de `$A4`, seleciona um dos extremos. Ao final escreve o slot
escolhido em `$C6`, o extremo em `$F8` e uma referência limitada por `$042A`
e `$12F2` em `$C4`. O segundo `CODE_80:D627` usa esse `$C6` reconstruído;
logo, os dois testes não são redundantes.

Depois de restaurar `Y`, somente se a confirmação retornar `SEC`,
`CODE_80:D60A` pode trocar `$00BA` para `4` e chamar `CODE_80:D680`; caso
contrário, limpa `$00C4` e retorna. A futura implementação deve conservar
essa confirmação em duas etapas, incluindo a varredura de atores, e não marcar
uma ocorrência no primeiro comparativo.

Esse `$00BA` é um campo da página direta ativa nesse fluxo, e não deve ser
confundido com a fase global `$7E:00C0` despachada por `CODE_83:CF7D`.
`CODE_80:D680` também não altera essa fase global: ele só pode marcar
`$19D2` com `$0400` após consultar dados do ator. A transição posterior para
uma interrupção global ainda precisa ser seguida a partir desse sinal local.

O índice `dist/data/issd-match-event-bits.json`, produzido por
`tools/extract_issd_match_event_bits.py`, reúne todas as escritas estáticas
localizadas para `$7E:19D2`. Ele confirma que o mesmo word também é escrito
por fluxos de falta/cartão e por substituições completas de valor; portanto
não é válido chamar o bit `$0400` de uma fase persistente. Nenhum consumidor
direto foi localizado nesta leitura estática, ficando a cadeia de transição
dependente de rastreamento em execução.

Três sites de jogo já chamam a mesma porta — `CODE_85:F4BE`, `85:F767` e
`85:F81F` — sempre preparando `$00AA/$00AC/$00D8/$00DE` e usando o valor de
`Y` devolvido. Os nomes dessas estruturas e a equivalência final de `SEC` com
uma marcação de impedimento permanecem pendentes: a documentação registra a
aritmética e o fluxo, não um rótulo especulativo para os slots.

## Máquinas de goleiro

`CODE_83:DCA2` despacha três entradas por `$14A8` através de
`DATA_83:DCAA`; não há nomes semânticos atribuídos às entradas `0..2`. A
inicialização compartilhada em `CODE_83:DCB0` prepara, em páginas diretas
separadas, os dois blocos de goleiro `$0D00` e `$0E00`. Para cada bloco,
`CODE_83:DCE7` define temporários `$B4/$B6/$B8/$BA/$BC/$BE/$CE` e a tabela
`DATA_81:B010`; o bit `$4000` de `$D0` altera `$F6`.

A entrada `CODE_83:DD05` visita os dois blocos e só avança sua tabela quando
o bit `$0002` de `$A4` permite. A entrada `CODE_83:DD6E` também visita ambos,
mas primeiro compara o índice do bloco com `$1522`, exige o mesmo bit de
`$A4` e usa `$B2/$B6` como guardas. Só então despacha pelas nove entradas de
`DATA_83:DDA1`: o índice vem do acumulador `A`, enquanto `$1500` é carregado
em `Y` como contexto/base para os handlers.

Esses fatos estabelecem que mergulho e retenção são máquinas com estado e
tabelas próprias para cada goleiro — não uma única colisão genérica da bola.
Ainda faltam os significados dos estados `$14A8` e dos valores em `A` que
selecionam a retenção, as condições que os escrevem e uma captura que associe
cada etapa às animações de defesa. Portanto o navegador continua sem alegar
que sua lógica provisória de posse represente uma defesa original.

`tools/extract_issd_goalkeeper_context_writes.py` registra os escritores
explícitos em `dist/data/issd-goalkeeper-context-writes.json`. Na revisão USA,
há cinco stores diretos para o seletor de mergulho `$7E:14A8` e três para o
contexto `$1500`; dois destes últimos são indexados por `Y`. O artefato
preserva rotina, linha, instrução e modo de endereçamento, sem converter o
contexto em um seletor de estados antes de correlacioná-lo com execução.

`tools/extract_issd_goalkeeper_handler_machine.py` complementa esse índice em
`dist/data/issd-goalkeeper-handler-machine.json`: fixa os três destinos de
`DCAA`, as nove entradas de `DDA1`, as páginas processadas e os campos locais
observados. É uma proteção contra mudar a estrutura do dispatch ao evoluir a
documentação, sem interpretar valores de controle como movimentos visuais.

As cinco escritas também provam o domínio numérico completo de `$14A8`: as
rotinas de inicialização escrevem `0`, `CODE_A4:BE2E` escreve imediatamente
`1` e `CODE_86:9BDA` escreve imediatamente `2`. Esses são identificadores de
dispatch para `DATA_83:DCAA`, não nomes de animação; a associação de cada um
com uma defesa específica permanece pendente de captura.

As cadeias imediatas também foram confirmadas. `CODE_A4:BE2E` grava o estado
`1` somente depois de carregar `DATA_87:B122`, chamar `CODE_858687` e depois
da preparação `CODE_83:DCB0`; em seguida transfere o controle para
`CODE_A4:BE46`, que despacha 13 entradas por `DATA_A4:BE66`. Já
`CODE_86:9BDA` grava `2`, agenda `CODE_86:9BE6` e este despacha 13 entradas
por `DATA_86:9BF8`. Essas tabelas descrevem duas sequências de controle
distintas, mas não autorizam chamá-las de mergulho alto/baixo/direção sem uma
correlação visual em runtime.

`tools/extract_issd_goalkeeper_mode_schedulers.py` preserva os dois
agendadores em `dist/data/issd-goalkeeper-mode-schedulers.json`. Para o modo
`1`, o índice é `$22` deslocado para `X`; no modo `2`, `X` chega pelos helpers
`86:A1DF/A659`. A diferença é material: não se deve copiar a regra de índice
de uma tabela para a outra, nem tratar os 13 destinos como uma sequência de
quadros até recuperar suas transições em execução.

### Progressão da tabela de retenção

As nove entradas de `DATA_83:DDA1` já têm efeitos locais recuperados. A tabela
abaixo usa o índice em `A`; os nomes são deliberadamente numéricos.

| Índice | Destino | Mutações confirmadas |
| ---: | --- | --- |
| 0 | `CODE_83:DDB3` | incrementa `$B2`, carrega `$B6` e dois destinos através de `DATA_81:B01C` |
| 1 | `CODE_83:DDC8` | consulta `CODE_83:DEC4`; em ramos válidos atualiza `$19B0`, incrementa `$B2`, define `$19B2 = 10` e usa `DATA_81:B01F`; no fallback fixa `$B2 = 5` e usa `B022` |
| 2 | `CODE_83:DE20` | incrementa `$B2` e usa `DATA_81:B025` |
| 3 | `CODE_83:DE2A` | decrementa `$19B2`; quando zera define `$B6 = 8` e `$B2 = 7`; caso contrário filtra dados do contexto e pode incrementar `$B2` com `B02E` |
| 4 | `CODE_83:DE88` | fixa `$B2 = 1` e usa `B028` |
| 5 | `CODE_83:DE92` | incrementa `$B2` e usa `B022` |
| 6 | `CODE_83:DE99` | limpa `$4000` em `$D0`, incrementa `$F6` e usa `B02B` |
| 7 | `CODE_83:DEA5` | incrementa `$B2` e usa `B028` |
| 8 | `CODE_83:DEAC` | fixa `$B2 = 1` e usa `B022` |

`CODE_83:DEC4`, chamado pela entrada 1, percorre 20 registros a partir de
`$3E00` ou `$3EC8` conforme a página do goleiro e retorna `carry` a partir de
uma soma de nibble. A interpretação desses registros, do contador `$B2` e dos
dados `B01C..B02E` exige captura; o que já é seguro é que a retenção é uma
máquina temporal com ramos e não uma troca direta de sprite.

`tools/extract_issd_goalkeeper_catch_timing.py` extrai os sete registros
`$81:B01C..B02E` para `dist/data/issd-goalkeeper-catch-records.json`. Cada
registro preserva o byte realmente carregado em `$B6` e a word copiada por
`CODE_83:DDB8` através de `($B8)` e `($CE)`. Os pares recuperados são
`4/0400`, `8/0080`, `8/8000`, `32/0200`, `32/0100`, `255/0080` e `32/0080`.
Eles devem ser usados como dados de controle da máquina até que runtime prove
quais são duração, flags ou outros parâmetros visuais.

## Sequenciador de trajetória da bola

`CODE_83:D980` processa até dois blocos de trajetória: `$08A0` quando
`$1E6C` é não-negativo e `$08D0` quando `$1E6E` é não-negativo. Em cada bloco,
`CODE_83:D99D` despacha `DATA_83:D9A5` usando `$2E` — os endereços observáveis
do índice são `$7E:08CE` e `$7E:08FE`.

| Índice `$2E` | Destino | Transição/contador confirmado |
| ---: | --- | --- |
| 0 | `CODE_83:D9B1` | decrementa `$26`; ao zerar incrementa `$2E` e define `$26 = 16` |
| 1 | `CODE_83:D9C7` | decrementa `$26`; em 8 atualiza recurso; ao zerar incrementa `$2E`, prepara dados e define `$26 = 64` |
| 2 | `CODE_83:DA38` | a cada expiração define `$26 = 8`, incrementa `$16`; após cinco passos incrementa `$2E` e zera `$26` |
| 3 | `CODE_83:DA98` | aguarda `$26`; na expiração incrementa `$2E`, define `$26 = 16` e atualiza recurso |
| 4 | `CODE_83:DAD1` | aguarda `$26`; em 8 atualiza recurso; na expiração incrementa `$2E` |
| 5 | `CODE_83:DAED` | encerra um dos blocos, marca `$1E6C/$1E6E` como `FFFF` e limpa um bit de `$11FA` quando ambos acabam |

Os handlers chamam rotinas de recurso/VRAM e usam campos locais adicionais
(`$16`, `$1A/$1C`, `$22/$23`, `$28/$29`). A sequência e os contadores são
confirmados; ainda não há evidência suficiente para nomear os seis índices como
tipos específicos de chute ou passe, nem para transplantar essa trajetória ao
Canvas antes de recuperar suas coordenadas e colisões.

`tools/extract_issd_ball_trajectory.py` reproduz essa leitura do assembly e
gera `dist/data/issd-ball-trajectory.json`. O extrator verifica os seis
destinos de `DATA_83:D9A5` e as instruções de transição/contador usadas acima;
assim, uma alteração no disassembly não transforma esta descrição em dado
silenciosamente divergente. O artefato não nomeia eventos futebolísticos nem
é consumido pelo navegador enquanto os inicializadores e a cinemática não
forem recuperados.

### Ativação dos blocos

**Inicialização estática confirmada.** `CODE_83:D92D` prepara cada bloco ativo
pela dupla de tabelas `DATA_81:B0BB/B0BF`, lê os valores locais `$08/$0C` de
`DATA_81:B0C3`, e acrescenta `$20` ao segundo para os estádios `5` e `7`.
Também escreve `$22=$5622`, `$26=$0040`, zera `$2E` e marca o bit `0001` de
`$11FA`. Isso é um contrato de estado e de offsets locais, não uma autorização
para chamar `$08/$0C` de coordenadas, nem para converter esses valores em
velocidade no Canvas.

O escritor dos dois words ativos foi localizado. `CODE_86:AAB0` lê
`$1E6C + ($22 << 1)` para `$F4`; em `CODE_86:9E48`, `$F4` é copiado a `$D0` e
gravado de volta em `$1E6C + ($22 << 1)`. Para os valores observados `0/1` em
`$22`, isso seleciona respectivamente `$1E6C/$1E6E`. Em seguida,
`CODE_83:D920` visita ambos os words pela tabela `$81:B0BB`, associa-os às
direct pages `$08A0/$08D0` via `$81:B0BF` e inicializa um bloco ativo em
estado zero com contador `$26 = 64`.

`tools/extract_issd_trajectory_activation.py` gera
`dist/data/issd-trajectory-activation.json`. A rotina que fornece o valor de
`$F4` ainda é um interpretador de script sem eventos nomeados; portanto isto
não prova qual comando é passe, chute, quique ou contato com a rede.

O helper `CODE_86:AADB` expõe parte da codificação do script: `AA91` conta
quantos dos índices locais `$48/$4A` são ao menos `11`, e `AADB` só transfere
quando a contagem é exatamente `1`. Ele lê bytes do ponteiro `$28`, mascara
com `1F` e grava o resultado nos words de trajetória. O helper vizinho
`AB0F` manipula o bit `20` entre as mesmas posições. Isso comprova uma
codificação de baixo 5 bits mais marcador, mas não o significado
futebolístico de cada valor.

O ponteiro indireto `$28` usado por esse transferidor é preenchido em
`CODE_86:A4B3`: escolhe um dos offsets de trabalho `$146E/$1482` pela palavra
`$22` e copia 20 bytes. Esses endereços baixos são memória de trabalho no
contexto da rotina, não blocos de ROM extraíveis estaticamente. `CODE_86:A4D1`
é o inicializador alternativo que escreve a
sequência de bytes `00..13`. Os consumidores usam `$48/$4A` e comparam cada
índice ao limiar 11. `tools/extract_issd_trajectory_script_buffer.py` gera
`dist/data/issd-trajectory-script-buffer.json`; os offsets e o limiar não são
rotulados como equipe, lado ou evento antes de evidência adicional.

A procedência desses offsets está confirmada: `CODE_86:A4A4` move 40 bytes de
`$7E:3F90` para `$81:146E`; portanto `$146E` e `$1482` são as duas metades de
20 bytes desse buffer de trabalho. Isso mantém a origem dinâmica explícita e
evita confundir o conteúdo de uma partida com dados extraídos da ROM.

## Arrays de escalação em runtime

`CODE_83:C6E6` inicializa `$7E:3F90` e `$7E:3FA4` com a sequência de bytes
`00..13`, cada um com 20 entradas. Em `CODE_83:C94F`, a ROM passa esses arrays
e as equipes configuradas para `CODE_83:C9C5`, que percorre 11 entradas por
equipe, preenchendo atores com bases `$0500/$1000` e passo `$0100`. A cada
iteração, lê a entrada do array, ignora entradas com bit `20`, usa os 5 bits
baixos no caminho de dados da equipe e avança a leitura de ator em `$20`.

`tools/extract_issd_team_runtime_slots.py` gera
`dist/data/issd-team-runtime-slots.json`. Esses arrays podem ser modificados
durante o fluxo da partida; portanto eles não são uma escalação estática para
ser copiada diretamente ao navegador.

`CODE_86:CA23` torna a marca `20` uma porta de atividade comprovada, não só
um filtro do leitor: para cada lado, começa no segundo byte do array
(`$3F91`/`$3FA5`), marca com `ORA #$20` as entradas posteriores à quantidade
configurada de jogadores em campo e limpa a mesma marca nas restantes com
`AND #$DF`. A rotina percorre apenas as 10 posições após o primeiro byte de
cada metade; ela não prova o significado humano do byte zero nem transforma o
valor em número de camisa.

Há também uma ponte estática entre essas listas e trajetória. Quando o ajuste
de jogadores é menor que quatro e `$1E6C` ou `$1E6E` está ativo,
`CODE_83:C71D` chama `CODE_83:C74F` com, respectivamente,
`$3F90/$7E:D864/$1E6C` e `$3FA4/$7E:D878/$1E6E`. `$1E6C/$1E6E` são palavras
de seleção; os blocos de estado processados pela máquina de trajetória são
`$08A0/$08D0`. A subrotina percorre 11 bytes do snapshot, descarta o candidato
de snapshot marcado com bit `20` e procura o valor dele na lista atual. Ela
escreve uma dupla de bytes pelo ponteiro fornecido: o byte alto recebe o valor
do candidato ausente no array atual e o byte baixo recebe o offset encontrado
na segunda busca do array atual; em falha escreve `$FFFF`.

`CODE_83:C7CB` lê o byte baixo para indexar o array de runtime atual;
`CODE_83:C870` lê o byte alto após `XBA`. Isso prova o encadeamento
snapshot → par de seleção → resolução de dados de ator, mas ainda não dá
rótulo de gameplay a esses bytes nem demonstra que uma mudança seja passe,
chute, troca de jogador ou movimento de formação.

O ciclo do snapshot também foi localizado. `CODE_83:C704` executa `MVN` de 40
bytes de `$7E:3F90` para `$7E:D864`: as duas metades resultantes são os
snapshots `$D864` e `$D878`. Um callsite observado, `CODE_A4:DAC0`, primeiro
zera os dois seletores com `$FFFF` e depois chama essa cópia. No consumo, o
byte baixo do par é mascarado por `00FF` em `C7CB` para indexar o array atual
e derivar flags internas em `$19D4`; `C870` salva as palavras em
`$06DC/$07DC`, aplica `XBA` e passa o byte alto para `C903`. Esses destinos
são dados internos, não nomes de evento ou comandos web.

### Registro-base de jogador usado na população

`CODE_83:C9C5` usa os 5 bits baixos da entrada de runtime para selecionar um
registro de 10 bytes. `CODE_83:CA79` calcula `base da equipe + índice × 10`;
para cada uma das 11 populações de ator, o destino avança `$0100`, enquanto a
fonte de contexto avança `$20`. Os dois passos coexistem, mas sua razão de
alto nível ainda não foi identificada.

As leituras comprovadas são: offset `00` (nibbles alimentam os offsets de ator
`+62/+66`), `02` (nibble alto para `+67`), `04` (nibble alto para `+30`), `05`
(word deslocada para `+56`), `06` (nibble alto combinado antes de `+03`), `07`
(bits `80/08` bloqueiam população específica) e `08` (ajuste limitado de
`+62/+66`). Esses offsets não devem receber nomes como velocidade, cabelo,
posição ou habilidade sem correlação adicional. O artefato regenerável é
`dist/data/issd-runtime-player-record.json`.

O byte `06`, que o catálogo apresenta como candidatos de aparência, tem agora
uma fronteira de evidência explícita: `83:C9C5` usa somente o nibble alto para
construir o campo de ator `+03`. Isso prova participação na população do ator,
mas não prova que os nibbles sejam tom de pele, cabelo, paleta ou gráfico. O
editor futuro poderá manter esses dados como conteúdo próprio, sem afirmar que
reproduz a aparência da ROM até a cadeia gráfica ser correlacionada.

## Caminho gráfico padrão do ator

Ao finalizar a população, `CODE_83:C943` chama `CODE_84:F80F`. Este chama
`84:F813`, que por sua vez executa `83:F222`, carrega o script de corrida
`DATA_82:CF9F`, a tabela direcional/temporal `DATA_82:E34A` e entra em
`84:E60C`. A temporização bruta da tabela é `4,3,3,3,4,3,3,3` ticks.

Os oito ponteiros de direção de `$82:E34A` são
`E382,E392,E3A2,E392,E382,E372,E362,E372`; repetições são aliases reais da
tabela, não autorização para reordenar ou duplicar frames manualmente.
`84:E60C` seleciona o descritor, e `84:E6C7` gera registros de transferência
a partir de `DATA_82:A3D7`, incluindo o seletor da porta VRAM. Essa cadeia
prova a inicialização visual padrão de corrida, mas ainda não decodifica todos
os campos do descritor nem prova a semântica de flip, prioridade ou OAM para
cada parte. O artefato é `dist/data/issd-default-locomotion-pipeline.json`.

### Aplicação web limitada à cadência confirmada

O navegador agora carrega `dist/data/issd-locomotion-scripts.json` para obter
os dez quadros de caminhada com três ticks e os oito ticks de corrida. A
carga valida explicitamente esses tamanhos e valores; se o manifesto não
estiver disponível, usa o mesmo contrato ROM-validado já embutido, sem
interpolar FPS inventado. Essa aplicação afeta somente a escolha temporal de
folhas de locomoção que já foram validadas. Velocidade, aceleração, posse,
colisão, chutes e transições continuam provisórios ou bloqueados por falta de
evidência correspondente.

## Máquina de controle de colisão

`CODE_83:D774` instala a direct page `$06A0`, lê `$32` e despacha
`DATA_83:D77F`. Há oito entradas: os índices 3 e 7 retornam imediatamente;
os demais inicializam ou atualizam campos locais, limites e dados do ator.
Os índices 0, 1, 2, 4, 5 e 6 correspondem respectivamente a
`D78F/D82C/D881/D8A9/D8E6/D910`. As transições comprovadas são incrementos de
`$32` nos ramos 0, 1 e no ramo de índice 6 dentro do handler 2. O handler 5
também ajusta os offsets `$08/$0C` do ator atual e o 6 escreve `$10`.

`tools/extract_issd_collision_machine.py` gera
`dist/data/issd-collision-machine.json` e valida os destinos e instruções
observadas. Os nomes semânticos dos estados e a relação exata com bola, rede,
trave ou jogadores permanecem pendentes; este dado ainda não modifica a física
provisória do navegador.

O mesmo artefato agora fixa o driver `CODE_84:A69A`: ele só chama o dispatcher
quando o `$76` local é não-zero e conserva uma guarda posterior em `$06D2`.
Também registra as seis transições que têm `INC $32` e condição observável.
Elas não formam uma linha obrigatória: os estados `1`, `2`, `4`, `5` e `6`
podem permanecer onde estão quando suas condições não se confirmam. A origem
do primeiro estado e o significado público dessas guards continuam pendentes.

O mesmo artefato preserva as cinco tabelas referenciadas pelos handlers:
`DATA_81:B031` (6 ponteiros), `B03D` (5), `B047` (5), `B051` (6) e `B05D`
(6 words). A última contém, na ordem, `0000, FFF0, FFF8, 0000, FFF8, FFF0` e
é escrita pelo handler 6 no offset `$10` do ator. Os quatro primeiros grupos
são ponteiros para dados em banco `$88`; o seu conteúdo e função visual ainda
precisam de uma investigação própria.

Essa estrutura foi agora delimitada: os 16 destinos únicos em `$88:E9EC..EB43`
começam com uma contagem e contêm exatamente essa quantidade de registros de
quatro bytes. O extrator preserva cada quarteto cru em `bank_88_descriptors`;
não rotula seus bytes como posição, tile, atributo ou prioridade antes de
confirmar o consumidor que os interpreta. Eles são candidatos a descritores de
composição, não spritesheet pronto para o navegador.

## Seleção de atores para colisão

Antes de iniciar o estado 0, `CODE_83:D78F` chama `CODE_83:DC1C` e
`CODE_83:DC5D`. Ambos percorrem 11 slots de ator, com passo `$0100`, a partir
de `$0500` ou `$1000` conforme a direct page. Um candidato é pulado quando o
offset `$001E` é não-zero ou `$0030` é zero. O primeiro auxiliar salva o slot
em `$24`; o segundo salva em `$34` e também exclui o candidato igual a `$3E`.
Eles copiam os 9 bits baixos do offset `$0002` para flags locais (o primeiro
faz `OR $0E00`).

`tools/extract_issd_collision_target_selection.py` gera
`dist/data/issd-collision-target-selection.json` e valida essa varredura. Os
papéis dos slots e a semântica das flags continuam pendentes; portanto não há
mudança da posse/colisão provisória no navegador.

`CODE_86:8000/8036` inicializa o offset de ator `$001E` com o registrador `Y`
e `$0030` com `0910`. As rotinas `CODE_86:A2D8/A30D` depois preenchem `$001E`
em grupos a partir do local `$22` (o segundo grava `$22 XOR 1`). Isso explica
por que os seletores consultam ambos os offsets, mas não prova seus nomes
públicos. `tools/extract_issd_actor_collision_fields.py` gera
`dist/data/issd-actor-collision-fields.json` para manter esse vínculo de
inicialização auditável.

## Portas de falta e cartão

As três entradas estáticas que consultam `CurrentFoulSetting` são
`CODE_80:EED3`, `80:EF83` e `80:F005`. A primeira só retorna cedo após uma
conjunção de campos de ator e de `$11F9`; a segunda usa o valor não-zero em
um ramo que escreve `0200` em `$6E` local e `8003` em `$78`; a terceira retorna
cedo em `F045` quando o setting é não-zero, após limpar `19D2` bit `0800`.
Assim, os valores não devem ser reduzidos a uma polaridade global de
liga/desliga. As portas de cartão amarelo em `F076/F09E` também desviam quando
o setting é não-zero, mas o resultado dos auxiliares ainda não está provado.

`tools/extract_issd_foul_gates.py` gera `dist/data/issd-foul-gates.json` com
esses ramos e limitações. Faltas, cartões, árbitro e reinícios seguem como
comportamento pendente de captura/fluxo e não alteram o protótipo web.

Os ramos de cartão que suprimem o processamento seguem para `CODE_80:F125`.
Esse final limpa o bit `0800` de `$04DE`, escreve `$00BA` como `0003` ou
`0006` conforme bits `1800` de `$0DD0`, copia `$76` local para `$00C4`, zera
`$00C6` e retorna com carry. Os valores são internos e não foram promovidos a
nomes de fase/reinício; a informação apenas fecha o efeito estático desses
desvios.
