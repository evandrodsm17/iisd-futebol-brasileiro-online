# Roteiro de mecânica fiel — ISS Deluxe

## Pontos de entrada confirmados

| Sistema | ROM / RAM | Papel |
| --- | --- | --- |
| Fase principal | `$7E:00C0` → `$83:CF86` | Dispatch de 15 fases da partida |
| Fase secundária | `$83:F375` | Continuação do dispatch de fase |
| Colisão/física | `$83:D77F` | Modos de colisão e bola |
| Trajetória | `$83:D9A5` | Bola, trave e rede |
| Mergulho GK | `$83:DCAA` | Defesa baixa/alta do goleiro |
| Captura GK | `$83:DDA1` | Segurar e proteger a bola |
| Sequenciador de jogador | `$84:A35F` | Seleção/composição de animação |

## Ordem de reconstrução

1. Registrar fase e registros de bola/jogador ao longo de jogo natural.
2. Substituir posse e bola livre pelo modo de colisão observado.
3. Ligar passe/chute às trajetórias observadas.
4. Integrar goleiro, rede e trave.
5. Tratar faltas, reinícios e cartão pelo dispatch de fase.

Nenhuma etapa promove uma regra do protótipo a comportamento final sem uma
rotina, tabela ou captura correspondente da ROM USA.

O código web atual mantém bola livre, posse por proximidade, atrito, quique e
reinícios apenas para que a tela de partida seja navegável. Eles não são
equivalentes à máquina da ROM e devem ser substituídos — e não ajustados por
sensação — conforme os handlers e registros forem recuperados.

## Projeção e geometria confirmadas para a próxima telemetria

O capturador passivo passa a registrar `stadium.layout` em `$7E:0086`, o
comprimento/largura nativos em `$7E:12A2/$7E:12A4` e a origem de câmera em
`$7E:13A0/$7E:13B0`. A alteração corrige a leitura anterior de câmera em
`$00A0/$00A2`, que não era a origem de visualização do jogo.

O leitor de recursos do `issd-native` confirma que os oito layouts originais
usam comprimentos `1792, 1856, 1984, 2048, 1920, 1920, 1792, 2176` e larguras
`576, 640, 704, 640, 640, 576, 704, 704`, extraídos da tabela ROM
`$81:EC47`. Esses valores serão usados apenas depois de aparecerem numa nova
telemetria; não serão aplicados retroativamente ao traço que não os registrou.

`tools/extract_issd_stadium_geometry.py` valida essa tabela diretamente na
ROM USA headerless e grava apenas os pares decodificados em
`dist/data/issd-stadium-geometry.json`. A ROM e seus bytes não entram no
repositório nem na distribuição web.

Os oito previews visuais extraídos estão em
`dist/assets/issd/stadium/layout-0.png` até `layout-7.png`, cada um com seu
manifesto de MD5/layout/dimensões. A tela de configuração web já permite
selecioná-los pelos mesmos índices de `StadiumIDs`; para a ROM USA, o estado
inicial é o layout 1.

## Seleção de estádio

O fluxo de configuração da partida usa `RAM_ISSD_MainMenu_SelectedStadium`
em `$7E:1FA2`. Em `CODE_85A4F8`, a ROM aplica `AND #$0007` e copia o valor
para `$7E:0086`, o seletor consumido pelo carregador de recursos em
`CODE_8B8CDE`. Os oito índices válidos e seus nomes estão definidos no
disassembly: `0 Japan`, `1 USA`, `2 Spain`, `3 Italy`, `4 England`,
`5 Germany`, `6 Brazil`, `7 Nigeria`.

A inicialização USA (`CODE_85A3B1`) define `StadiumIDs_USA` (`1`) como
padrão. Por isso o navegador carrega `layout-1.png` como cenário inicial em
vez de `layout-0.png`. A interface de configuração usa somente esses oito
valores e troca o preview/cenário sem inventar um nono estádio.

O manifesto `dist/data/issd-stadium-layouts.json` fornece ao navegador o
nome, arquivo e recorte de cada preview. `tools/build_issd_stadium_layout_manifest.py`
obtém cada recorte pelo limite RGB não-preto da própria extração, que reproduz
o recorte anterior do layout 0; portanto a troca de cenário não reutiliza
coordenadas de outra imagem.

Em fluxos sem escolha manual, `CODE_85C058` também pode produzir `$0086` por
uma tabela de cenário (`DATA_8BFC28`) ou pela rotina `CODE_858419`. Esses
caminhos ficarão separados da futura escolha manual para preservar o
comportamento de cada modo original.

## Opções de partida

`CODE_85:A456` normaliza as opções escolhidas no menu antes de iniciar a
partida. O manifesto `dist/data/issd-match-settings.json` registra as faixas
confirmadas: cinco níveis, três opções de tempo, regras binárias, três horários
e três climas, oito estádios e três árbitros mais a opção aleatória. Ele é um
contrato de armazenamento da ROM, não uma afirmação de que os respectivos
efeitos já foram reproduzidos no navegador.

A tela atual materializa o contrato de armazenamento dessas opções para a
partida web. Somente a seleção de estádio já altera a apresentação; nível,
tempo, regras, horário, clima e árbitro permanecem dados selecionáveis até que
as rotinas que consomem cada campo sejam validadas na ROM. Assim a interface
não antecipa efeitos de mecânica ainda não comprovados.

`tools/extract_issd_match_setting_transfer.py` agora recupera a transferência
inteira de `CODE_85:A456` a partir do disassembly e grava
`dist/data/issd-match-setting-transfer.json`. O registro inclui as doze
transferências reais do trecho: as dez opções da partida, som e o flag de
locução marcado como não usado. Para cada uma, preserva os endereços WRAM de
menu, destino em jogo e linhas-fonte. Isso separa o fato já provado — por
exemplo, estádio termina em `$7E:0086` — do efeito de jogo que ainda requer
análise de cada consumidor.

O índice complementar `dist/data/issd-match-setting-consumers.json`, gerado
por `tools/extract_issd_match_setting_consumers.py`, encontra 136 acessos
explícitos aos dez registros de partida que mantêm símbolos `InGame`.
Ele identifica rotinas e leitura/escrita, sem nomear o resultado de um ramo:
por exemplo, `CurrentOffSideSetting` é lido em `CODE_80:D5DF`, e
`CurrentYellowCardSetting` em `CODE_80:F076`. Este é o ponto de partida
reproduzível para recuperar cada regra; o índice não transforma esses acessos
em uma implementação web prematura.

## Relógio

O código de interface em `CODE_83:C201` usa BCD e consulta
`DATA_81:AC83`; `CODE_A4:9401` só atualiza o contador quando os flags de pausa
não estão ativos e compara contra `60` frames. A porta de elegibilidade faz OR
de `$11FA/$00C0/$00B8/$00B6/$00BA`: qualquer valor não-zero impede tanto o
incremento do contador de frames quanto o tick BCD. Esses campos são
bloqueadores internos observados, não nomes de pausa, reinício ou fase já
resolvidos. O extrator
`tools/extract_issd_match_clock.py` grava os valores e fontes em
`dist/data/issd-match-clock.json`: além dos offsets de exibição, ele recupera
as duas tabelas de contagem inicial de `CODE_A4:A4926F` (`$81:E893` e
`$81:E89B`). `CODE_83:B02C` zera `$00A8` na inicialização e, portanto, prova
que a primeira partida usa a tabela `$81:E893`. A semântica do contador e o
quarto índice das tabelas continuam pendentes. Por isso o relógio simplificado
do navegador não foi substituído até que a transição de fases e as interrupções
sejam validadas em execução.

`CODE_A4:93CC` também foi recuperada: sob `SED`, reduz `$0001` enquanto o byte
BCD inferior é não-zero e reduz `$0041` quando ele é zero (`0500 → 0459`). O
Canvas usa a tabela inicial da primeira etapa (`$00A8 = 0`) e essa transformação
para apresentar a contagem regressiva das três opções de tempo. Ainda não
implementa os bloqueadores internos nem a transição de intervalo/fim ao chegar
em zero; por isso a apresentação congela em `00:00`, sem inventar uma fase.

O navegador já aplica o trecho de inicialização comprovado: ao começar uma
**nova** partida, zera placares e o progresso exibido do relógio. Isso fica
separado de reinícios dentro da partida, que preservam o tempo. O limite de
duração, intervalos e a transição de fim de período ainda não foram conectados
ao motor web.

## Câmera ampla

O código `issd-native` oferece perfis modernos `TACTICAL (80%)` e
`TACTICAL WIDE (67%)`, com projeções `4/5` e `2/3`. Eles estão registrados em
`dist/data/issd-camera-profiles.json` como extensões opt-in, e não como valores
originais da ROM. A projeção de referência continuará dependente da origem de
câmera capturada em `$7E:13A0/$7E:13B0` e do frame correspondente.
