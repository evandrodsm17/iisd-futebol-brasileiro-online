# Captura de restrições de movimento

## Sessão concluída: 113515

A versão com loop explícito registrou 18.000 frames consecutivos, de 130601
a 148600, com 22 atores em cada amostra (cinco minutos a 60 fps). O seletor
de estádio permaneceu 3; todos os limites observados coincidem com as
fórmulas estáticas, sem divergência em nenhuma amostra. Foram observados
valores de fase `$00C0` 0, 3 e 7, sem atribuir nomes públicos a eles.

`$12FA` permaneceu zero nos 18.000 frames e nenhum ator apresentou `$0800`
em `$6C`. Portanto a coleta confirma os limites do estádio 3, mas não valida
dinamicamente a restrição por âncora. Não há motivo para repetir caminhada
ou corrida: a próxima investigação deve identificar o controle que ativa
essa rotina antes de solicitar nova captura.

Relatório: `issd-motion-constraints-summary.json`. Reprodução:
`python tools/analyze_issd_motion_constraints.py docs/issd-motion-constraints-20261029-113515.jsonl docs/issd-motion-constraints-summary.json`.
O JSONL bruto permanece local e ignorado pelo Git.

## Investigação após a captura

### Correção da associação de controles

`83:C94F` prepara `$0012=$0E00` para o grupo de atores iniciado em `$0500`
e `$0012=$0D00` para o grupo iniciado em `$1000`. `83:CA47` copia esse word
para `$88` de cada ator. As amostras runtime contêm esses mesmos valores
(3584 e 3328). Já `83:8000` inicializa registros a partir de `$1AA0`, passo
`$30`. A ponte entre esses registros e `$0D00/$0E00` ainda não foi provada.

Assim, a identificação anterior como ação lógica Y deve ser tratada apenas
como candidata. A existência de um campo `+$1C` em ambas as estruturas não
prova identidade de conteúdo. O JSON marca explicitamente essa limitação;
não orientar captura por botão Y antes de resolver a transferência.

O campo de controle `+$1C` é produzido por `83:8000`: passa a máscara
lógica `$4000` a `83:8059` e grava o retorno. O resolvedor procura essa
ação nos words de configuração Y+0, Y+2 e Y+4, retornando respectivamente
`$0080/$8000/$0040`; se não encontrar, retorna `$4000`. O arquivo local
`Global/Controllers/StandardJoypad.asm` define esses valores como A/B/X/Y.
Logo, o comando corresponde à ação lógica Y, mas sua tecla física depende
do remapeamento. A configuração começa em `KeyConfig_P1AButtonSetting` e
avança `$000C` por registro. Ainda falta confirmar a atribuição do registro
ao jogador e o nome da ação na interface antes de orientar uma captura.

Essa informação está em `anchor_constraint.control_word.button_mapping`.
Não se deve fixar a tecla Y no navegador para reproduzir o teste de `AB38`:
o código nativo consulta a máscara resolvida em `+$1C`.

A chamada `8B:8907`, feita na inicialização de `$12FA`, salva as posições
X/Y da camada 2 em `$1CA6/$1CA8`, salva `$7FFF9E/$7FFFA0` em `$1CAC/$1CAA`
e zera `$1C90`. Em `8B:8989`, a referência mascarada por `$7FFF` fornece
campos de controle; `89AF` usa `XBA; AND #$000F` sobre `$0012,y` para obter
um nibble direcional. Os candidatos de deslocamento usam tabelas
`81:EE9D/EEBD`. Isso liga o mecanismo a um contexto de visualização e input,
mas ainda não identifica o botão nem autoriza chamá-lo de regra de colisão.
O contrato `anchor_constraint.control_word.view_context` preserva as fontes.
Não é necessária outra partida IA × IA para repetir a ausência já observada.

Em 29/10/2026, as sessões `110703` e `111613` criaram arquivos JSONL de
zero bytes. Não há evidência de gameplay aproveitável nesses arquivos.
A causa exata requer o erro do Lua Console; não foi observada diretamente.

O coletor foi alterado para manter um loop explícito com `emu.frameadvance`,
gravar e descarregar um registro `session_start` imediatamente, mostrar
progresso e informar exceções. Essa alteração ainda precisa de validação no
BizHawk. O registro inicial não conta como amostra de gameplay.

Para validar, parar as instâncias antigas do script no Lua Console, carregar
uma única vez `tools/capture_issd_motion_constraints.lua` durante uma partida
e deixar a emulação avançar em velocidade normal. Após os 30 segundos de
preparação, deve aparecer a mensagem de início da coleta; após mais 30 segundos,
o primeiro progresso. Conferir arquivo com registros contendo `actors`
antes de pedir uma sessão longa. O coletor permanece somente leitura da RAM.

As capturas locais foram adicionadas ao gitignore. Os arquivos vazios foram
preservados e a ROM não foi alterada.
