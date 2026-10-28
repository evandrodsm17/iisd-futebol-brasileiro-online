#!/usr/bin/env python3
"""Verify that recovered ISSD mechanics keep machine and human documentation."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
DATA = ROOT / "dist" / "data"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def load(name: str) -> dict:
    path = DATA / name
    require(path.is_file(), f"missing data artifact: {path.relative_to(ROOT)}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    require("source" in payload, f"missing source metadata: {path.relative_to(ROOT)}")
    require("limitations" in payload, f"missing limitations: {path.relative_to(ROOT)}")
    return payload


def main() -> None:
    index = DOCS / "issd-reverse-engineering-log.md"
    roadmap = DOCS / "issd-mechanics-roadmap.md"
    mechanics = DOCS / "issd-static-mechanics.md"
    specification = DOCS / "issd-reconstruction-spec.md"
    for path in (index, roadmap, mechanics, specification):
        require(path.is_file(), f"missing human documentation: {path.relative_to(ROOT)}")

    index_text = index.read_text(encoding="utf-8")
    for text in ("Regra de evidência", "Atualização obrigatória", "Ponto de retomada", "Próximo passo ao retomar", "Relógio", "Configuração de partida", "Goleiro"):
        require(text in index_text, f"index lacks required section or system: {text}")
    readme_text = (ROOT / "README.md").read_text(encoding="utf-8")
    require("issd-reverse-engineering-log.md" in readme_text, "README does not link the research index")
    require("issd-reconstruction-spec.md" in readme_text, "README does not link the reconstruction specification")
    specification_text = specification.read_text(encoding="utf-8")
    for text in ("Regra de implementação", "Contrato de estado da partida", "Ordem obrigatória de reconstrução", "Critério de aceite"):
        require(text in specification_text, f"reconstruction specification lacks required section: {text}")

    settings = load("issd-match-settings.json")
    transfer = load("issd-match-setting-transfer.json")
    consumers = load("issd-match-setting-consumers.json")
    clock = load("issd-match-clock.json")
    goalkeeper = load("issd-goalkeeper-context-writes.json")
    goalkeeper_records = load("issd-goalkeeper-catch-records.json")
    trajectory = load("issd-ball-trajectory.json")
    collision = load("issd-collision-machine.json")
    collision_selection = load("issd-collision-target-selection.json")
    actor_fields = load("issd-actor-collision-fields.json")
    foul_gates = load("issd-foul-gates.json")
    phase_gate = load("issd-phase-actor-gate.json")
    active_actor = load("issd-active-actor-selection.json")
    trajectory_activation = load("issd-trajectory-activation.json")
    script_buffer = load("issd-trajectory-script-buffer.json")
    runtime_slots = load("issd-team-runtime-slots.json")
    runtime_record = load("issd-runtime-player-record.json")
    require(len(transfer.get("fields", [])) == 12, "match setting transfer must contain 12 fields")
    require(bool(consumers.get("symbols")), "match setting consumer index is empty")
    require(clock.get("facts", {}).get("counter_frames_per_tick") == 60, "clock tick evidence changed")
    require("game_time" in settings.get("settings", {}), "match setting manifest lacks game_time")
    require(bool(goalkeeper.get("dive_selector", {}).get("writes")), "goalkeeper dive writer index is empty")
    require(goalkeeper.get("catch_dispatch", {}).get("index") == "accumulator A at CODE_83:DD99", "goalkeeper catch dispatch source changed")
    dive_values = {entry["assigned_value"].get("value") for entry in goalkeeper["dive_selector"]["writes"]}
    require(dive_values == {"0000", "0001", "0002"}, "goalkeeper dive selector domain changed")
    require(len(goalkeeper_records.get("records", {})) == 7, "goalkeeper catch records changed")
    require(len(trajectory.get("states", [])) == 6, "ball trajectory state count changed")
    require(trajectory.get("source", {}).get("dispatch_table") == "DATA_83:D9A5", "ball trajectory dispatch source changed")
    require(len(collision.get("states", [])) == 8, "collision machine state count changed")
    require(collision.get("source", {}).get("dispatch_table") == "DATA_83:D77F", "collision machine dispatch source changed")
    require(collision.get("referenced_tables", {}).get("DATA_81B05D") == ["$0000", "$FFF0", "$FFF8", "$0000", "$FFF8", "$FFF0"], "collision offset table changed")
    descriptors = collision.get("bank_88_descriptors", {})
    require(len(descriptors) == 16, "collision descriptor count changed")
    require(descriptors.get("DATA_88EA1E", {}).get("record_count") == 6, "collision descriptor structure changed")
    require(collision_selection.get("selection", {}).get("scan_count") == 11, "collision target scan count changed")
    require(actor_fields.get("fields", {}).get("0030", {}).get("initialization") == "0910", "actor collision field initialization changed")
    require(len(foul_gates.get("foul_setting_gates", [])) == 3, "foul gate count changed")
    require(foul_gates.get("common_exit", {}).get("entry") == "CODE_80:F125", "foul common exit changed")
    require(phase_gate.get("entries", {}).get("special_index") == 3, "phase actor gate special index changed")
    require(active_actor.get("source", {}).get("global_pointer") == "WRAM 7E:11E8", "active actor pointer source changed")
    require(trajectory_activation.get("source", {}).get("activation") == "CODE_86:9E48", "trajectory activation source changed")
    require(trajectory_activation.get("script_transfer", {}).get("entry") == "CODE_86:AADB", "trajectory script transfer changed")
    require(script_buffer.get("buffer", {}).get("length_bytes") == 20, "trajectory script buffer size changed")
    require("7E:3F90" in script_buffer.get("buffer", {}).get("population", ""), "trajectory script buffer provenance changed")
    require(runtime_slots.get("runtime_arrays", {}).get("population_entries_per_team") == 11, "team runtime slot population changed")
    require(runtime_slots.get("active_player_mask", {}).get("control_bit") == "20", "team runtime activity-mask bit changed")
    require(runtime_slots.get("trajectory_selection_compare", {}).get("entry") == "CODE_83:C71D", "team runtime trajectory comparison source changed")
    require(runtime_slots.get("trajectory_selection_compare", {}).get("selection_pair", {}).get("failure") == "FFFF", "team runtime selector-pair sentinel changed")
    require("40 bytes" in runtime_slots.get("snapshot_lifecycle", {}).get("copy", ""), "team runtime snapshot copy size changed")
    require(runtime_slots.get("selector_consumers", {}).get("high_byte", {}).get("entry") == "CODE_83:C870", "team runtime high-byte consumer changed")
    require(runtime_record.get("record", {}).get("size_bytes") == 10, "runtime player record size changed")
    require(len(runtime_record.get("observed_reads", [])) == 7, "runtime player record read coverage changed")
    print("ISSD documentation audit: OK")


if __name__ == "__main__":
    main()
