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


def load_document_data(name: str) -> dict:
    path = DOCS / name
    require(path.is_file(), f"missing documented data artifact: {path.relative_to(ROOT)}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    require("source" in payload, f"missing source metadata: {path.relative_to(ROOT)}")
    require("limitations" in payload, f"missing limitations: {path.relative_to(ROOT)}")
    return payload


def main() -> None:
    index = DOCS / "issd-reverse-engineering-log.md"
    roadmap = DOCS / "issd-mechanics-roadmap.md"
    mechanics = DOCS / "issd-static-mechanics.md"
    specification = DOCS / "issd-reconstruction-spec.md"
    product_vision = DOCS / "product-vision.md"
    editor_contract = DOCS / "content-editor-contract.md"
    for path in (index, roadmap, mechanics, specification, product_vision, editor_contract):
        require(path.is_file(), f"missing human documentation: {path.relative_to(ROOT)}")

    index_text = index.read_text(encoding="utf-8")
    for text in ("Regra de evidência", "Atualização obrigatória", "Ponto de retomada", "Próximo passo ao retomar", "Relógio", "Configuração de partida", "Goleiro"):
        require(text in index_text, f"index lacks required section or system: {text}")
    readme_text = (ROOT / "README.md").read_text(encoding="utf-8")
    require("issd-reverse-engineering-log.md" in readme_text, "README does not link the research index")
    require("issd-reconstruction-spec.md" in readme_text, "README does not link the reconstruction specification")
    require("product-vision.md" in readme_text, "README does not link the product vision")
    specification_text = specification.read_text(encoding="utf-8")
    for text in ("Regra de implementação", "Contrato de estado da partida", "Ordem obrigatória de reconstrução", "Critério de aceite"):
        require(text in specification_text, f"reconstruction specification lacks required section: {text}")
    vision_text = product_vision.read_text(encoding="utf-8")
    for text in ("Modo local", "Multiplayer online", "Competições e temporadas", "Regras reais", "Editor de conteúdo", "pacote validado"):
        require(text in vision_text, f"product vision lacks required section: {text}")
    editor_text = editor_contract.read_text(encoding="utf-8")
    for text in ("Envelope do pacote", "Regras de validação inicial", "schema_version", "package_id"):
        require(text in editor_text, f"content editor contract lacks required section: {text}")

    settings = load("issd-match-settings.json")
    transfer = load("issd-match-setting-transfer.json")
    consumers = load("issd-match-setting-consumers.json")
    clock = load("issd-match-clock.json")
    goalkeeper = load("issd-goalkeeper-context-writes.json")
    goalkeeper_records = load("issd-goalkeeper-catch-records.json")
    goalkeeper_machine = load("issd-goalkeeper-handler-machine.json")
    goalkeeper_schedulers = load("issd-goalkeeper-mode-schedulers.json")
    offside_predicate = load("issd-offside-boundary-predicate.json")
    event_bits = load("issd-match-event-bits.json")
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
    default_locomotion = load("issd-default-locomotion-pipeline.json")
    input_motion = load("issd-input-motion-analysis.json")
    animation_survey = load("issd-animation-survey.json")
    dynamic_vram_upload = load("issd-dynamic-vram-upload.json")
    oam_composition = load("issd-oam-composition-contract.json")
    kinematics = load_document_data("issd-motion-kinematics.json")
    selected_kinematics = load_document_data("issd-motion-kinematics-selected-p1.json")
    require(len(transfer.get("fields", [])) == 12, "match setting transfer must contain 12 fields")
    require(bool(consumers.get("symbols")), "match setting consumer index is empty")
    require(clock.get("facts", {}).get("counter_frames_per_tick") == 60, "clock tick evidence changed")
    require(clock.get("facts", {}).get("frame_eligibility", {}).get("blockers_orred") == ["$11FA", "$00C0", "$00B8", "$00B6", "$00BA"], "clock eligibility gate changed")
    require(clock.get("facts", {}).get("tick_transform", {}).get("example") == "$0500 becomes $0459", "clock BCD decrement changed")
    require(clock.get("facts", {}).get("zero_display_path", {}).get("phase_write") == "no direct write to $00A8 occurs in CODE_A4:92CF", "clock zero path changed")
    require("game_time" in settings.get("settings", {}), "match setting manifest lacks game_time")
    require(bool(goalkeeper.get("dive_selector", {}).get("writes")), "goalkeeper dive writer index is empty")
    require(goalkeeper.get("catch_dispatch", {}).get("index") == "accumulator A at CODE_83:DD99", "goalkeeper catch dispatch source changed")
    dive_values = {entry["assigned_value"].get("value") for entry in goalkeeper["dive_selector"]["writes"]}
    require(dive_values == {"0000", "0001", "0002"}, "goalkeeper dive selector domain changed")
    require(len(goalkeeper_records.get("records", {})) == 7, "goalkeeper catch records changed")
    require(goalkeeper_machine.get("source", {}).get("mode_dispatch") == "DATA_83:DCAA", "goalkeeper mode dispatch source changed")
    require(len(goalkeeper_machine.get("mode_machine", {}).get("entries", [])) == 3, "goalkeeper mode dispatch count changed")
    require(goalkeeper_machine.get("source", {}).get("catch_dispatch") == "DATA_83:DDA1", "goalkeeper catch dispatch table changed")
    require(len(goalkeeper_machine.get("catch_machine", {}).get("entries", [])) == 9, "goalkeeper catch dispatch count changed")
    require(len(goalkeeper_schedulers.get("schedulers", [])) == 2, "goalkeeper scheduler count changed")
    require(all(len(scheduler.get("entries", [])) == 13 for scheduler in goalkeeper_schedulers.get("schedulers", [])), "goalkeeper scheduler entry count changed")
    require(offside_predicate.get("source", {}).get("entry") == "CODE_80:D627", "offside boundary predicate source changed")
    require(len(offside_predicate.get("branches", [])) == 2, "offside boundary branch count changed")
    require(offside_predicate.get("branches", [])[0].get("margin", {}).get("normal") == "$000C", "offside normal margin changed")
    require(offside_predicate.get("branches", [])[1].get("margin", {}).get("after $042A replacement") == "$0018", "offside boundary margin changed")
    require(event_bits.get("source", {}).get("word") == "$7E:19D2", "match event word changed")
    require(len(event_bits.get("writers", [])) == 8, "match event writer index changed")
    require(event_bits.get("writers", [])[0].get("mask") == "$0400", "offside event bit writer changed")
    require(len(trajectory.get("states", [])) == 6, "ball trajectory state count changed")
    require(trajectory.get("source", {}).get("dispatch_table") == "DATA_83:D9A5", "ball trajectory dispatch source changed")
    require(trajectory.get("source", {}).get("initializer", {}).get("entry") == "CODE_83:D92D", "ball trajectory initializer source changed")
    require("stadium ids 5 and 7" in trajectory.get("source", {}).get("initializer", {}).get("local_offsets", ""), "ball trajectory stadium offset rule changed")
    require(len(collision.get("states", [])) == 8, "collision machine state count changed")
    require(collision.get("source", {}).get("dispatch_table") == "DATA_83:D77F", "collision machine dispatch source changed")
    require(collision.get("runtime_driver", {}).get("entry") == "CODE_84:A69A", "collision runtime driver changed")
    require(len(collision.get("observed_transitions", [])) == 6, "collision transition count changed")
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
    require(default_locomotion.get("default_running", {}).get("script_table") == "DATA_82:CF9F", "default locomotion script changed")
    require(default_locomotion.get("default_running", {}).get("frame_ticks") == [4, 3, 3, 3, 4, 3, 3, 3], "default locomotion timing changed")
    require(input_motion.get("source", {}).get("kind") == "passive_runtime_capture", "input/motion source changed")
    require(input_motion.get("sample_count") == 3600, "input/motion sample count changed")
    expected_directions = {"256": 0, "512": 4, "1024": 2, "2048": 6, "1280": 1, "1536": 3, "2304": 7, "2560": 5}
    observed_directions = input_motion.get("observed_direction_masks", {})
    for mask, direction in expected_directions.items():
        candidate = observed_directions.get(mask, {})
        require(candidate.get("direction") == direction, f"input/motion direction candidate changed: {mask}")
        require(candidate.get("direction_ratio", 0) >= 0.7, f"input/motion direction evidence too weak: {mask}")
    require(input_motion.get("observed_motion_modifier", {}).get("held", {}).get("scripts", {}).get("53151") == 1633, "input/motion running modifier correlation changed")
    require(animation_survey.get("source", {}).get("kind") == "passive_runtime_animation_survey", "animation survey source changed")
    require(animation_survey.get("sample_count") == 468, "animation survey sample count changed")
    surveyed_scripts = {entry.get("script"): entry for entry in animation_survey.get("observed_scripts", [])}
    for script in ("$82:D320", "$82:D6DB"):
        entry = surveyed_scripts.get(script, {})
        require(len(entry.get("directions", {})) == 8, f"animation survey lacks eight idle directions: {script}")
        require(len(entry.get("descriptors", [])) == 15, f"animation survey idle descriptor coverage changed: {script}")
    require(dynamic_vram_upload.get("upload", {}).get("destination_vram_word") == "$6000 + ((graphics_source_low_word & $01FF) << 4)", "dynamic VRAM upload address changed")
    require(oam_composition.get("source", {}).get("entry") == "CODE_80:95E0", "OAM composition entry changed")
    require(oam_composition.get("draw_list", {}).get("base") == "$7E:1D40", "OAM draw-list base changed")
    require(oam_composition.get("object_transform", {}).get("tile_base") == "object+$02 is added to each geometry tile before hardware OAM write", "OAM tile-base rule changed")
    require(oam_composition.get("dynamic_geometry", {}).get("tile_normalization") == "geometry_tile is pre-base; tile is the final OAM byte after object+$02", "OAM tile normalization changed")
    require(kinematics.get("actor_scope") == "all_capturable_actors", "all-actor motion kinematics scope changed")
    require(selected_kinematics.get("actor_scope") == "selected_p1", "selected-player motion kinematics scope changed")
    for payload in (kinematics, selected_kinematics):
        for family in ("walking", "running"):
            require(len(payload.get("families", {}).get(family, {})) == 8, f"motion kinematics lacks eight {family} directions")
    print("ISSD documentation audit: OK")


if __name__ == "__main__":
    main()
