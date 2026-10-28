# Registro de engenharia reversa — ISS Deluxe

Este é o índice humano das descobertas usadas na reconstrução web. Todo dado
novo extraído da ROM, do disassembly ou de uma captura deve ter uma entrada em
Markdown aqui ou no documento temático correspondente, além do artefato
estruturado que o acompanha. A ROM USA permanece local e não é versionada.

## Regra de evidência

| Estado | Critério | Uso permitido no navegador |
| --- | --- | --- |
| Confirmado estaticamente | rotina, tabela ou acesso RAM localizado no disassembly/ROM | dados, limites e fluxo explicitamente observados |
| Confirmado em execução | captura passiva associa o dado a um frame/estado real | composição visual e sequência que a captura cobre |
| Pendente | falta consumidor, polaridade, captura ou transição | não implementar como mecânica final |

Um valor estático não autoriza por si só uma regra jogável. O código web deve
declarar quando mantém um comportamento provisório.

## Índice por sistema

| Sistema | Estado atual | Documento | Dados e ferramentas |
| --- | --- | --- | --- |
| Fluxo, colisão, trajetória e regras | dispatches, gates de regra e fluxo de impedimento parcialmente recuperados | `issd-static-mechanics.md`, `issd-mechanics-roadmap.md` | `issd-dispatch-targets.json`, `issd-dispatch-graph.json`, `issd-handler-flow.json`, `issd-handler-ram.json`, `extract_issd_dispatch_tables.py`, `extract_issd_handler_flow.py` |
| Goleiro | seletor de mergulho, dispatch de retenção, contexto e registros de controle recuperados | `issd-static-mechanics.md` | `dist/data/issd-goalkeeper-context-writes.json`, `dist/data/issd-goalkeeper-catch-records.json`, extratores de contexto/retenção |
| Configuração de partida | normalização e transferência de 12 opções de menu confirmadas | `issd-mechanics-roadmap.md` | `dist/data/issd-match-settings.json`, `dist/data/issd-match-setting-transfer.json`, `dist/data/issd-match-setting-consumers.json`, extratores `extract_issd_match_setting_*.py` |
| Relógio | BCD, tick de 60 frames, offsets, tabelas iniciais e inicialização em `$00A8 = 0` confirmados | `issd-mechanics-roadmap.md` | `dist/data/issd-match-clock.json`, `extract_issd_match_clock.py` |
| Jogadores e animações | ciclos de caminhada/corrida, OAM e descritores parciais recuperados; ações aguardam composição VRAM completa | `issd-animation-inventory.md`, `issd-player-sprite-research.md` | `dist/data/issd-action-*.json`, `extract_issd_locomotion_scripts.py`, `validate_issd_locomotion_assets.py`, `capture_issd_action_vram.lua`, renderizadores OAM/VRAM |
| Estádios e câmera | oito layouts e geometria extraídos; câmera nativa ampla separada como extensão | `issd-mechanics-roadmap.md` | `dist/data/issd-stadium-*.json`, `dist/data/issd-camera-profiles.json`, extratores de estádio |
| Elencos, equipes e uniformes | catálogo USA, formações, paletas e duas opções de uniforme por equipe | `reference-ledger.md` | `docs/issd-rom-catalog.json`, `tools/extract_issd_catalog.py`, ativos em `dist/assets/issd/` |

## Descobertas mecânicas recentes

- `CODE_85:A456` transfere configurações de menu para registros de partida;
  estádio selecionado termina em `$7E:0086`.
- O impedimento lê `$7E:1E4A`, passa por `CODE_80:D627`, recalcula uma linha
  de referência em `CODE_A4:A442` a partir de 11 slots de ator e confirma o
  resultado uma segunda vez. A transição global posterior ainda é pendente.
- O relógio usa BCD; `CODE_A4:9401` só avança após 60 frames elegíveis.
  `CODE_83:B02C` zera `$00A8`, selecionando inicialmente `$81:E893`.
- O goleiro possui um seletor de mergulho (`$14A8`, três entradas) e uma
  tabela de nove handlers de retenção indexada por `A`; `$1500` é contexto em
  `Y`, não o seletor da tabela. A tabela altera `$B2/$B6` e temporizadores;
  ambos usam os blocos `$0D00/$0E00`.
- A bola possui dois blocos de trajetória (`$08A0/$08D0`) com seis handlers
  temporizados e índices observáveis em `$7E:08CE/$7E:08FE`.
- Caminhada e corrida usam durações da ROM: caminhada com 10 poses de 3 ticks
  e corrida com 8 poses de durações `4,3,3,3,4,3,3,3`.

## Atualização obrigatória

Ao concluir uma nova investigação, registrar:

1. fonte exata: ROM/endereço, rótulo do disassembly ou captura;
2. o que foi comprovado e o que continua pendente;
3. artefato gerado e comando/teste usado;
4. efeito aplicado — ou explicitamente não aplicado — no navegador.

O resumo desta página não substitui os documentos temáticos: eles preservam o
contexto e as limitações necessárias para implementar a mecânica com fidelidade.

## Verificação

Execute `python tools/verify_issd_documentation.py` após alterar extratores,
artefatos de mecânica ou esta documentação. O verificador garante a presença
do índice, dos documentos mecânicos, dos metadados de fonte/limitação e dos
artefatos essenciais de configuração e relógio; ele não substitui a revisão
humana da evidência.
