# Como jogar o teste multiplayer online

O Nostalgia Soccer HD possui um **teste experimental para duas pessoas**. Cada participante controla um atleta por vez. O servidor coordena a sala e os comandos; ainda não é uma partida completa nem um servidor pronto para acesso público.

## 1. Iniciar o servidor no computador anfitrião

Instale o Node.js 20 ou superior. No PowerShell, dentro da pasta do projeto, execute este único comando:

```powershell
npm run jogar:rede
```

O comando instala as dependências se necessário, atualiza a identidade da versão e inicia o servidor. Ele mostra o endereço deste computador e os endereços IPv4 encontrados nas redes conectadas. Mantenha o terminal aberto; pressione **Ctrl+C** para encerrar. Para testar no mesmo computador, abra [http://127.0.0.1:4173/](http://127.0.0.1:4173/) em duas janelas ou perfis de navegador.

No computador deste projeto, também é possível executar o comando abaixo de qualquer pasta do PowerShell:

```powershell
npm --prefix "$env:USERPROFILE\Documents\REA-FUTEBOL" run jogar:rede
```

Se a porta 4173 já estiver ocupada, pare o servidor com `Ctrl+C` e inicie-o em outra porta:

```powershell
$env:PORT = '4175'
npm run jogar:rede
```

Nesse exemplo, use `http://127.0.0.1:4175/`. Para voltar à porta padrão em outro teste, execute `Remove-Item Env:PORT -ErrorAction SilentlyContinue` antes de iniciar. É necessário reiniciar o servidor depois de atualizar os arquivos do jogo.

### Dois computadores na mesma rede local

Os dois participantes devem acessar o mesmo endereço **Na rede** exibido pelo comando no computador anfitrião, escolhendo a conexão Wi-Fi ou Ethernet usada pelos dois. Se houver várias redes ou adaptadores virtuais, podem aparecer vários endereços. Por exemplo, `http://192.168.1.10:4173/`. `127.0.0.1` sempre aponta para o próprio computador e não conecta o segundo dispositivo ao anfitrião. O firewall do anfitrião pode precisar permitir a conexão na rede privada.

Este procedimento é para teste em rede confiável. Jogar pela internet exige disponibilizar um servidor acessível aos dois participantes, com HTTPS/WSS e infraestrutura adequada; isso ainda não está configurado. Não é necessário iniciar o Docker ou o PostgreSQL para este teste.

## 2. Criar e entrar na sala

1. Nos dois navegadores, abra o mesmo endereço do servidor e escolha **MULTIPLAYER ONLINE** (ou **SALA ONLINE · EXPERIMENTAL**, em versões anteriores) no menu. Confirme a opção.
2. Aguarde a conexão. O primeiro participante seleciona **CRIAR SALA** e compartilha o código exibido.
3. O segundo digita o código em **CÓDIGO DA SALA** e seleciona **ENTRAR NA SALA**.
4. Cada participante seleciona **ESCOLHER EQUIPE E UNIFORME**. Navegue pelos grupos e bandeiras e escolha sua equipe. O avanço aos uniformes aguarda os dois escolherem.
5. Na tela de uniformes, cada participante escolhe o próprio uniforme 1 ou 2 e pode conferir a prévia visual. Avance e confirme a seleção para retornar à sala.
6. Na sala, o anfitrião escolhe estádio e relógio inicial. Cada participante seleciona **ESTOU PRONTO**. Mudanças na configuração podem exigir nova confirmação.
7. Aguarde os dois navegadores validarem os dados e concluírem a verificação da troca de comandos. O anfitrião seleciona **INICIAR TESTE ONLINE** quando o botão ficar disponível.

Mantenha as duas janelas visíveis quando estiver testando no mesmo computador: o navegador pode reduzir ou suspender o processamento de abas em segundo plano. Se alguém sair ou perder a conexão, o teste é interrompido e será necessário preparar outra sessão.

## 3. Controles padrão

| Tecla | Ação no teste online |
| --- | --- |
| Setas | Mover o jogador controlado |
| E | Correr enquanto mantém a direção pressionada |
| A | Chutar com a bola; mantenha E pressionado para um chute mais alto |
| X | Com posse, passe; sem posse, tentativa de pressão/desarme |
| Q | Trocar para um atleta elegível próximo da bola |
| Direção + X ou direção + A | Ao cobrar lateral, direcionar e arremessar; A seleciona a cobrança mais forte |

Para lateral, mantenha a direção desejada e pressione **X** ou **A**. Durante a jogada, o chute usa a direção pressionada ou a direção para a qual o jogador está olhando. W para passe enfiado e D para cruzamento estão reservados, mas essas ações ainda não foram implementadas. O F funciona como desarme no modo local, porém não é enviado no teste online atual: use X sem posse.

No teste online atual, cada pessoa controla um atleta. Os demais jogadores de
linha se movimentam automaticamente, procuram manter a formação e disputam a
bola; goleiros não controlados se posicionam e tentam defender chutes. A assistência
de passe pode escolher um companheiro elegível próximo da direção indicada.

Enquanto sua equipe estiver com a bola, **Q** mantém o controle no portador.
Com a bola livre ou com o adversário, **Q** pode selecionar outro atleta da
sua equipe próximo da bola. Quando um companheiro recupera a bola ou o goleiro
segura um chute, o controle passa para ele; use **X** para passar ou **A** para
chutar a bola de volta ao jogo.

O menu **CONFIGURAR CONTROLES DO TECLADO** permite alterar e restaurar os atalhos; as escolhas são guardadas no navegador. Se as teclas tiverem sido personalizadas, os atalhos exibidos no painel prevalecem sobre a tabela acima.

No começo da partida e após um gol, a bola permanece no centro durante cerca de um segundo antes da saída. Após o gol, a equipe que o sofreu recebe a posse para reiniciar a partida.

## O que está disponível e o que falta

O teste sincroniza os dois atletas controlados, condução, passe e chute, tentativa de desarme, contato entre eles, troca de atleta e classificação provisória de saídas, gols e reinícios. O lateral possui preparação e arremesso controláveis; o placar e a saída após o gol são sincronizados. O voo e o quique do chute usam a aproximação atual do jogo local; essas regras e sua física ainda precisam de validação contra a ROM.

Os goleiros usam posicionamento, defesa, rebote e reposição aérea provisórios compartilhados com o modo local; a animação específica e a mecânica completa ainda precisam ser validadas. A movimentação automática, os contatos e a assistência de passe são aproximações que ainda precisam ser comparadas com o jogo original. O relógio regressivo avança com os quadros de simulação confirmados e pausa durante a preparação do lateral; ao chegar a zero, ainda não encerra a partida nem muda de tempo. Ainda faltam faltas, fim de partida e outras regras. Clubes e alterações locais do editor não estão disponíveis na sala; o teste usa o catálogo-base.

## Se algo não funcionar

- **A página não abre:** confirme que `npm run jogar:rede` continua em execução e confira a porta. Em outra máquina, use o IPv4 de rede exibido pelo anfitrião e verifique rede e firewall.
- **Criar/entrar ou iniciar está desabilitado:** aguarde a conexão; confira as escolhas dos dois participantes, a confirmação de ambos e a mensagem de verificação. Caso uma escolha mude, confirme novamente.
- **Versões incompatíveis ou dados indisponíveis:** ambos devem abrir o mesmo servidor atualizado. Reinicie-o após atualizar o projeto e recarregue as páginas; se o código do jogo foi alterado, veja a seção de identidade em [Servidor e multiplayer experimental](server-foundation.md#identidade-e-preparação).
- **O jogo parou ou atrasou:** confirme que os dois navegadores e a conexão permanecem ativos. Não há reconexão ou recuperação automática da sessão.

Detalhes técnicos e testes automatizados: [Servidor e multiplayer experimental](server-foundation.md).
