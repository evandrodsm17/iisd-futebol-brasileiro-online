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
