# Cadência da simulação web

`dist/simulation-clock.mjs` atualiza a simulação em passos fixos de 1/60 s;
o desenho permanece na cadência do navegador. Isso elimina a variação da
aceleração provisória causada por dt diferente entre monitores. Não constitui
uma reprodução completa do escalonamento de atores da ROM.

A política web limita recuperação de atrasos a seis passos por desenho e
descarta o excesso acima de 100 ms. Ocultar a página reinicia o acumulador e
limpa teclas; o tempo oculto não avança a partida. Essa política é de interface,
não uma regra extraída da ROM. Timers ainda baseados em performance.now têm
comportamento de tempo real e precisam ser migrados separadamente.

`node tools/test_simulation_clock.mjs` compara dez segundos de movimento
em 30/60/120/144 Hz e exige igualdade de posição, velocidade e 600 passos.
Também verifica atraso longo, reset e entradas inválidas. A movimentação
fracionária inteira nativa e seus coeficientes ainda aguardam integração;
os valores de velocidade atuais continuam provisórios.
