# Checklist de física, eventos e animações — ISS Deluxe

Este é o plano de trabalho para tornar a partida web jogável seguindo a ROM
USA. Cada item desmarcado representa trabalho ainda necessário; um módulo
provisório no navegador não significa que o comportamento original foi
reproduzido. As descobertas detalhadas e suas fontes ficam em
[mecânicas](issd-mechanics-roadmap.md),
[especificação de reconstrução](issd-reconstruction-spec.md) e
[inventário de animações](issd-animation-inventory.md).

## Situação de partida

- [x] Locomoção em oito direções e animações de andar, correr e parado já
  disponíveis no navegador. A aparência foi considerada boa na avaliação do
  usuário; isso não encerra a calibração física nem valida todos os estados.
- [x] Seleção de equipes, uniformes e preparação da partida no fluxo web.
- [x] Há implementações provisórias de contato entre jogadores, roubo de bola
  e classificação de gol, lateral, escanteio e tiro de meta. Elas permitem
  testar a partida, mas suas distâncias, respostas e reposições não estão
  comprovadas como iguais às da ROM.
- [x] Foram identificadas rotas parciais de ação defensiva e uma verificação
  compartilhada de contato com a bola. Ainda não foi demonstrada a sequência
  completa de carrinho, contato e resultado em situação natural.
- [ ] Reproduzir os eventos abaixo de ponta a ponta e substituir as
  aproximações por comportamento validado.

## Prioridade 1 — Fundamentos da simulação

- [ ] Relacionar coordenadas nativas, frações, alturas e velocidades da ROM
  às unidades do campo web, sem misturá-las à projeção da câmera.
- [ ] Identificar ordem de atualização por quadro: entrada, atores, bola,
  detecção de contato, resultado, fases e animação.
- [ ] Mapear aceleração, velocidade, desaceleração, atrito e mudança de
  direção de caminhada e corrida, inclusive com bola e sob ação defensiva;
  verificar diferenças ligadas aos atributos dos jogadores.
- [ ] Mapear bola livre e em posse: posição junto ao pé, aquisição e perda de
  controle, velocidade, altura, gravidade, quique, rolagem e desaceleração.
- [ ] Validar fronteiras do campo, raio/altura efetivos da bola, cruzamento de
  linhas, postes, travessão e rede, incluindo trajetórias de alta velocidade.
- [ ] Confirmar duração de quadros, arredondamentos e aritmética usados na
  simulação e manter a execução independente da taxa de renderização.

## Prioridade 2 — Disputa, carrinho e queda

- [ ] Mapear condições de entrada e saída da pressão, disputa em pé e roubo:
  comando, distância, direção, posse, velocidade e estados incompatíveis.
- [ ] Identificar volumes de contato jogador–jogador e jogador–bola, sua
  posição por estado e a ordem de resolução em contatos simultâneos.
- [ ] Investigar respostas a contato corporal: bloqueio, deslocamento,
  desaceleração, perda de bola e recuperação do controle, com e sem bola.
- [x] Observar uma entrada natural de carrinho `$82:DB25` e um contato entre
  jogadores em replay pareado: [evidência](issd-slide-player-contact.json).
- [ ] Generalizar as condições de entrada com `$68`, `$6E`, `84:9FED`,
  `84:A124`, `84:A056` e `84:A08D`; `$DF7F` isolado não comprova carrinho.
- [ ] Registrar quadro a quadro a janela efetiva de contato do carrinho e seus
  resultados: erra, toca na bola, atinge jogador, recupera posse e comete falta.
- [ ] Identificar animações e temporização de entrada, deslize, recuperação e
  retomada do controle em cada direção aplicável, incluindo espelhamento.
- [ ] Identificar animações e física de desequilíbrio, queda e levantamento
  para o jogador atingido e, quando ocorrer, para quem realizou o carrinho. A
  queda da vítima em um contato e cinco quadros iniciais de recuperação
  estão no laboratório com uniformes derivados da ROM; ainda faltam outras
  direções, recuperação em outros contextos e física.
- [ ] Mapear a reação de salto que evita o carrinho e mantém o vínculo da bola:
  condições, controle/IA, física e composição visual. Um caso pareado foi
  observado; veja [a evidência](issd-slide-jump-reaction.json). A composição
  de 23 quadros nas oito direções está no laboratório, com variantes de
  equipe derivadas da ROM. Só uma direção foi observada contra o estado de
  carrinho; faltam cabelo e as condições completas de escolha da reação.
- [ ] Integrar física, posse e animação a uma mesma máquina de estados; testar
  contatos frontais, laterais, por trás e múltiplos, sem presumir seus efeitos.

## Prioridade 3 — Faltas e reinícios

### Falta, cartão e cobrança

- [ ] Mapear critérios da ROM para marcar ou não uma falta, posição do evento,
  equipe beneficiada e influência das opções de regras.
- [ ] Identificar interrupção, sinalização, cartões, vantagem e pênalti quando
  existirem no jogo, incluindo as condições e transições correspondentes.
- [ ] Mapear escolha do cobrador, posição da bola, barreira e posicionamento
  dos demais jogadores; identificar quando o relógio e os controles param.
- [ ] Reconstruir animações de jogador caído, árbitro e cobrança de falta ou
  pênalti, com suas janelas de entrada e retomada da bola em jogo.

### Lateral

- [ ] Mapear cruzamento da linha lateral, último toque e equipe que cobra,
  inclusive quando a bola sai pelo ar ou próxima a uma quina.
- [ ] Identificar local da cobrança, escolha e deslocamento do cobrador,
  posicionamento dos demais atletas e condições para reiniciar a partida.
- [ ] Reconstruir a animação de segurar e lançar a bola, sua direção, duração,
  momento de soltura, trajetória e possibilidade de receber/interceptar.

### Linha de fundo, tiro de meta e escanteio

- [ ] Diferenciar gol, saída pela linha de fundo, tiro de meta e escanteio
  pelos testes geométricos e pelo último toque usados na ROM.
- [ ] Mapear escolha do lado de cobrança, posicionamento da bola, goleiro,
  cobrador e demais atletas para tiro de meta e para escanteio.
- [ ] Reconstruir preparação, animação de cobrança, lançamento, condições de
  retomada e controle da bola para os dois tipos de reinício.
- [ ] Testar os dois lados do campo, ambas as equipes, cruzamentos próximos
  às traves e as combinações de último toque relevantes.

## Prioridade 4 — Jogadas e fases restantes

- [ ] Mapear passe, chute, finalização, cruzamento e cabeceio: comandos,
  elegibilidade, direção, força, trajetória e contato com a bola.
- [ ] Construir e validar as animações correspondentes, incluindo o quadro em
  que a bola é atingida e o retorno do atleta ao estado controlável.
- [ ] Investigar dribles especiais, pedalada, bicicleta e demais movimentos
  presentes na ROM; registrar pré-condições e sequências antes de implementá-los.
- [ ] Mapear goleiro: deslocamento, posicionamento, defesa, mergulho, captura,
  soltura e reposição, com suas animações e interações com bola e jogadores.
- [ ] Mapear impedimento, início/reinício após gol, intervalo, fim de partida,
  cronômetro, pausas e demais fases que afetem o controle da simulação.
- [ ] Correlacionar decisões da CPU e troca de jogador com os mesmos estados e
  regras físicas, distinguindo lógica original de comportamento provisório.

## Método para cada animação e evento

- [ ] Identificar a rotina, condições, estado anterior e posterior, flags e
  dados da ROM; registrar o endereço e a fonte exata.
- [ ] Capturar uma sequência natural com entradas, atores, bola, fases e tempo
  por quadro; incluir um controle sem a ação e casos positivos e negativos.
- [ ] Identificar descritores de pose, tiles, OAM/VRAM, paletas, deslocamentos,
  ordem, prioridade, espelhamento e duração. Cobrir direções que existirem na
  ROM, sem inventar poses ou sequências ausentes.
- [ ] Verificar composição dinâmica de uniforme, pele e cabelo para os
  jogadores aplicáveis; não presumir que todas as ações usem os mesmos dados.
- [ ] Comparar imagem e tempo com referência da ROM e conferir pontos de apoio,
  sombras e ligação ao evento físico; registrar qualquer lacuna de captura.
- [ ] Implementar no navegador com teste de transições, geometria e resultado;
  comparar os registros web e ROM em cenários equivalentes.
- [ ] Atualizar a documentação com evidência, limitações, comportamento web,
  testes e próximo passo. Preservar a ROM e manter capturas sensíveis locais.

## Critério para marcar uma etapa como concluída

Uma etapa só é concluída quando condições de entrada, sequência de estados,
física, animação e saída relevante estiverem ligadas por evidência da ROM e
testadas na web. Caso só parte esteja comprovada, marcar apenas os itens
correspondentes e manter o restante explicitamente pendente. Câmera ampla,
clubes e modos online/offline são extensões e não devem mudar a referência
da simulação original sem adaptação documentada.

## Próxima frente ao retomar

Prosseguir pela prioridade 2: a rota `$DB25` já foi alcançada naturalmente e
o contato aceito no script `$DF7F` foi observado em um replay pareado e as
instruções que limpam e escrevem `$00A6` nesse caso foram identificadas. Uma
reação do adversário foi rastreada até os estados `$0328/$0330/$0360/$0350`,
e em um replay estendido passou por recuperação até uma pose parada. A
generalização da saída e suas animações ainda precisam de validação. Falta
produzir contato aceito em `$DB25` e acompanhar as consequências até
recuperação, queda ou falta. Há um primeiro traço
quadro a quadro de `$DB25 → $DB5B` com OAM/VRAM/CGRAM locais; falta associar
completamente as peças ao ator e validar a composição e as demais direções.
As seis poses agora têm 35 peças de corpo comparadas à geometria da ROM e à
OAM da PPU, após correção de defasagem de um quadro no replay. As 36
divergências restantes coincidem com pixels do controle na área do minimapa;
a camada responsável e partes auxiliares ainda precisam ser verificadas. Os
tiles usados pelo corpo coincidem com a ROM nas seis poses; cabelo e variações
de uniforme e pele ainda não foram validados. Usar esses dados
para decidir a primeira substituição segura da física provisória no navegador.

Em testes pareados com parâmetros sintéticos no replay, um índice de árbitro
levou a `80:F125`, mudança de fase e mensagem visual `FOUL`; outros índices
não produziram essa mudança na mesma janela. Ainda faltam confirmar as regras
gerais e capturar a cobrança e o reinício completos.
