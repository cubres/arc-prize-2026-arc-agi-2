"""Original source-only native integration; root owns every remote action.

Use only the current run's owned inference directory, never downloaded
pickles. Preserve the exact strong-reference pair before adding any object
candidate. Official export is deliberately absent: pair qualification comes
first. This file was not part of the already completed CPU screen.
"""
import hashlib
import json
import os
import time
from pathlib import Path

import numpy as np

PINNED = {"baseline37.py":"52141a1eb17b5d33b2c528f8571b16eef9f4e784f7a8873d3f62f59f31d1c2cf",
          "object_selector.py":"9926c66261bd1b97a206ae5808f6208e717fe7544b0cc57c75589d0d39f0d391"}


def fill_query_pairs(task, ranked_pairs, seconds=0.4):
    import object_selector
    from baseline37 import grid
    if len(ranked_pairs)!=len(task["test"]):
        raise ValueError("complete native query inventory required")
    canonical=[]
    for pair in ranked_pairs:
        if len(pair)>2:
            raise ValueError("only native top-two prefix permitted")
        canonical.append([grid(a).tolist() for a in pair])
    extra=object_selector.solve(task,seconds=seconds,candidate_cap=32)
    merged=[]
    additions=0
    for index,pair in enumerate(canonical):
        result=list(pair)
        # Retain both original slots exactly, including a duplicated pair.
        # Only actual ranking cardinality determines whether a slot exists.
        for candidate in extra["candidates"]:
            value=candidate["grids"][index]
            if len(result)<2 and value not in result:
                result.append(value)
                additions+=1
        assert result[:len(pair)]==pair
        merged.append(result)
    return merged,{"object":extra,"new_guesses":additions,"all_native_slots_preserved":True}


def run(namespace):
    """A prospective full-query paired diagnostic after exact control sealing."""
    from arc_loader import ArcDataset
    from arc_decoder import ArcDecoder, score_kgmon
    from strongref_extension import write_seal
    here=Path(__file__).resolve().parent
    for name,expected in PINNED.items():
        if hashlib.sha256((here/name).read_bytes()).hexdigest()!=expected:
            raise RuntimeError("screened object source drift: "+name)
    import object_selector
    import baseline37
    if Path(object_selector.__file__).resolve()!=here/"object_selector.py" or Path(baseline37.__file__).resolve()!=here/"baseline37.py":
        raise RuntimeError("actually loaded object/helper path drift")
    if os.environ.get("ARC_STRONGREF_DEEP")!="0":
        raise RuntimeError("isolate object factor: stronger main control only, deep disabled")
    if namespace["STRONGREF_RECEIPT"]["status"]!="CONTROL_NO_EXTRA_PASS":
        raise RuntimeError("unqualified strong-reference control")
    v12=namespace["v12"]
    rerun=namespace["V12_RERUN"]
    work=namespace["V12_WORKDIR"]
    challenge_path=Path(os.environ["V12_DATA_ROOT"])/v12.challenges_name(rerun)
    challenges=json.loads(challenge_path.read_bytes())
    data=ArcDataset.from_file(str(challenge_path))
    decoder=ArcDecoder(data,n_guesses=2)
    # Same current-run owned pool source already used by the qualified control.
    decoder.load_decoded_results("/kaggle/inference_outputs")
    main=decoder.run_selection_algo(score_kgmon)
    control=data.get_submission(main)
    control_raw=(Path(work)/"PRIVATE_strongref_main_predictions.json").read_bytes()
    prior=json.loads(control_raw)
    if control!=prior:
        raise RuntimeError("native selector repeat does not match the sealed control")
    plan_raw=(Path(work)/"PRIVATE_strongref_query_plan.json").read_bytes()
    if hashlib.sha256(plan_raw).hexdigest()!=namespace["STRONGREF_RECEIPT"]["query_plan_sha256"]:
        raise RuntimeError("registered control query inventory hash drift")
    inventory=json.loads(plan_raw)["inventory"]
    if not inventory or any(task not in challenges or count!=len(challenges[task]["test"])
                            for task,count in inventory.items()):
        raise RuntimeError("registered control task/query inventory drift")
    if rerun and set(inventory)!=set(challenges):
        raise RuntimeError("official-rerun control inventory is incomplete")
    inventory_pin=write_seal(Path(work)/"PRIVATE_object_query_inventory.json",{
        "challenges_sha256":hashlib.sha256(challenge_path.read_bytes()).hexdigest(),
        "inventory":inventory,"source_pins":PINNED,"candidate_seconds":0.4,
        "full_native_top_two_preserved":True,"test_truth_used":False})
    started=time.monotonic()
    build_end=namespace["V12_START_MONO"]+namespace["V12_DEADLINES"]["submission_build_end"]
    stop_at=min(started+120,build_end-20)
    merged=dict(main)
    records=[]
    # A non-rerun main processes only its registered smoke inventory; never
    # supplement constructor placeholders for tasks the control did not run.
    for task_id in inventory:
        spec=challenges[task_id]
        if time.monotonic()>=stop_at:
            records.append({"task_id":task_id,"status":"SKIPPED_NATIVE_BUDGET","new_guesses":0})
            continue
        task={"train":spec["train"],"test":[{"input":p["input"]} for p in spec["test"]]}
        # Task IDs are indexing metadata only and never supplied to solve().
        pairs=[]
        for index in range(len(task["test"])):
            pair=main.get(task_id+"_"+str(index),[])[:2]
            pairs.append([np.asarray(a).tolist() for a in pair])
        filled,receipt=fill_query_pairs(task,pairs,seconds=0.4)
        for index,pair in enumerate(filled):
            merged[task_id+"_"+str(index)]=[np.asarray(a,dtype=np.uint8) for a in pair]
        records.append({"task_id":task_id,"status":"SCREENED","new_guesses":receipt["new_guesses"],
                        "object_cpu_seconds":receipt["object"]["seconds_cpu"],
                        "object_stop":receipt["object"]["stop_reason"],
                        "all_native_slots_preserved":True})
    treatment=data.get_submission(merged)
    if v12.validate(treatment,challenges):
        raise RuntimeError("complete paired candidate schema failed")
    for task_id,queries in inventory.items():
        for index in range(queries):
            pair=main.get(task_id+"_"+str(index),[])[:2]
            for offset in range(len(pair)):
                slot="attempt_"+str(offset+1)
                if treatment[task_id][index][slot]!=control[task_id][index][slot]:
                    raise RuntimeError("an existing native first/second attempt changed")
    treatment_pin=write_seal(Path(work)/"PRIVATE_object_treatment_predictions.json",treatment)
    receipt={"schema":"arc2-native-object-paired-diagnostic/1","query_inventory":inventory_pin,
        "control_sha256":hashlib.sha256(control_raw).hexdigest(),"treatment":treatment_pin,
        "tasks":len(inventory),"queries":sum(inventory.values()),"records":records,
        "matched_scope_is_complete_rerun_inventory":rerun,
        "outside_registered_inventory_unchanged":True,
        "new_guesses":sum(r["new_guesses"] for r in records),
        "native_budget_skips":sum(r["status"]!="SCREENED" for r in records),
        "all_native_first_two_slots_preserved":True,"solutions_opened":False,
        "elapsed_wall_seconds":time.monotonic()-started,"official_export_enabled":False,
        "qualification":"PRIVATE_FULL_PAIR_REQUIRES_ROOT_REVIEW_AND_EXACT_TRUTH_EVALUATION"}
    write_seal(Path(work)/"PRIVATE_object_native_receipt.json",receipt)
    if time.monotonic()>=build_end:
        raise RuntimeError("paired native diagnostic exceeded whole build deadline")
    print("OBJECT_PAIRED_PRIVATE_DIAGNOSTIC_SEALED",json.dumps({k:receipt[k] for k in ["tasks","queries","new_guesses","native_budget_skips","elapsed_wall_seconds"]}),flush=True)
    return receipt
