# Investigação: nove topologias de controle e telemetria do menu de equipe

## Constantes novas para o projeto

`Misc_Defines_ISSD.asm` define nove `!Define_ISSD_NumOfPlayers_*`, numeradas de `0000` a `0008`: até quatro controles humanos contra CPU, P1 x P2, P1+P3 x P2, P1+P3 x P2+P4, P1+P3+P4 x P2 e CPU x CPU. Os pares de portas são indicados pelo nome simbólico; ainda não foram validados pela execução nativa no BizHawk.

`dist/data/issd-controller-topologies.json` contém os nove mapeamentos, e `tools/verify_issd_controller_topologies.py` confirma os nomes e valores numéricos diretamente na disassembly. Não atribuir cores, joystick físico ou dono da posse a um lado sem uma camada própria de associação.

## Pontos de memória úteis já registrados (revisão)

- `$7E:3F90..3FA3` e `$7E:3FA4..3FB7`: duas matrizes de elenco de 20 bytes.
- `$7E:D864..D877` e `$7E:D878..D88B`: snapshots para comparação.
- `$7E:1E6C` / `$7E:1E6E`: pares de seleção observados no caminho de troca.
- `$7E:00C0`: índice de fase, significado por índice ainda não certificado.
- `$7E:0010`, `$7E:0020`, `$7E:0028`: palavras de entrada P1 utilizadas no capturador de movimento já existente.
- `$0D00+$A6` / `$0E00+$A6`: bytes de registros de equipe, tratados na captura como brutos; validar correlação com a formação no menu.

O `issd-native` de terceiros aponta a rotina `CODE_86:A5C1` e três alterações aceitas. Essa é uma pista de investigação, **não validação independente no nosso runtime**. O projeto externo é GPL-3.0: não foram copiados algoritmos para o nosso repositório.

## Novo experimento no BizHawk

1. Copie `tools/capture_issd_team_management.lua` para um diretório acessível ao BizHawk.
2. Inicie uma partida real na ROM USA e execute o Lua Console. Modifique `output_path` se necessário; o arquivo deve estar em pasta gravável.
3. Execute o script, pressione SELECT para solicitar o menu, navegue nas opções e faça uma substituição **real**: selecionar quem sai e depois quem entra. Repita com a segunda equipe se possível.
4. Use cancelamento, formação e pausa para produzir controles de comparação. O script lê exclusivamente RAM (captura passiva).
5. Gere o relatório:
   `python tools/report_issd_team_management.py issd-team-management-trace.jsonl docs/issd-team-management-observations.json`
6. Testes: `python -m unittest discover -s tools -p 'test_report_issd_team_management.py' -v` e `python tools/verify_issd_controller_topologies.py`.

Não há monitoramento automático contínuo nem evidência de substituição enquanto nenhuma captura nova for executada. Quando o trace estiver disponível, as diferenças por slot, eventos de entrada e alterações de cena poderão ser correlacionados frame a frame.

## Próximas investigações úteis
1. Reconstruir confirmação/cancelamento dos menus, limites de trocas, jogadores inelegíveis, intervalos de substituição e fases.
2. Mapear o conjunto P1–P4 de palavras de entrada com suporte a multitap.
3. Separar a seleção humana de ator (`$1ACC` e ponteiro `$11E8` continuam semanticamente distintos).
4. Identificar a composição **completa** do sprite da bola e suas direções/ângulos em OAM/VRAM, sem confundir um tile parcial com o objeto todo.
5. Depois de evidência suficiente, conectar os fluxos do jogo a botões de joystick; preservar camadas de calendário/competições fora da física original.
