# Validação das capturas de ação — 30/10/2026

O arquivo fornecido `docs.rar` continha 41 snapshots pareados (VRAM 64 KiB, CGRAM 512 bytes e metadados de ator). A inspeção revelou **34 poses de parado** com geometria dinâmica coerente: 24 sob `$D320` e 10 sob `$D6DB`. O restante (3 `$D100`, 2 `$D007`, 2 `$DB5B`) foi capturado com ponteiros `pose >= $8000`, formato de geometria estática/compactada.

O capturador vigente lê incorretamente essa segunda categoria via planos dinâmicos WRAM `$2000/$4000/$6000`. Nas sete ações, o tile de geometria foi sempre `$55` e os offsets chegaram a milhares de pixels. Portanto **não são quadros de animação utilizáveis** apesar de existir VRAM/CGRAM completa.

Correções propostas: decodificar endereços VRAM de 2048 tiles 4bpp (não apenas 512), rejeitar composições de ações com geometria compactada mal interpretada e sinalizar cobertura de captura como inválida no auditor. Não reconstruir artificialmente as pernas/braços ou animações de chute. O próximo capturador precisará salvar OAM final já produzido pelo SNES, ou decodificar corretamente a representação estática no banco da ROM. A temporização das ações continua pendente.

As prévias de poses paradas foram exportadas localmente separadas das sete amostras inválidas. Este PR não modifica a partida.
