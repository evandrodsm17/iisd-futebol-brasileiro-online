# International Superstar Soccer Deluxe — projeto web

Este repositório abriga o trabalho de pesquisa e reconstrução de uma experiência
inspirada em *International Superstar Soccer Deluxe*, atualizada para navegador
com uma câmera longa que mostre a maior parte do campo.

## Material local

A ROM de referência é mantida somente na máquina de desenvolvimento em
`International Superstar Soccer Deluxe/` e é ignorada pelo Git. Ela não é parte
do projeto distribuído nem deve ser publicada.

## Executar o servidor de desenvolvimento

Com Node.js 20 ou mais recente instalado, execute na raiz do projeto:

```powershell
npm install
npm start
```

Abra [http://127.0.0.1:4173/](http://127.0.0.1:4173/). O servidor é local e
mantém as funções offline do navegador. Para usar outra porta, por exemplo se
o servidor Python já estiver usando a 4173:

```powershell
$env:PORT=4174
npm start
```

O servidor inclui salas e um teste online de movimentação, condução e passe para duas pessoas;
a partida completa e o PostgreSQL ainda não estão conectados. O endpoint
`/api/v1/status` informa as capacidades disponíveis. O comando anterior
`python tools/serve_local.py` continua disponível para servir os arquivos sem a
API. Para jogar com outra pessoa, consulte [Como jogar o teste multiplayer online](docs/como-jogar-multiplayer.md). Detalhes técnicos e próximos passos em [docs/server-foundation.md](docs/server-foundation.md).

## Ferramentas de pesquisa

O REA está registrado no Codex como servidor MCP. Reinicie o Codex antes da
primeira análise para que a integração seja carregada.

No Windows, a análise profunda de binários pelo REA requer configurar um provedor
nativo compatível, como o Ghidra. Sem esse provedor, ainda é possível usar as
inspeções estáticas que não dependem de descompilador.

## Registro de descobertas

[`docs/issd-reverse-engineering-log.md`](docs/issd-reverse-engineering-log.md)
é o índice obrigatório das descobertas de lógica, mecânica, gráficos e dados.
Cada extração deve registrar fonte, evidência, pendências, artefatos e testes;
os documentos temáticos preservam o detalhamento de cada subsistema.

Para implementar ou revisar o motor, use também a
[`docs/issd-reconstruction-spec.md`](docs/issd-reconstruction-spec.md): ela
consolida os contratos confirmados, as limitações de evidência e a ordem de
reconstrução sem transformar comportamento provisório em mecânica fiel.

A visão de produto de longo prazo está em
[`docs/product-vision.md`](docs/product-vision.md): clubes, temporadas,
competições nacionais e sul-americanas, promoção/rebaixamento, modo local e
multiplayer online sobre o mesmo núcleo determinístico. Ela inclui também o
editor de conteúdo para clubes, jogadores, uniformes, estádios, competições e
temporadas, sempre separado da ROM de referência.

O planejamento de física, eventos de partida e animações está no
[`docs/issd-checklist-fisica-animacoes.md`](docs/issd-checklist-fisica-animacoes.md).
As alternativas para exibição em alta resolução e arte HD estão em
[`docs/issd-resolucao-grafica.md`](docs/issd-resolucao-grafica.md).

O contrato inicial desse editor está em
[`docs/content-editor-contract.md`](docs/content-editor-contract.md). Um pacote
local pode ser validado com `python tools/validate_content_package.py`.
Acrescente `--print-hash` para obter a identidade canônica usada por saves e
futuro multiplayer.

## Direção inicial

- Preservar a sensação de futebol arcade do jogo de referência.
- Produzir uma implementação original para navegador; não distribuir conteúdo da ROM.
- Projetar a câmera para uma visão longa, com boa leitura das linhas e jogadores.

## Catálogo da ROM

`docs/issd-rom-catalog.json` é uma exportação auditável da edição USA de
referência: 36 seleções, 20 jogadores por seleção, atributos, aparência e
formações. Não contém a ROM. Para regenerá-lo a partir da cópia local:

```powershell
python tools/extract_issd_catalog.py `
  "International Superstar Soccer Deluxe/International Superstar Soccer Deluxe (USA).sfc" `
  docs/issd-rom-catalog.json
```

O extrator confere o MD5 da revisão suportada antes de escrever, mantendo a
base de menus, escalações e futuras partidas conectada ao dado original.

## Editor de clubes e conteúdo próprio

No menu inicial, selecione **MODO DE EDIÇÃO** e confirme para abrir [o Editor de Conteúdo](dist/editor/index.html). Ele permite criar clubes, gerenciar jogadores, importar PNGs de escudos e estádios, escolher cores e padrões de uniformes, armazenar dados no navegador e exportar/importar pacotes ZIP. [Manual](docs/content-editor-guide.md).

Para jogar, selecione **NOVO JOGO**, escolha as equipes pelas páginas de grupos
e avance para os uniformes, com prévia do jogador parado. Depois escolha estádio
e configurações antes de iniciar a partida. É possível voltar entre as etapas
sem perder as escolhas. A página das Américas segue a ordem da referência; os
nomes das demais páginas são uma organização provisória do catálogo. O menu indica os modos ainda não implementados;
as opções de regras exibidas na preparação não significam que todos os seus
efeitos já estejam reproduzidos no motor.
