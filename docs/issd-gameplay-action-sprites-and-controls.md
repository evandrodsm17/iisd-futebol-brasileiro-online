# Partida: sprites de chute/passe e teclado configurável (experimental)

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
