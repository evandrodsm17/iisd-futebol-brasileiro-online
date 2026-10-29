# Cadência da simulação web

Os comandos discretos de teclado agora entram em `simulation-input.mjs` e
são consumidos, em ordem, no começo do próximo tick ativo. Movimento contínuo
continua lendo teclas mantidas. Eventos de repetição automática do teclado
não geram novos chutes/passes/pressões; soltar e apertar novamente gera outro
comando. A fila é limpa no início de partida, retorno ao menu, perda de foco
e mudança de visibilidade. O limite defensivo é de 32 comandos pendentes.
Essa é uma política de entrada web, não a reconstrução completa dos gates
de input da ROM. `node tools/test_simulation_input.mjs` verifica ordem,
consumo único, repetição e descarte de comandos após limpeza.

`dist/simulation-clock.mjs` atualiza a simulação em passos fixos de 1/60 s;
o desenho permanece na cadência do navegador. Isso elimina a variação da
aceleração provisória causada por dt diferente entre monitores. Não constitui
uma reprodução completa do escalonamento de atores da ROM.

A política web limita recuperação de atrasos a seis passos por desenho e
descarta o excesso acima de 100 ms. Ocultar a página reinicia o acumulador e
limpa teclas; o tempo oculto não avança a partida. Essa política é de interface,
não uma regra extraída da ROM. Os intervalos de chute/passe, pressão e
retomada de posse agora usam um contador inteiro de ticks ativos convertido
em milissegundos. Iniciar uma partida zera esse contador e o tempo de
animação, limpa os cooldowns anteriores e instala novamente a espera inicial.
As durações provisórias de 1000/420/260 ms foram mantidas. Mensagens visuais
continuam usando setTimeout e não controlam a física.

`node tools/test_simulation_clock.mjs` compara dez segundos de movimento
em 30/60/120/144 Hz e exige igualdade de posição, velocidade e 600 passos.
Também verifica atraso longo, reset e entradas inválidas. A movimentação
fracionária inteira nativa e seus coeficientes ainda aguardam integração;
os valores de velocidade atuais continuam provisórios.
