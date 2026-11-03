# ISSD — poses nativas de referência

34 poses com geometria dinâmica plausível extraídas de capturas reais do BizHawk (24 sem bola, 10 com bola). As imagens PNG são RGBA transparentes na resolução nativa. As folhas PREVIA são apenas visualizações 3× e não uma sequência temporal.

**Importante:** sete registros de chute/levantar foram excluídos da exportação pois seu campo `pose` usa geometria estática/compactada. O coletor antigo leu OAM dinâmica incorretamente, então essas capturas não são quadros válidos. Os dumps VRAM/CGRAM existem no arquivo de origem fornecido. Consulte auditoria.json.

**Observação:** A precisão geométrica foi avaliada por consistência de coordenadas e visualização dos sprites, ainda sem comparação pixel a pixel com um vídeo de referência. Não afirmar que são sprites HD, tampouco um ciclo fechado.
