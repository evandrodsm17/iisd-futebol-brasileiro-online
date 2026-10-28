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
`$A4` e usa `$B2/$B6` como guardas. Só então despacha por `$1500` nas nove
entradas de `DATA_83:DDA1`.

Esses fatos estabelecem que mergulho e retenção são máquinas com estado e
tabelas próprias para cada goleiro — não uma única colisão genérica da bola.
Ainda faltam os significados dos estados `$14A8/$1500`, as condições que os
escrevem e uma captura que associe cada etapa às animações de defesa. Portanto
o navegador continua sem alegar que sua lógica provisória de posse represente
uma defesa original.
