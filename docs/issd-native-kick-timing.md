# Registro temporal das ações de chute — 30/10/2026

As 135 capturas OAM nativas de `docs2.zip` foram organizadas em 20 sequências, 11 pares script/direção e 66 descritores únicos. Os valores medidos são os **intervalos entre dois descritores distintos capturados**, e não o tempo de animação inteiro.

- `$D007`: intervalos predominantemente `2,1,1,1,1` frames do emulador.
- `$D100`: `1,1,1,1,1` frames.
- A direção 7 de `$D007` também mostrou um intervalo inicial de 5 frames em uma das execuções. O relatório preserva essa discrepância.
- O último descritor das sequências completas aparece novamente 3 frames depois, confirmando **pelo menos 4 frames de exposição amostrada**, não o término da pose.
- O cursor nativo nas sequências completas percorre `2,4,6,8,10,12`.

`tools/report_issd_native_action_timing.py` audita novas capturas sem inventar temporização, retornando agrupamentos por ação/direção e limites da evidência. Teste com `python -m unittest discover -s tools -p 'test_native_action_timing.py' -v`.

O testador portátil em HTML e os 66 PNGs foram fornecidos como anexo do ChatGPT separado do repositório. Nenhum PNG foi incorporado ao build principal e nenhuma animação foi ativada no motor da partida. Os sprites ainda são recortes OAM heurísticos. Para uso final, falta validar visualmente cada peça, confirmar o término da última pose e o comando que ativa `$D100`.
