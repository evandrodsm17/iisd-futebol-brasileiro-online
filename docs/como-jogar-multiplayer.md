# Como jogar o teste multiplayer online

O Nostalgia Soccer HD possui um **teste experimental para duas pessoas**. Cada participante controla um atleta por vez. O servidor coordena a sala e os comandos; ainda não é uma partida completa nem um servidor pronto para acesso público.

## 1. Iniciar o servidor no computador anfitrião

Instale o Node.js 20 ou superior. No PowerShell, entre na pasta do projeto e execute:

```powershell
cd "$env:USERPROFILE\Documents\REA-FUTEBOL"
npm install
npm start
```

Mantenha o terminal aberto durante o teste. No mesmo computador, abra [http://127.0.0.1:4173/](http://127.0.0.1:4173/) em duas janelas ou perfis de navegador. Se o projeto estiver em outra pasta, substitua o caminho do `cd`.

Se a porta 4173 já estiver ocupada, pare o servidor com `Ctrl+C` e inicie-o em outra porta:

```powershell
$env:PORT = '4175'
npm start
```

Nesse exemplo, use `http://127.0.0.1:4175/`. Para voltar à porta padrão em outro teste, execute `Remove-Item Env:PORT -ErrorAction SilentlyContinue` antes de iniciar. É necessário reiniciar o servidor depois de atualizar os arquivos do jogo.

### Dois computadores na mesma rede local

No computador anfitrião, inicie o servidor para aceitar conexões da rede:

```powershell
cd "$env:USERPROFILE\Documents\REA-FUTEBOL"
$env:HOST = '0.0.0.0'
npm start
```

Execute `ipconfig` em outro terminal e procure o **Endereço IPv4** da conexão Wi-Fi ou Ethernet ativa. Os dois participantes devem acessar `http://IP-DO-ANFITRIAO:4173/`, trocando o IP pelo endereço encontrado, por exemplo `http://192.168.1.10:4173/`. Se a porta tiver sido alterada, use a mesma porta na URL. `127.0.0.1` sempre aponta para o próprio computador e não conecta o segundo dispositivo ao anfitrião. O firewall do anfitrião pode precisar permitir a conexão na rede privada.

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
| X | Com posse, passe; sem posse, tentativa de pressão/desarme |
| Q | Trocar para um atleta elegível próximo da bola |
| Direção + X ou direção + A | Ao cobrar lateral, direcionar e arremessar; A seleciona a cobrança mais forte |

Para lateral, mantenha a direção desejada e pressione **X** ou **A**. O chute com A durante a jogada normal ainda está desativado no online. W para passe enfiado e D para cruzamento estão reservados, mas essas ações ainda não foram implementadas. O F funciona como desarme no modo local, porém não é enviado no teste online atual: use X sem posse.

No teste online atual, apenas um atleta por equipe participa da disputa. Assim,
o passe segue a direção escolhida e não é direcionado automaticamente aos
demais atletas parados. Na partida local, a assistência pode escolher um
companheiro elegível próximo da direção indicada.

O menu **CONFIGURAR CONTROLES DO TECLADO** permite alterar e restaurar os atalhos; as escolhas são guardadas no navegador. Se as teclas tiverem sido personalizadas, os atalhos exibidos no painel prevalecem sobre a tabela acima.

## O que está disponível e o que falta

O teste sincroniza os dois atletas controlados, condução e passe, tentativa de desarme, contato entre eles, troca de atleta e classificação provisória de saídas, gols e reinícios. O lateral possui preparação e arremesso controláveis; o placar pode ser atualizado em um gol reconhecido. Essas regras e sua física ainda precisam de validação contra a ROM.

Os demais atletas ficam parados e não disputam a bola. Ainda faltam chute em jogo aberto, ação completa dos goleiros, IA, contato com os demais atletas, faltas, relógio avançando, fim de partida e demais regras. Clubes e alterações locais do editor não estão disponíveis na sala; o teste usa o catálogo-base. O relógio selecionado é um valor inicial de configuração, não um cronômetro funcional nessa sessão.

## Se algo não funcionar

- **A página não abre:** confirme que `npm start` continua em execução e confira a porta. Em outra máquina, use o IPv4 do anfitrião e verifique rede e firewall.
- **Criar/entrar ou iniciar está desabilitado:** aguarde a conexão; confira as escolhas dos dois participantes, a confirmação de ambos e a mensagem de verificação. Caso uma escolha mude, confirme novamente.
- **Versões incompatíveis ou dados indisponíveis:** ambos devem abrir o mesmo servidor atualizado. Reinicie-o após atualizar o projeto e recarregue as páginas; se o código do jogo foi alterado, veja a seção de identidade em [Servidor e multiplayer experimental](server-foundation.md#identidade-e-preparação).
- **O jogo parou ou atrasou:** confirme que os dois navegadores e a conexão permanecem ativos. Não há reconexão ou recuperação automática da sessão.

Detalhes técnicos e testes automatizados: [Servidor e multiplayer experimental](server-foundation.md).
