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

## Fronteira de arquitetura

| Camada | Fonte de verdade |
| --- | --- |
| Simulação de partida | ROM, disassembly e capturas |
| Widescreen | adaptador de apresentação sem alterar a simulação |
| Clubes, jogadores e escudos | base de dados do produto |
| Competições e temporadas | regulamentos versionados |
| Multiplayer | protocolo determinístico sobre a partida local |

Clubes e regulamentos não são dados da ROM. Nomes, escudos, elencos e fontes de terceiros dependem de licença e direito de distribuição adequados.

## Ordem de construção

1. Concluir o núcleo de partida fiel e determinístico.
2. Definir dados de clube, jogador, uniforme, estádio e save de temporada.
3. Implementar o motor de competição e regulamentos versionados.
4. Construir a primeira temporada nacional no modo local.
5. Adicionar online, reconexão, integridade de resultado, divisões e ranking.
