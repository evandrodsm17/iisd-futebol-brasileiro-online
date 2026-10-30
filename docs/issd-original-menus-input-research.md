# Reconstrução dos menus e controles originais do ISS Deluxe

## Diretriz aprovada

Manter a experiência de navegação por joystick: selecionar jogador a sair, confirmar, selecionar reserva, confirmar; menus com D-pad, confirmar/cancelar, Start/Select, sem exigir arrastar-e-soltar. A interface de escalações offline existente permanece como *ferramenta de edição externa*, não substitui a tela de substituição durante a partida.

## Novas referências verificadas

- Projeto independente [issd-native](https://github.com/sergiomanzur/issd-native), arquivo [TEAM_CHANGES_ACCEPTANCE.md](https://github.com/sergiomanzur/issd-native/blob/master/docs/TEAM_CHANGES_ACCEPTANCE.md), registra arrays ativos $7E:3F90/$3FA4 (20 bytes/equipe), seleção de jogador no byte baixo (5 bits), CODE_83:C94F/C9C5 de refresh e byte $A6 para formação. Nosso `dist/data/issd-team-runtime-slots.json` já recuperava a estrutura dos arrays e seleção de 11 atores sem nomear substituições.
- Em [SUBSTITUTION_FLOW_ACCEPTANCE.md](https://github.com/sergiomanzur/issd-native/blob/master/docs/SUBSTITUTION_FLOW_ACCEPTANCE.md), testes nativos por entrada de controle documentam seleção via menu de equipe, pedido por SELECT e admissão numa parada. No retail USA, relatam três substituições aceitas; a quarta é rejeitada, com comparação apontada em CODE_86:A5DC..A5E4. **Essa relação exige replicação local no BizHawk antes de afirmarmos equivalência da implementação web**.
- O disassembly deste repositório já contém `Misc_Defines_ISSD.asm` com `AnnouncerVoiceID_PlayerChange = $0016` e configuração de até quatro controles humanos; o nome da constante não prova sozinho o fluxo de menu.
- O arquivo `AsarScripts/DisassembleUnknownMenuScript.asm` já preserva um decodificador para script de menus $87:ABAA; os opcodes são ainda rotulados `UnknownOpcode` e precisam de classificação com runtime.
- A referência externa é **GPL-3.0**, portanto ideias e achados públicos podem orientar nossas próprias investigações; **não copiar código GPL para a nossa implementação sem revisão de licenciamento**.

## Trabalho incluído nesta PR

- `dist/native-gamepad.mjs`: amostrador puro da Gamepad API para um controle P1 padronizado, com zona morta, arestas de botões, portão neutro após conexão e limpeza ao desconectar. Mapeamento jogável **provisório**, não identificado com botão SNES original e ainda não ativado no motor da partida.
- `dist/native-substitution.mjs`: máquina de estados pura para pedido/espera/parada, seleção de quem sai e entra, cancelamento, retorno e limite inicial de três substituições. **Não é implementação de interface nem altera elenco da partida**.
- `tools/test_native_menu_input.mjs`: testes de lógica sem ROM.

## Próximo experimento no BizHawk (prioridade alta)

1. Iniciar Open Game com equipe contendo pelo menos 3 reservas.
2. Fazer savestate local antes do pedido; registrar frame e ações de SELECT/Start, D-pad, confirmar e cancelar.
3. Gravar bytes $3F90..$3FB7, $1E6C/$1E6E, registros $0D00/$0E00 incluindo $A6, e estado de cena $00C0; registrar prints antes do menu, após selecionar saída, após entrada e após retornar ao jogo.
4. Confirmar empiricamente o limite de substituições, a latência de admissão e como o elenco titular é atualizado.
5. Só depois integrar o estado de substituição ao overlay do jogo, criando navegação exclusivamente por teclas/gamepad; não inventar trocas de atores sem essa verificação.

## Extensões de produto

Multiplayer online e Master Liga (Brasil, América do Sul, Copa do Mundo e expansão europeia) ficam acima do mesmo núcleo determinístico. PostgreSQL mantém campeonatos e temporadas com regulamentos versionados por edição; não colocar regras históricas diferentes dentro do motor de física.

## Teste

```bash
node tools/test_native_menu_input.mjs
```
