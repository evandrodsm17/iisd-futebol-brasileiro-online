# Contrato de dados do editor de conteúdo

## Objetivo

O editor cria pacotes próprios para expandir o jogo com clubes, jogadores,
uniformes, estádios e competições. O pacote não contém ROM, bytes extraídos ou
assets de terceiros sem licença. Os dados da ROM continuam somente como uma
fonte de referência para a simulação e para o catálogo inicial auditado.

## Envelope do pacote

Todo pacote possui:

- `schema_version`: versão inteira do formato;
- `package_id`: identificador estável, único no ambiente de conteúdo;
- `revision`: revisão monotônica do pacote;
- `clubs`, `players`, `stadiums` e `competitions`: coleções próprias;
- `assets`: referências relativas ao pacote, nunca caminhos locais absolutos;
- `metadata`: autoria, licença e proveniência dos dados autorais.

Uma partida e um save de temporada registram `package_id`, `revision` e hash
canônico do pacote validado. Clientes multiplayer devem concordar nesses três
valores antes da simulação começar.

## Entidades mínimas

| Entidade | Identidade | Relações e regras mínimas |
| --- | --- | --- |
| Clube | `id` | nome, país, cores, escudo opcional, pelo menos um uniforme |
| Jogador | `id` | clube ativo opcional, nome, posição, camisa, aparência e atributos estruturados |
| Uniforme | `id` dentro do clube | tipo, camisa/calção/meias, cores e variante de goleiro quando aplicável |
| Estádio | `id` | nome, dimensões lógicas, apresentação e referências de assets |
| Competição | `id` | regulamento versionado, participantes e calendário/regras próprios |

IDs não podem depender de posição em lista, nome exibido ou arquivo de imagem.
Renomear clube/jogador não pode quebrar uma temporada salva.

## Regras de validação inicial

1. IDs são únicos por coleção e seguem `^[a-z0-9][a-z0-9-]{1,63}$`.
2. Toda referência de jogador a clube existente é resolvida antes de exportar.
3. Todo clube tem `home` e `away`; uniformes adicionais são permitidos.
4. Cores de uniforme são hexadecimais de seis dígitos e são normalizadas antes
   de medir contraste.
5. Arquivos de asset são caminhos relativos, sem `..`, URL externa ou caminho
   absoluto.
6. Campos de licença e autoria não podem ficar vazios quando o pacote contém
   conteúdo autoral novo.
7. O validador não interpreta atributos como física da ROM; regras de partida
   só são consumidas pelo motor quando tiverem um contrato de simulação próprio.

## Evolução

Mudanças incompatíveis exigem incremento de `schema_version` e migração
reversível. Campos desconhecidos devem ser preservados por importação/exportação
para que uma versão antiga do editor não destrua dados mais novos. A primeira
interface do editor é local e offline; sincronização, catálogo público e
colaboração são camadas posteriores.
