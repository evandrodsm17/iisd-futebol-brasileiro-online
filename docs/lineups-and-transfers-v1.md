# Escalações e transferências entre clubes — primeira integração

O editor de conteúdo agora oferece `dist/editor/lineups.html` (link na página principal do editor). A página lista equipes da ROM com nomes/atributos modificados e clubes autorais do IndexedDB; salva formação e titulares em `localStorage`, e também permite transferências entre essas duas fontes.

## Funcionamento

- Formações disponíveis: 4-4-2, 4-3-3, 4-2-3-1 e 3-5-2. Os dez outfield slots são projetados como posições provisórias do Canvas, NÃO são dados ROM recuperados.
- Até onze titulares distintos escolhidos da equipe corrente. O botão **Salvar** exige onze; a ordem usada inicialmente segue a ordem do elenco listado, incluindo o goleiro como primeiro por convenção.
- O motor recebe elenco reordenado e a formação selecionada ao **recarregar a partida**. Só a partida usa jogadores temporários quando um elenco tem menos de onze atletas; eles não vão para o banco nem para o pacote exportável.
- Transferências não apagam nem duplicam os registros de origem. Jogadores ROM são identificados por `rom:<source-team>:<slot>`; os autorais usam `custom:<id>`. Transferências permanecem numa camada independente (`issd-team-transfers-v1`).
- Escalações ficam na chave `issd-team-lineups-v1`. O catálogo ROM e os pacotes autorais não são alterados permanentemente.
- Os dados podem ser migrados futuramente para `club_memberships` e para tabelas de tática no PostgreSQL.

## Testes

```bash
node tools/test_lineups.mjs
node tools/test_content_editor.mjs
node dist/editor/test-rom-overrides.mjs
node --check dist/editor/lineups.js
node --check dist/game.js
```

## Limitações e alertas

A tela ainda não possui drag-and-drop ou escolha independente de posição dos onze jogadores; o alinhamento usa a ordem dos titulares selecionados no elenco. Também não há substituições durante a partida, banco de reservas controlável, mercado com propostas/contratos, transferência de atletas entre pacotes autorais salvos ou servidor PostgreSQL executando. A transferência entre fontes usa composição local e requer atenção à origem de um jogador no editor de atributos da ROM. O editor precisa de teste funcional no Chrome antes de ser tratado como pronto para produção.

Esta PR é isolada e não altera a ROM do jogo.
