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
