# Bola relativa ao ator — 01/11/2026

## Fontes e resultado

Assembly local `Routine_Macros_ISSD.asm` e ROM USA original, somente leitura.
`tools/extract_issd_ball_attachment.py` produz
`dist/data/issd-ball-attachment.json`: quatro tabelas conferidas byte a byte
na ROM, SHA-256 da entrada e trechos de seis rotinas. Não copia a ROM.

| Tabela SNES | Offset LoROM sem header | Conteúdo |
| --- | --- | --- |
| `81:97C2` | `0097C2` | 8 pares de palavras X/Y |
| `81:97E2` | `0097E2` | 8 pares de palavras X/Y |
| `81:9802` | `009802` | 16 pares de palavras X/Y |
| `81:9842` | `009842` | 64 bytes de deslocamentos |

## Escritas diretas de posição

`80:DE3D/DE3F`: indexa `81:97C2` por `$2E*4`, soma os dois deslocamentos
às palavras locais `+$08/+$0C` e grava `$0408/$040C` (bola).
`80:DE55` faz o mesmo com `81:97E2`. A soma tem o comportamento de palavra
de 16 bits do processador; os valores negativos da tabela estão em complemento
de dois. Exemplo do índice **nativo** zero: `(11,-1)` versus `(19,-1)`.
Isso não atribui uma direção de tela a esse índice.

`80:DE6D` usa outra trajetória: acumula `$78` em `$76`, usa os cinco bits
baixos, escolhe um dos 16 pares de `81:9802` e inverte os dois deslocamentos
na metade superior do ciclo. Os resultados são somados às coordenadas do ator.
Não atribuímos nome de ação a essa trajetória.

## Ciclo de oito fases

`80:DEA5` inicializa `$70=4`; `DEAA` zera `$76/$78/$7A` e chama `DEB9`
com a base `81:9842`. `80:DF00` decrementa `$70`: quando chega a zero,
recarrega 4 e avança `$76` módulo 8. `DEB9` combina a fase e a tabela
de direção `81:9623`, lê bytes assinados para os dois eixos e aplica os
espelhamentos controlados pelos bits transferidos a `$44/$45`.

`80:DF1D` soma `$78/$7A` à posição do ator e escreve a posição da bola,
além dos espelhos `$1BC8/$1BCC` e `$0412`. A rotina é chamada em
`84:8EE2` quando o índice direcional retornado coincide com `$2E`.
O caminho de inicialização `84:8EB2` chama `DEA5`.

**Limite temporal:** quatro chamadas por fase não prova quatro frames
renderizados. É necessário validar a cadência do estado chamador. Também
não está demonstrado que esse ciclo seja usado em toda caminhada/corrida.

## Vínculo de ator em $00A6

Há evidência mais forte que a hipótese descartada de `$1B90`:

- `84:97FE` executa `TDC; STA.w $00A6`, guardando a página direta atual,
  depois de testar entradas do controle e zerar `$00A4`.
- `85:ECC3` chama `85:F8B9` e grava X em `$00A6`. Dentro de `F8C5`,
  `TDC; TAX` copia o ator chamador; `F8D6` zera `$00A6` antes da transição.
  O trecho não basta para afirmar que todos os caminhos preservam X até
  o retorno: essa prova interprocedural continua pendente.
- `80:E9E7` usa `$00A6` como base para ler `$0060,Y`; se o bit `$8000`
  estiver ativo, usa os incrementos `+$23/+$27` desse ator para calcular
  coordenadas relacionadas à bola. Se zero, segue a rota da própria bola.
- `80:DF37` compara a página direta a `$00A6` antes de limitar deslocamentos.

Conclusão restrita: `$00A6` vincula um ator a caminhos de tratamento da bola.
Ainda não é contrato universal de posse: há transições, goleiros, reinícios
e estados sem bola que precisam ser separados. Não confundir o absoluto
`$00A6` com `STA.b $A6` em uma página direta não zero.

## Testes e retomada

Continuação: [issd-ball-state-routing.md](issd-ball-state-routing.md) recupera
as entradas B8/C0/C8 e a preservação normal de X no caminho de `85:F8B9`.
Os limites de posse universal e de cadência continuam válidos.

Executados: extração com comparação real das quatro tabelas; dois testes
automatizados cobrindo arquivos com/sem header de 512 bytes e rejeição de
byte divergente. A ROM não foi alterada. Nenhum deslocamento foi aplicado
ao Canvas: conversão de unidades, direção de tela e cadência seguem pendentes.

Próximo passo: fechar a preservação de X em `85:F8B9` e o roteamento de estados
que chega a `84:8EB2/8EE2`; buscar `$00A6` nas capturas existentes antes de
solicitar nova captura. Só então classificar vínculo, condução e liberação.
