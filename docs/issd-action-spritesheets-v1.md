# Pacote de spritesheets de ações v1

A versão portátil foi gerada em `ISSD-Spritesheets-Acoes-v1.zip` e entregue no chat. Este documento registra o contrato para importar o pacote ao repositório **sem substituir o motor**.

## Conteúdo verificado

- 11 folhas horizontais de 576×96 PNG RGBA, seis quadros de 96×96 por folha.
- 6 direções para `D007` (0, 2, 3, 4, 6, 7); 5 direções para `D100` (0, 2, 3, 4, 6).
- 66 PNGs individuais; âncora comum (48,68).
- `issd-action-manifest.json` com `actions[script].directions[direction].sheet`, `descriptors`, `sourceFrames`, `timing.observedTransitionFrames`, `timing.previewDurationFrames` e `rendering`.
- `index.html`, `issd-action-tester.html`, `js/issd-action-runtime.mjs` e testes.
- `quality-report.json` lista possíveis resíduos sem apagar componentes do jogador.

## Instalação local

Extraia a pasta do pacote em `dist/action-lab`. Abra `dist/action-lab/index.html` para verificar a animação no navegador. Não inclua assets automaticamente no renderer principal; este material tem status `diagnostic-awaiting-visual-validation`.

```powershell
node dist/action-lab/js/test-action-runtime.mjs
```

## Restrições

As poses resultam de agrupamento heurístico de OAM. Não inferir animações para direções ausentes, não transformar `D100` em passe confirmado e não usar o último intervalo de 4 frames como timing real: é somente preview. A captura ainda não confirma em qual frame a pose final termina. Validar manualmente os slots com resíduos antes de liberar sprites HD definitivos.

O pacote binário continua **separado do repositório** até ser enviado e revisado. A PR contém somente estas instruções de integração e não altera `dist/game.js`.
