# Partida: sprites de chute/passe e teclado configurável (experimental)

## Estado atual do chute e evidência local

O chute da partida usa composição dinâmica experimental nos oito setores de
tela para jogadores de linha, equipes e uniformes com paletas locais
disponíveis. Goleiros não usam essa composição. Cabelo personalizado,
temporização e validação visual individual das variações continuam pendentes.

Um replay isolado registrou os seis descritores `$A617`, `$A620`, `$A629`,
`$A632`, `$A63B`, `$A644` do ator `$1900`. A ferramenta
`tools/export_issd_shot_body.py` verifica a geometria da ROM, atribuição de
slots OAM, OAM exibida, tiles da VRAM e pixels da screenshot antes de gerar
`dist/assets/issd/native-shot-body-local.json` (ignorado pelo Git). As seis
composições somam 2.005 pixels candidatos, todos coincidentes nesta captura;
os resultados estão em `docs/issd-shot-body-evidence.json`. Isso valida a
aparência capturada, não cada combinação de paleta, cabelo ou contexto de
partida. A duração visual ainda usa a temporização provisória anterior.

Mais três replays com direção escolhida antes do comando produziram seis
quadros cada para as direções nativas 6, 1 e 2. O exportador também confere
tiles de detalhes e guarda suas variantes de número geradas da ROM. Foram
comparados 1.914, 2.064 e 2.086 pixels candidatos, respectivamente; em duas
direções 6 e 45 pixels são encobertos por outras peças da OAM e a composição
integral explica as diferenças. O relatório está em
`docs/issd-shot-directions-evidence.json`. A paleta e o detalhe numérico de
outras equipes são extrapolados do mecanismo utilizado no passe e ainda não
foram validados visualmente para todas as combinações. Na direção esquerda,
um dos quadros coincidiu com a OAM da PPU dois quadros após a preparação,
enquanto os demais coincidiram após um. A exportação agora aceita esse atraso
somente quando todas as peças, tiles e pixels passam nas verificações; a
sequência esquerda foi incluída. Pressionar
direção junto ao comando produziu outro script em algumas tentativas; isso não
prova por si só o significado desse comando.

Um replay adicional ajustou a direção antes do comando e registrou os seis
descritores da direção nativa 7, correspondentes à diagonal superior direita.
Os 1.871 pixels candidatos coincidiram com a captura, além das verificações de
geometria, OAM e VRAM. Alterando o instante da orientação antes do chute, dois
replays adicionais registraram as direções nativas 5 e 3, correspondentes às
diagonais superior e inferior esquerdas. Foram comparados, respectivamente,
1.871 e 2.064 pixels candidatos; as diferenças de 86 e 50 pixels são explicadas
por sobreposição de outras peças na composição integral da OAM. A evidência
continua restrita ao ator, uniforme e contexto das capturas.

Para gerar a versão com as oito direções validadas a partir dos replays locais:

```powershell
python tools/export_issd_shot_directions.py --root analysis --rom 'International Superstar Soccer Deluxe/International Superstar Soccer Deluxe (USA).sfc' --output dist/assets/issd/native-shot-body-local.json --report docs/issd-shot-directions-evidence.json
```

Sem o arquivo local gerado, a partida e o laboratório mantêm o recurso visual
anterior. O laboratório em `#action-lab` sinaliza o setor composto e os limites.

`python tools/audit_issd_shot_capture_coverage.py analysis --output
docs/issd-shot-capture-inventory.json` inventaria as capturas gráficas locais
do script `D007`. Nesta cópia, há seis descritores observados para cada uma
das direções nativas 0, 1, 2, 4 e 6 com arquivos de VRAM, OAM da PPU, CGRAM
e screenshot presentes. A presença dos arquivos **não** confirma a atribuição
dos slots OAM ao jogador, sincronização, correspondência de tiles nem a
composição final; a direção nativa 4 compartilha descritores com a direção 0,
o que por si só não demonstra o espelhamento correto. A análise precisa
correlacionar os slots e a geometria com a ROM e as imagens antes de produzir
um compositor dinâmico ou acrescentar direções. O inventário contém apenas
contagens e identificadores, não os gráficos nem a ROM.

Esta atualização conecta ações de gameplay existentes a animações visuais de um único jogador e acrescenta configuração de atalhos pelo menu de partida. Não modifica a física da bola nem a locomoção existente.

## Após fazer merge

O pacote de **11 spritesheets PNG** é fornecido separadamente no ZIP `ISSD-integracao-partida-v1.zip`, entregue no ChatGPT. **A PR contém somente código, não os 11 PNGs**: extraia o ZIP na raiz do repositório para instalar os assets em `dist/assets/issd/actions/D007` e `D100`. Em seguida atualize o site seguindo o processo normal de deploy. Caso os PNGs faltem, a partida continua mostrando a animação de caminhada/corrida.

- Chute (padrão Espaço) mostra `D007`, chute forte.
- Passe (padrão X) mostra `D100`, *LowKick* como **aproximação visual provisória** (não há prova de equivalência ao botão de passe do SNES).
- A direção é mapeada para a direcional observada mais próxima; direções ausentes não recebem novos sprites inventados.
- A ação visual é disparada apenas quando a ação real é aceita, retorna à locomoção após o último quadro e é cancelada no reinício.
- A velocidade visual foi multiplicada por 3 para legibilidade no jogo (não é timing fiel do SNES). O último frame da captura permanece sem duração final comprovada.
- O uniforme do jogador no movimento de chute vem da captura original; ainda não recolore as 36 equipes nem seus kits. Esse é o próximo refinamento visual.

## Editor de atalhos

Na página principal do jogo, abra **CONFIGURAR CONTROLES DO TECLADO**. Clique na tecla de uma ação, pressione outra e veja a atualização imediata. Escape cancela a edição; teclas já em uso não são aceitas; Restaurar Padrões desfaz alterações. O mapeamento fica em `localStorage` do navegador. Teclado físico por `KeyboardEvent.code`.

As teclas de movimento também são configuráveis (WASD, correr, chute, passe, pressão, trocar jogador e reiniciar).

## Testes

```bash
node dist/test-gameplay-actions.mjs
```

Teste manual: entre em Open Game, faça passe e chute com posse de bola, troque os atalhos durante a navegação e verifique a volta para caminhada/corrida. Este PR não inclui verificação de navegador em produção; revise o comportamento visual antes de liberar a funcionalidade.

## Limites conhecidos

As folhas experimentais possuem resíduos OAM, e não são ainda assets finais. A equipe deve validar a correspondência de direções e paletas. A interação do comando e o efeito físico no jogo permanecem os já existentes; esta PR não afirma reconstruir a lógica original do SNES.
