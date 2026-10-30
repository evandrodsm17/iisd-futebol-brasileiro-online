#!/usr/bin/env python3
"""Audit existing native ball-to-carrier geometry without reinterpreting ROM states.

Stream the 78 MB trace instead of loading it all into memory. WRAM units stay
native, separate from Canvas. A carrier address match is NOT proof of possession.
"""
import argparse
import json
import math
from collections import Counter
from pathlib import Path


def stats(values):
    ordered=sorted(values)
    if not ordered:
        return {"count":0,"median":None,"p10":None,"p90":None,"max":None}
    return {
        "count":len(ordered),
        "median":round(ordered[(len(ordered)-1)//2],3),
        "p10":round(ordered[round((len(ordered)-1)*0.10)],3),
        "p90":round(ordered[round((len(ordered)-1)*0.90)],3),
        "max":round(ordered[-1],3)
    }


def analyze(lines):
    records=0
    matched=[]
    ground=[]
    nearest=[]
    carrier_speed=[]
    ball_speed=[]
    carriers=Counter()
    missing=0
    previous=None
    last_frame=None
    for line in lines:
        if not line.strip():
            continue
        sample=json.loads(line)
        frame=sample.get("frame")
        if not isinstance(frame,int) or (last_frame is not None and frame<=last_frame):
            raise ValueError("Frames missing or non-monotonic")
        last_frame=frame
        records+=1
        ball=sample.get("ball") or {}
        actors=sample.get("actors") or []
        if not isinstance(actors,list) or not all(isinstance(ball.get(k),(int,float)) for k in ("x","y","z")):
            raise ValueError("Trace row lacks ball/actor data")
        carrier=sample.get("carrier")
        carriers[str(carrier)]+=1
        active=[a for a in actors if isinstance(a.get("address"),int) and isinstance(a.get("x"),(int,float)) and isinstance(a.get("y"),(int,float))]
        if active:
            nearest.append(min(math.hypot(a["x"]-ball["x"],a["y"]-ball["y"]) for a in active))
        actor=next((a for a in active if a["address"]==carrier),None)
        if actor is None:
            missing+=1
            previous=None
            continue
        distance=math.hypot(ball["x"]-actor["x"],ball["y"]-actor["y"])
        matched.append(distance)
        if ball["z"]==0:ground.append(distance)
        if previous is not None and previous["carrier"]==carrier and 1<=frame-previous["frame"]<=2:
            dt=frame-previous["frame"]
            ps=math.hypot(actor["x"]-previous["actor"]["x"],actor["y"]-previous["actor"]["y"])/dt
            bs=math.hypot(ball["x"]-previous["ball"]["x"],ball["y"]-previous["ball"]["y"])/dt
            if ps<12 and bs<25:
                carrier_speed.append(ps)
                ball_speed.append(bs)
        previous={"frame":frame,"carrier":carrier,"actor":actor,"ball":ball}
    return {
        "schema":"issd-native-dribble-reference/v1",
        "source":"docs/issd-natural-play-trace.jsonl (BizHawk passive WRAM)",
        "frames_read":records,
        "last_frame":last_frame,
        "carrier_values_top":carriers.most_common(10),
        "samples_with_carrier_actor_match":len(matched),
        "samples_without_carrier_actor_match":missing,
        "distance_ball_to_carrier_candidate_native_units":stats(matched),
        "ground_ball_to_carrier_candidate_native_units":stats(ground),
        "nearest_actor_distance_native_units_not_possession":stats(nearest),
        "carrier_candidate_speed_per_emulated_frame":stats(carrier_speed),
        "ball_speed_per_emulated_frame_when_carrier_matches":stats(ball_speed),
        "status":"native_candidate_distance_observed" if matched else "no_valid_carrier_matches",
        "cautions":[
            "The WRAM $1B90 carrier field is a candidate pointer, not fully verified ownership.",
            "Proximity to an actor is not proof of a controlled dribble.",
            "Native WRAM values and browser Canvas world units are not directly comparable.",
            "Do not apply any automatic calibration without verifying coordinate units and possession semantics."
        ]
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("trace",type=Path)
    p.add_argument("--output",type=Path)
    args=p.parse_args()
    with args.trace.open(encoding="utf-8") as file:
        result=analyze(file)
    summary=json.dumps(result,ensure_ascii=False,indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(summary+"\n",encoding="utf-8")
    print(summary)


if __name__=="__main__":
    main()
