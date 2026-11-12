# Nostalgia Soccer HD

Este repositório reúne a investigação de *International Superstar Soccer Deluxe*
e a construção de um jogo para navegador baseado em suas mecânicas, animações
e fluxo. A prioridade é reproduzir o comportamento original com evidências da
ROM; widescreen, câmera mais ampla, clubes e multiplayer são extensões do projeto.

## Estado atual

- **Partida local:** o fluxo passa por menu, seleção de equipes em grupos,
  uniformes com prévia, estádio e configurações. A partida permite movimentar,
  conduzir, passar e chutar, além de testar desarmes, goleiro e reinícios.
  Colisões, posse, saídas, regras e parte da física ainda são provisórias.
- **Gráficos e animações:** a locomoção e algumas ações são compostas com dados
  derivados da referência; há cobertura parcial para passe, chute, carrinho,
  reações, lateral e goleiro. Nem todas as poses e transições estão validadas
  para todas as circunstâncias da partida. O [laboratório de animações](dist/editor/locomotion-lab.html#action-lab)
  permite examiná-las sem jogar.
- **Chute:** a trajetória vertical do jogador usa valores de tabelas nativas
  tipo 5 com uma escala e seleção de força provisórias. A conversão de unidades,
  direção horizontal, contato, quique e a escolha de força da CPU ainda precisam de
  calibração; os números não demonstram equivalência completa com a ROM.
- **Online:** há um teste experimental para dois participantes com sala e
  troca de comandos. Não é uma partida completa nem um servidor autoritativo.
  Veja o [guia multiplayer](docs/como-jogar-multiplayer.md) para a lista de
  ações disponíveis e limitações.
- **Editor:** já existe um editor local de conteúdo; clubes, competições,
  temporadas e persistência compartilhada ainda não compõem o produto final.

O projeto final prevê modo local com clubes, calendário e competições, além de
multiplayer com divisões. O servidor online com banco de dados e a persistência
local são objetivos de arquitetura, não recursos completos disponíveis hoje.

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

Na partida local, os controles padrão são setas para mover, **E** para correr,
**A** para chutar, **E + A** para chute alto, **X** para passe ou pressão sem
posse, e **Q** para trocar de jogador. O menu permite personalizá-los. Passe
enfiado (**W**) e cruzamento (**D**) ainda estão reservados para implementação;
o teste online possui restrições adicionais descritas no guia.

## Testes principais

```powershell
npm run test:server
node dist/test-goalkeeper-model.mjs
node dist/test-match-flow.mjs
node --test dist/test-native-shot-type5.mjs
```

O teste do servidor atualiza primeiro a identidade da versão. Alguns testes
nativos conferem dados locais de ROM e capturas quando disponíveis; sem esses
arquivos, as verificações correspondentes são ignoradas. O teste opcional
`npm run test:online-browser` usa navegadores ocultos e está descrito na
[documentação do servidor](docs/server-foundation.md#validação).

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

## Próximos passos prioritários

- Relacionar coordenadas, velocidades, altura e tempo da ROM às unidades web,
  comparando trajetórias em mais direções e condições antes de calibrar a bola.
- Reconstruir contato, posse, carrinho, faltas e reinícios junto às respectivas
  animações e máquinas de estado, distinguindo evidência de aproximação.
- Validar traves, goleiros, chutes e quiques em situações comparáveis à referência.
- Completar progressivamente a simulação compartilhada e o fluxo online, antes
  de tratar o teste atual como partida multiplayer completa.

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
