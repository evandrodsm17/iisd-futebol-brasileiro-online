# Auditoria de cobertura de sprites de ações

Este diagnóstico acrescenta uma camada **somente leitura** sobre o levantamento do ISS Deluxe. Não modifica jogo, renderizador, ROM ou animações existentes.

## Dados confirmados

- `dist/data/issd-action-scripts.json`: tabela estática por rotina e direção; descritores repetidos são preservados na contagem original.
- `docs/issd-focus-*-report.json`: evidência agregada de execução; esses relatórios não permitem dizer qual descritor pertenceu a qual direção.
- `docs/issd-natural-play-asset-map.json`: correspondência de assets gráficos. Os descritores `$ABF6` e `$AC50` da rotina `$82:D100` foram associados a `LowKick`; isso **não** comprova que representem passe ou qual botão os dispara.
- Traços JSONL brutos: necessários para calcular descritores efetivamente observados **por direção**.
- `tools/capture_issd_action_vram.lua`: coleta OAM, VRAM e CGRAM do mesmo frame para composição sem tiles adivinhados.

## Gerar o relatório sem nova captura

Na raiz do repositório, execute:

```powershell
python tools/report_issd_action_sprite_gaps.py --report docs/issd-focus-shot-report.json --report docs/issd-focus-pass-report.json --report docs/issd-focus-big-kick-report.json --asset-map docs/issd-natural-play-asset-map.json --output analysis/issd-action-sprite-gaps.json
```

Os campos direcionais de observação permanecerão `null` porque os relatórios somados não têm esse cruzamento. Isso é intencional.

## Com os JSONL existentes

```powershell
python tools/report_issd_action_sprite_gaps.py --report docs/issd-focus-shot-report.json --report docs/issd-focus-pass-report.json --report docs/issd-focus-big-kick-report.json --trace docs/issd-focus-shot.jsonl --trace docs/issd-focus-pass.jsonl --trace docs/issd-focus-big-kick.jsonl --asset-map docs/issd-natural-play-asset-map.json --output analysis/issd-action-sprite-gaps.json
```

O relatório identifica, por direção, os descritores estáticos, os observados e os ainda não observados. Use `--capture docs/issd-action-vram-trace.jsonl` quando a nova coleta gráfica estiver pronta **e seus arquivos VRAM/CGRAM estiverem presentes**. Os caminhos do JSONL precisam apontar para os dumps correspondentes. A checagem marca apenas presença de dados completos; a comparação visual e byte a byte continua nos validadores já existentes.

## Próxima etapa no BizHawk

1. Abra uma partida e carregue `tools/capture_issd_action_vram.lua` pelo Lua Console.
2. Repita chutes fortes e variantes em direções diferentes. Não substitua uma captura anterior antes de arquivá-la.
3. Use `tools/validate_issd_oam_capture_schema.py` no novo JSONL.
4. Rode esta auditoria com `--capture`; renderize apenas poses com material completo usando `tools/render_issd_action_vram_capture.py`.
5. Para entender o passe, correlacione controles e contexto de posse/bola antes de atribuir o nome humano a qualquer script `LowKick`.

## Testes

```powershell
python -m unittest discover -s tools -p "test_action_sprite_gaps.py" -v
```

Não é gerado PNG nesta etapa: nenhuma pose ou duração é criada sem evidência do runtime.
