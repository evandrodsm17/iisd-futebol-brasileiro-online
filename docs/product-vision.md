# Visão de produto

## Propósito

O produto final moderniza a partida do International Superstar Soccer Deluxe para o navegador, preservando a simulação comprovada da ROM. Além das seleções da ROM, oferecerá clubes, modo local completo e multiplayer online.

## Modo local

O modo local deve suportar clubes, escalações, uniformes, calendário, temporadas, competições nacionais, copas nacionais, competições sul-americanas e promoção/rebaixamento.

## Multiplayer online

O multiplayer usa a mesma simulação determinística do modo local. Rede, matchmaking, divisões, classificação e ranking são camadas de serviço; não podem introduzir física ou regras diferentes da partida local.

## Competições e temporadas

O motor de competição deve ser genérico e suportar divisões, liga, grupos, mata-mata, ida/volta, final única ou em dois jogos, classificação para copas, vagas continentais, promoção, rebaixamento, calendário, descanso, suspensões, elenco, histórico e transição de temporada.

## Regras reais

Toda regra real deve apontar para uma edição de temporada e fonte normativa. Formato, vagas, desempates e acesso/rebaixamento mudam entre anos. Portanto cada temporada deve possuir regulamento versionado, vigência, fonte e testes de simulação; nenhuma regra deve ser tratada como universal sem essa versão.

## Editor de conteúdo

O produto incluirá um editor próprio, inspirado no fluxo de edição presente nas
ferramentas de referência adicionadas ao projeto, mas orientado à base de dados
do navegador. Ele deve permitir criar, importar, editar, validar e remover:

- clubes, identidades, apelidos, país/estado/cidade, cores e escudos;
- jogadores, nomes, posição, número, atributos, aparência, pé dominante,
  cabelo, tom de pele e vínculo com elenco;
- uniformes titular, reserva e adicionais, incluindo cores, padrões, números,
  goleiro e regras automáticas de contraste entre adversários;
- escalações, formações, banco, comissão técnica e disponibilidade;
- estádios, dimensões lógicas, identidade visual, câmera, gramado, clima e
  recursos de apresentação;
- competições, regulamentos versionados, calendário, participantes, vagas,
  promoção/rebaixamento e saves de temporada.

O editor não modifica a ROM de referência e não depende dela em produção. A
ROM e a disassembly permanecem fontes de comportamento para o núcleo fiel; os
dados autorais novos são registros do produto, exportáveis/importáveis em um
formato versionado e sujeitos a validação antes de entrarem em uma partida ou
temporada.

O primeiro recorte do editor deve ser local/offline e determinístico: uma
edição de dados gera um pacote validado, com identificadores estáveis e versão
de esquema. Multiplayer só aceita pacotes compatíveis, identificados por hash,
para que clientes não disputem uma partida com elenco, uniforme, estádio ou
regulamento diferentes.

## Fronteira de arquitetura

| Camada | Fonte de verdade |
| --- | --- |
| Simulação de partida | ROM, disassembly e capturas |
| Widescreen | adaptador de apresentação sem alterar a simulação |
| Clubes, jogadores e escudos | base de dados do produto |
| Competições e temporadas | regulamentos versionados |
| Editor de conteúdo | pacote de dados versionado e validado |
| Multiplayer | protocolo determinístico sobre a partida local |

Clubes e regulamentos não são dados da ROM. Nomes, escudos, elencos e fontes de terceiros dependem de licença e direito de distribuição adequados.

## Ordem de construção

1. Concluir o núcleo de partida fiel e determinístico.
2. Definir o esquema e o pacote versionado de clube, jogador, uniforme, estádio e save de temporada.
3. Construir o editor local desses dados, com validação e importação/exportação.
4. Implementar o motor de competição e regulamentos versionados.
5. Construir a primeira temporada nacional no modo local.
6. Adicionar online, reconexão, integridade de resultado, divisões e ranking.
