# Captura de restrições de movimento

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
