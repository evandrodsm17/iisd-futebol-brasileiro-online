# Automação inicial de partida — 02/11/2026

## Resultado observado

Foi iniciada uma instância própria do BizHawk com janela oculta, ROM local e
`tools/automate_issd_probe.lua`. A sequência experimental de pulsos navegou
até uma partida: a imagem de teste no frame 3600 mostra Inglaterra × Brasil
em campo, e o campo `$11E6` registrado é 0 (modo 1 × CPU no disassembly).
As instâncias usadas no experimento foram encerradas ao término; não houve
interação com a tela nem alteração da ROM.

A primeira tentativa enviava nomes `P1 Start` com o argumento de controle 1;
o registro de entrada permanecia zero nos pulsos observados e a partida
apresentada podia ser demonstração. Com nomes sem prefixo (`Start`, `A`,
`Right`, `B`) e controle 1, os registros confirmaram `held_p1=$1000` para
Start, `$0080` para A e `$0100` para Right. O campo de entrada é evidência
de botão recebido, não de efeito esportivo específico.

Dois experimentos concluídos:

- 9.000 passos, 4.500 amostras; 900 amostras com Right e slot de ator
  válido, mas a imagem de 7200 mostra uma reposição próxima ao gol. Relatório
  `docs/issd-automated-probe-summary.json`.
- 4.800 passos, 2.400 amostras; a pressão de Right ocorreu entre passos
  3600 e 3898, com 150 amostras de slot válido. Relatório
  `docs/issd-automated-motion-probe-summary.json`.

Na segunda execução, `$1ACC=$0E00` e as coordenadas inteiras capturadas
passaram de `(160,136)` no passo 3600 a `(168,136)` no passo 3620, mas
permaneceram `(168,136)` nas amostras posteriores até 3898. Ainda não
sabemos se o ponteiro, o estado da partida ou a interpretação das
coordenadas explica essa interrupção. Os números são registrados sem
concluir velocidade, resposta de controle ou fidelidade da física.

## Instrumentos e limites

O script injeta entradas de teste e lê WRAM; não modifica a ROM nem a RAM do
jogo. Registra modos, entrada recebida, configuração de jogadores, ator
candidato, bola e vínculos a cada dois passos, além de screenshots a cada
600. Usa nomes de arquivo únicos em `analysis/` (ignorado pelo Git); a
variável `ISSD_AUTO_OUTPUT_DIR` pode indicar outro diretório existente.
O script não identifica sozinho um evento ou uma condição segura para
medir. O fechamento da instância é feito pelo processo que a iniciou.

`tools/analyze_issd_auto_probe.py` gera resumos com hash dos traces locais;
`tools/test_issd_auto_probe.py` cobre integridade básica e contagem de
entradas. Os traces e screenshots são evidência local, não distribuição da
ROM. O script foi executado duas vezes com sucesso após corrigir as entradas.

## Próxima etapa

### Movimento humano quando o vínculo da bola aponta ao outro time — 02/11/2026

O cenário `ISSD_AUTO_SCENARIO=opponent_link` espera um ator válido associado
ao controle físico e um `$00A6` válido de equipe diferente; nesse momento,
salva uma imagem e envia Right, Left, Up e Down ao P1 em sequência. O teste
tem limite de 10.000 passos e registra se encontrou candidato. A condição é
um **indício para seleção do experimento**, não uma definição universal de
posse. A imagem do teste fica em
`analysis/issd-auto-probe-20261102-163255-candidate.png`; nela há jogadores
próximos e a posse não pode ser estabelecida com segurança apenas pela imagem.

O candidato ocorreu no passo 4175, com ator controlado `$0E00` e vínculo
`$1A00`, de registros de equipe diferentes. A execução terminou os 10.000
passos em instância oculta, depois encerrada. Foram registrados 45 amostras
de controle ativo por direção. Enquanto `$00A6` apontava para um ator
diferente do controlado, houve mudanças na posição inteira/fracionária em
28 pares consecutivos para Right, sete para Left, nove para Up e oito para
Down. O vínculo pode mudar durante cada trecho: as contagens são por amostra,
não significam posse adversária contínua durante toda a sequência.

Os resumos com hash estão em `docs/issd-auto-opponent-link-summary.json` e
`docs/issd-auto-opponent-probe-summary.json`. Os analisadores aceitam o evento
de gatilho sem confundi-lo com amostra; quatro testes passaram. Não há ainda
prova visual suficiente para chamar o instante de posse da CPU, nem dados
para converter movimento ao Canvas. Próxima etapa: acompanhar por frame a
bola, os dois atores e suas distâncias/estados, com screenshots ao longo da
sequência, para distinguir condução adversária de outros vínculos.

### Registro separado do controle e dos atores — 02/11/2026

O script schema v2 agora registra os cinco registros de controle e os 22
slots de atores, incluindo coordenadas inteiras e fracionárias. Os comandos
Right, Left, Up e Down são enviados pelo controle P1 **sem verificar posse
de bola**. `tools/analyze_issd_auto_control.py` acompanha o ator apontado
por `+$2C` do registro `$1AA0`, além do candidato `$1ACC` e do vínculo
`$00A6`. Isso separa o jogador associado ao controle do jogador relacionado
à bola; `$00A6` não foi validado como definição universal de posse.

Na execução `analysis/issd-auto-probe-20261102-162636.jsonl`, foram
registradas 60 amostras em cada direção. O controle `$1AA0` apontou para
`$0E00`, com entrada não zero nas quatro direções. Entre 59 pares consecutivos
por direção, as palavras de posição inteira/fracionária mudaram em 55
(Right), 52 (Left), 56 (Up) e 51 (Down). Isso esclarece a observação anterior:
olhar somente as coordenadas inteiras não mostrava todas as mudanças. Ainda
não há conversão de unidades, comparação causal com um estado repetido nem
medida de velocidade que possa ser aplicada ao navegador.

Nessa coleta, `$00A6` apontou para o mesmo ator durante os comandos. Uma
segunda tentativa, `analysis/issd-auto-probe-20261102-162848.jsonl`, enviou
B antes das direções, mas não demonstrou transferência para outro ator;
as contagens de movimento permaneceram iguais. Portanto **a situação de
CPU com a bola ainda não foi validada**. As saídas resumidas com hashes são
`docs/issd-auto-control-summary.json` e
`docs/issd-auto-control-action-summary.json`. Capturas brutas ficam em
`analysis/` e as instâncias de teste foram encerradas.

Dois testes de `test_issd_auto_control.py` verificam mudança na parte
fracionária, ponteiros diferentes e rejeição de passos repetidos. A auditoria
documental passou. Nenhuma constante da mecânica web foi alterada.

Próximo passo: criar uma sequência que aguarde durante a partida até o vínculo
relacionado à bola ser diferente do ator do controle, sem usar isso como
prova isolada de posse, e então executar movimentos. Correlacionar imagem,
estado e vínculo para confirmar visualmente a CPU com a bola; se esse evento
não ocorrer dentro do limite, registrar a tentativa sem fabricar resultado.

Capturar, no mesmo experimento e em todos os atores, os campos de controle
`$1AA0..$1B60`, ponteiro do ator em `+$2C`, flags `+$2E`, `$1ACC`, estados
e coordenadas inteiras/fracionárias; verificar qual registro realmente
recebe o controle e por que a posição observada ficou parada. Comparar
repetições de sequências neutra/direita a partir de um estado reproduzível
antes de converter unidades ou alterar a velocidade web. Não é necessário
pedir ao usuário que repita caminhada nesta etapa.
