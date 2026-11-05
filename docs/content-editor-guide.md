# Editor de conteúdo v1

Abra `dist/editor/index.html` pelo mesmo servidor HTTP da aplicação ou siga o link da tela inicial. Cadastre clubes, edite uniformes e jogadores, associe escudos PNG e estádios personalizados. Os dados ficam no IndexedDB deste navegador.

## Importação e exportação

O botão **Exportar pacote ZIP** cria `content-package.json` e todos os PNGs em `assets/`. Para restaurar, selecione o arquivo ZIP em **Importar pacote ZIP**. Nenhum dado é enviado ao servidor. Use seus próprios arquivos ou materiais com direitos de distribuição.

## Integração no jogo

No editor do catálogo original (`dist/editor/rom-catalog.html`), cada jogador
também pode ter código de cabelo 0–13 e variante de pele normal/alternativa
salvos no navegador. Esses valores são dados de catálogo: **a representação
visual em partida ainda não os aplica**. A seleção e edição de cores de
paleta também não estão implementadas nesse editor; na ROM, algumas cores são
compartilhadas pela equipe. Restaurar o jogador remove seus overrides.

### Prévia do jogador

Para ativar a prévia no editor de catálogo, gere os dados localmente a partir
da sua ROM USA e abra o editor pelo servidor HTTP do projeto:

```powershell
python tools/export_issd_editor_preview.py `
  "International Superstar Soccer Deluxe/International Superstar Soccer Deluxe (USA).sfc" `
  --output dist/assets/issd/editor-preview-local.json
```

O arquivo gerado é ignorado pelo Git e não contém a ROM integral. Na ficha do
jogador, use as setas para girar a pose e **Escolher cabelo** para ver as 14
opções; mudanças de cabelo, variante de pele e posição atualizam a prévia
imediatamente. Clique em **Salvar jogador** para persistir a escolha. Essas
poses são as do editor original, distintas das animações de gameplay.

### Laboratório de construção do jogador

No editor principal, abra **Ver a construção do jogador** para comparar as
camadas de corpo e cabelo com o resultado composto. Nesta máquina, os dados
locais já foram gerados a partir das capturas de pesquisa. Para regenerá-los
quando as capturas locais estiverem disponíveis:

```powershell
python tools/export_issd_hair_lab.py `
  --style1 analysis/bsnes-hair-oam-clear `
  --style2 analysis/bsnes-hair-style2 `
  --style13 analysis/bsnes-hair-style13 `
  --output dist/assets/issd/hair-lab-local
```

As imagens derivadas permanecem locais e não são enviadas ao Git. A prévia
usa apenas quadros que coincidiram com o emulador, em uma direção e paleta;
o posicionamento e dois estilos foram ajustados em RAM para a captura. Ela
não altera a partida e não representa ainda todas as animações ou equipes.

A seção **Montagem calculada ao vivo** usa folha de corpo, âncoras, detalhe
de uniforme e atlas de cabelo separadamente em treze amostras validadas. Para servir o projeto no
Windows com o tipo correto de módulos JavaScript, execute
`python tools/serve_local.py` e abra `http://127.0.0.1:4173/editor/locomotion-lab.html`.
O detalhe local é recriado com `tools/audit_issd_dynamic_hair.py` usando a
captura `analysis/bsnes-hair-anchor-draw` e o argumento `--detail-output
dist/assets/issd/hair-lab-local/dynamic-detail-local.json`.

Clubes personalizados aparecem no seletor de equipes com prefixo *[PERSONALIZADO]*. Seus elencos, nomes, cores e escudos são carregados. Até haver sprites HD próprios por equipe, a representação dos jogadores usa um fallback visual de referência e não altera física.

Estádios personalizados têm nome e referência a um dos oito layouts-base já suportados, opcionalmente com PNG autoral. O layout lógico segue o escolhido; a criação de dimensões próprias e arquivos de câmera é etapa futura.

## Limitações

A primeira versão trabalha com um pacote local ativo por navegador, não sincroniza pela nuvem e não inclui edição de competições ou formação tática. O pacote admite elencos inferiores a 11 atletas; vagas de uma partida são preenchidas com jogadores temporários. A exclusão de clubes desvincula jogadores e a exclusão de estádios desvincula clubes. Ao abrir a partida, recarregue a página para aplicar as alterações feitas no editor.

## Testes

```bash
node tools/test_content_editor.mjs
node --check dist/editor/editor.js
node --check dist/game.js
python tools/validate_content_package.py dist/data/content-package.example.json --print-hash
```

### Prévia de ações no laboratório

Abra `http://127.0.0.1:4173/editor/locomotion-lab.html#action-lab` e escolha
**Passe** ou **Chute**. É possível selecionar equipe, uniforme, direção, pele,
cabelo e número; pausar e inspecionar os quadros pelo controle deslizante. A
prévia de passe usa o mesmo compositor e as mesmas limitações da partida. A
chute usa composição de uniforme experimental nas direções cima, direita,
baixo e diagonal baixo-direita quando os
dados locais validados estão disponíveis; outras direções usam a folha de
aparência fixa e podem conter aproximações. O painel informa isso. O carrinho continua acessível
logo abaixo, em `#slide-lab`, com sua cobertura limitada.

O laboratório usa recursos extraídos localmente da ROM: se algum não existir,
o painel informa a indisponibilidade. Ele não modifica o estado da partida.
Para regenerar o passe completo, siga `tools/export_issd_pass_orientations.py`
com as capturas pareadas descritas em `issd-mechanics-roadmap.md`; os arquivos
derivados permanecem ignorados pelo Git.

Para atualizar um recurso de passe já existente com as paletas iniciais das
equipes, execute na raiz do projeto:

```powershell
python tools/update_issd_pass_team_palettes.py --asset dist/assets/issd/native-pass-body-local.json --rom "International Superstar Soccer Deluxe/International Superstar Soccer Deluxe (USA).sfc"
```

O comando confere a identidade da ROM e do recurso antes de alterá-lo. As
paletas e os gráficos continuam locais; a ROM não é incluída na distribuição.
