# Editor de elenco — atributos e transferências

Esta fase expande a PR #10 já mesclada, sem alterar arquivos da ROM ou exigir PostgreSQL ligado.

## Funcionalidades
- Na página `dist/editor/rom-catalog.html`, cada jogador possui nome, camisa, posição, nove atributos (1–99) e seleção de equipe.
- Transferir muda o elenco de destino na próxima carga do jogo e **preserva a chave de origem** (`team_id` + `slot`), necessária para saves e importação.
- O próprio time que perdeu o jogador deixa de listá-lo; os novos atletas entram depois dos integrantes originais do destino. Ordem de escalação e transferências entre clubes autorais são melhorias posteriores.
- Restaurar jogador desfaz tanto transferência quanto atributos/nome/camisa daquele atleta. Restaurar todos limpa overrides.
- Importação e exportação continuam usando JSON de `schema_version:1`. Nomes salvos na versão anterior continuam compatíveis.
- Para um time ficar com menos de onze atletas, a partida usa atletas temporários de fallback; não tenta alterar escalação automaticamente.

## Estrutura futura de banco de dados
Migração `database/migrations/002_rom_catalog_edits.sql` registra histórico de alterações de catálogo e filas de importação. Os atributos e o destino permanecem dentro de metadados editáveis, ainda não sincronizados. A futura API deverá validar transacionalmente cada transferência, disponibilidade e contrato de conteúdo. Nenhuma migração foi executada em PostgreSQL real.

## Testes
```bash
node dist/editor/test-rom-overrides.mjs
node --check dist/editor/rom-editor.js
node --check dist/game.js
```

No navegador: escolha uma seleção, edite o atleta, salve, confirme que ele aparece no novo elenco e recarregue o jogo para verificar os nomes. Teste também a exportação e importação do JSON.

## Limitações
Os atributos são metadados do jogador. O motor físico atual ainda não consome todos eles. O editor não oferece transferências para clubes autorais, escalação titular personalizada ou histórico online. Nada foi colocado em produção automaticamente.
