# Resolução gráfica e jogadores em telas 4K

Os jogadores são compostos a partir de gráficos de baixa resolução, poses,
paletas e dados de aparência identificados na ROM. A composição dinâmica
permite combinar partes e cores sem manter uma imagem diferente para cada
jogador, mas não cria automaticamente detalhes que não existem nos tiles.
Locomoção e pose parada têm cobertura melhor que as demais ações; a
investigação de animações continua no
[checklist de física e animações](issd-checklist-fisica-animacoes.md).

## Renderização atual

O campo usa coordenadas lógicas de 1280×720 independentemente do tamanho da
tela. O canvas é dimensionado pela largura exibida e pela densidade de pixels
do dispositivo, de no mínimo 1280×720 até no máximo 3840×2160. Câmera,
simulação e dimensões lógicas não mudam quando a resolução da tela muda.
O navegador continua desenhando as imagens dos jogadores sem interpolação
suave, preservando os pixels originais. O canvas maior evita ampliar um único
quadro final de 720p na TV e melhora a precisão de posicionamento e desenho
dos elementos, mas **não acrescenta detalhes à arte original**.

O limite 4K evita alocações ainda maiores em telas de alta densidade; o buffer
RGBA 3840×2160 pode ocupar aproximadamente 32 MiB, além dos demais recursos
gráficos. Desempenho depende do navegador e da GPU. Mudanças de tamanho ou de
densidade de tela atualizam o buffer, sem afetar o estado da partida.

## Caminhos possíveis para uma versão visualmente HD

1. **Pixel art original:** ampliar os pixels com vizinho mais próximo. Mantém
   a referência visual e a composição dinâmica, mas os pixels permanecem
   aparentes. É a opção atualmente usada.
2. **Filtro opcional de ampliação:** experimentar algoritmos que tentam
   suavizar contornos entre pixels. Isso pode modificar linhas finas, números,
   cabelo ou cores; requer comparação em movimento e deve ser opcional, sem
   trocar as fontes nem interferir na simulação.
3. **Arte HD redesenhada:** criar versões em maior resolução para cada parte,
   pose, direção e ação validada, respeitando ancoragem, sobreposição,
   temporização, uniformes, cores de pele e cabelo. É o caminho para adicionar
   detalhes reais, mas exige um fluxo de produção e validação de muitos quadros;
   a composição de tiles da ROM não garante que um único redesenho baste.

Antes de escolher um filtro ou redesenhar o elenco inteiro, produzir uma
amostra comparável de um jogador com poses de parado, caminhada e corrida,
duas direções e dois uniformes. Avaliar consistência em movimento e em 4K;
depois ampliar a cobertura para as demais ações comprovadas.
