# International Superstar Soccer Deluxe — projeto web

Este repositório abriga o trabalho de pesquisa e reconstrução de uma experiência
inspirada em *International Superstar Soccer Deluxe*, atualizada para navegador
com uma câmera longa que mostre a maior parte do campo.

## Material local

A ROM de referência é mantida somente na máquina de desenvolvimento em
`International Superstar Soccer Deluxe/` e é ignorada pelo Git. Ela não é parte
do projeto distribuído nem deve ser publicada.

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
