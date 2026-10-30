# Editor de clubes e jogadores + preparação de banco (v1)

## Já implementado

O editor que existia em `dist/editor/index.html` continua responsável por criar clubes, elencos, escudos, uniformes e estádios **autorais**. Nova rota: `dist/editor/rom-catalog.html` para editar os nomes das **36 equipes e 720 jogadores** do catálogo extraído da ROM (20 por equipe), sem alterar seus atributos, IDs ou bytes originais.

- A tela lista equipes, permite busca, altera nome de clube e nome de jogador, restaura originais e exporta/importa alterações JSON.
- Uma camada de substituições usa identidade `(team_id, slot)`, independente do nome, e persiste em `localStorage` (chave `issd-rom-catalog-overrides-v1`).
- `dist/game.js` aplica a camada ao carregar `issd-rom-catalog.json`, para exibir nomes editados na escolha das equipes e escalações. É necessário recarregar a partida para refletir alterações do editor.
- O editor de conteúdo autoral usa IndexedDB e ZIP, separadamente; as alterações da ROM ficam em JSON próprio, de modo que importar um ZIP não as sobrescreva.

## Banco de dados futuro

`database/migrations/001_initial.sql` contém PostgreSQL DDL para `clubs`, `players`, `stadiums`, `club_memberships`, `kits`, `content_packages`, `competitions`, `seasons`, `season_teams` e `matches`.

O banco **não está ligado à aplicação** e a migração **não foi executada em servidor real**. O formato SQL inclui UUID para IDs estáveis, histórico de vínculo do jogador ao clube, índices e relações com integridade referencial. Uma segunda etapa definirá API e migrações que tragam os pacotes v1 do navegador para PostgreSQL.

### Escolha de arquitetura

- **Agora:** editor local no navegador, sem servidor, com exportação de JSON (nomes) e ZIP (conteúdo autoral).
- **Depois:** API Node e PostgreSQL como fonte de verdade para contas, competições, transferências e dados compartilhados. Importações devem ser transacionais e nunca regravar a ROM.
- **Multiplayer:** o catálogo usado pelo motor deverá ter versão/hash de conteúdo para sincronização de dados entre participantes.

## Teste local

Sirva a pasta `dist` por HTTP; na tela inicial, abra Editor → **Editar nomes das equipes e dos jogadores originais**. Troque nomes e recarregue o jogo.

```bash
node dist/editor/test-rom-overrides.mjs
node --check dist/editor/rom-editor.js
node --check dist/game.js
```

A PR precisa de validação manual em navegador antes do deploy. O esquema PostgreSQL exige uma base separada de desenvolvimento para ser testado; não execute migrações diretamente em produção sem backup.

## Limitações desta fase

Atributos e transferências dos jogadores originais ainda não são editáveis; as equipes autorais e as 36 seleções originais continuam em sistemas de dados distintos. Não existem login, sincronização, API, servidor nem banco em execução nesta fase. A importação de JSON não deve ser considerada segura para publicação sem validação no backend futuro.
