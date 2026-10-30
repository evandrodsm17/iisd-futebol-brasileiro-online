#!/usr/bin/env python3
"""Report candidate CPU attacking action transitions, without labeling pass/cross/shot."""
from __future__ import annotations
import argparse, json, math
from collections import Counter, defaultdict
from pathlib import Path

WATCH={0xD007:"D007",0xD100:"D100",0xD0BE:"D0BE",0xD290:"D290"}
def analyze(records):
    scripts=Counter(); events=[]; prev_actor={}; prev_ball=None
    frames=0; levels=Counter(); sides=Counter(); team_settings=Counter()
    for row in records:
        frames+=1; levels[row.get("game_level")]+=1
        side_flags=row.get("side_flags_a4"); local_levels=row.get("team_CC")
        if isinstance(side_flags,list) and isinstance(local_levels,list) and len(side_flags)==len(local_levels)==2:
            team_settings[(tuple(side_flags),tuple(local_levels),row.get("game_level"))]+=1
        actors={a["address"]:a for a in row.get("actors",[]) if isinstance(a.get("address"),int)}
        ball=row.get("ball",{})
        for address,actor in actors.items():
            script=actor.get("script")
            scripts[str(script)]+=1
            old=prev_actor.get(address)
            if script in WATCH and (old is None or old.get("script")!=script):
                sides[actor.get("side")]+=1
                event={"frame":row["frame"],"script":WATCH[script],
                       "actor":address,"side":actor.get("side"),
                       "state":actor.get("state"),"direction":actor.get("direction"),
                       "ball":{k:ball.get(k) for k in ("x","y","z","vx","vy","vz")},
                       "actor_xy":[actor.get("x"),actor.get("y")],
                       "carrier_candidate":row.get("carrier_candidate"),
                       "team_CC":row.get("team_CC"),"side_flags_a4":row.get("side_flags_a4"),
                       "prng_words":row.get("prng_words"),
                       "carrier_matches_actor":row.get("carrier_candidate")==address,
                       "proximity":round(math.hypot(ball["x"]-actor["x"],ball["y"]-actor["y"]),3)
                       if all(isinstance(v,(int,float)) for v in
                       (ball.get("x"),ball.get("y"),actor.get("x"),actor.get("y"))) else None}
                events.append(event)
        prev_actor=actors
        prev_ball=ball
    return {"schema":"issd-cpu-offense-observations/v1",
            "frames":frames,"difficulty_samples":dict(levels),
            "team_settings_samples":[{"side_flags_a4":list(flags),"team_CC":list(cc),
              "selected_game_level":level,"frames":count}
              for (flags,cc,level),count in team_settings.most_common()],
            "candidate_script_transitions":len(events),
            "by_script":dict(Counter(e["script"] for e in events)),
            "by_side":dict(sides),"events":events,
            "limitations":[
                "Transitions to a kick-associated animation are not proof of a pass, cross or shot.",
                "CPU-controlled side requires confirmation of CPUvsCPU gameplay mode.",
                "The candidate carrier pointer is not certified possession.",
                "No thresholds for shooting/crossing are inferred from these traces.",
                "PRNG values observed during events do not establish which branch consumed them.",
                "Compare multiple controlled scenarios and observed ball trajectories before naming behaviors."]}
def main():
    p=argparse.ArgumentParser();p.add_argument("trace",type=Path);p.add_argument("output",type=Path)
    args=p.parse_args()
    def rows():
        with args.trace.open(encoding="utf-8") as stream:
            for l in stream:
                if l.strip():yield json.loads(l)
    result=analyze(rows())
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(f"Read {result['frames']} frames; {result['candidate_script_transitions']} candidate transitions.")
if __name__=="__main__":main()
