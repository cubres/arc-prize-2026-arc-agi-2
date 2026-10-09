"""Original local CPU runner; no solution/reference inputs. MIT."""
import argparse,hashlib,importlib.util,json,time
from pathlib import Path
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("local_rules",HERE/"local_rules.py")
solver=importlib.util.module_from_spec(spec);spec.loader.exec_module(solver)


def main():
    p=argparse.ArgumentParser();p.add_argument("--challenges",type=Path,required=True);p.add_argument("--output",type=Path,required=True)
    a=p.parse_args();raw=a.challenges.read_bytes();tasks=json.loads(raw)
    source_pins={name:hashlib.sha256((HERE/name).read_bytes()).hexdigest() for name in ("PROTOCOL.json","local_rules.py","run_predictions.py")}
    with (HERE/"PRE_PREDICTION_SOURCE_SEAL.json").open("x") as f:json.dump({"source_pins":source_pins,"discovery_only":True,"solutions_opened_by_runner":False},f,indent=2)
    start=time.monotonic();out={}
    for task_id,t in sorted(tasks.items()):
        if time.monotonic()-start>90:raise RuntimeError("Whole experiment cap exceeded")
        clean={"train":t["train"],"test":[{"input":pair["input"]} for pair in t["test"]]}
        out[task_id]=solver.solve_task(clean)
    result={"schema":"original-arc2-cellular-discovery-predictions-v1","discovery_only":True,"solutions_opened_by_runner":False,
            "source_pins":source_pins,"challenge_sha256":hashlib.sha256(raw).hexdigest(),"seconds":time.monotonic()-start,"tasks":out}
    data=(json.dumps(result,indent=2,sort_keys=True)+"\n").encode()
    with a.output.open("xb") as f:f.write(data)
    with a.output.with_suffix(".seal.json").open("x") as f:json.dump({"sha256":hashlib.sha256(data).hexdigest(),"bytes":len(data),"source_pins":source_pins},f,indent=2)
    print(json.dumps({"tasks":len(out),"seconds":result["seconds"],"with_fit":sum(bool(x['fits']) for x in out.values()),"prediction_sha256":hashlib.sha256(data).hexdigest()},indent=2))


if __name__=="__main__":main()
