"""Public discovery evaluation after source/prediction sealing. MIT."""
import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
DATA=ROOT/'research/claude_takeover_20261008/arc2/v12_work/competition_files_20261008T104737Z'
REFERENCE=ROOT/'research/claude_takeover_20261008/arc2/frontier_rokaiya_v2_output/submission.json'


def main():
    raw=(HERE/'public_predictions.json').read_bytes();seal=json.loads((HERE/'public_predictions.seal.json').read_text())
    if hashlib.sha256(raw).hexdigest()!=seal['sha256']:raise RuntimeError('Prediction seal mismatch')
    for name,sha in seal['source_pins'].items():
        if hashlib.sha256((HERE/name).read_bytes()).hexdigest()!=sha:raise RuntimeError('Source changed')
    predictions=json.loads(raw);solution_raw=(DATA/'arc-agi_evaluation_solutions.json').read_bytes();reference_raw=REFERENCE.read_bytes()
    solutions=json.loads(solution_raw);reference=json.loads(reference_raw)
    if set(solutions)!=set(predictions['tasks']) or set(reference)!=set(solutions):raise RuntimeError('Task coverage mismatch')
    rows=[]
    for task_id,truths in solutions.items():
        p=predictions['tasks'][task_id]
        if len(p['attempts'])!=len(truths) or len(reference[task_id])!=len(truths):raise RuntimeError('Output coverage mismatch')
        base=[];own=[];merged=[];unique=[]
        for i,truth in enumerate(truths):
            initial=[reference[task_id][i]['attempt_1'],reference[task_id][i]['attempt_2']]
            final=[]
            for g in initial:
                if g and g not in final:final.append(g)
            for g in p['attempts'][i]:
                if len(final)<2 and g not in final:final.append(g)
            base.append(truth in initial);own.append(truth in p['attempts'][i]);merged.append(truth in final)
            unique.append(own[-1] and not base[-1])
        rows.append({'task':task_id,'outputs':len(truths),'reference':base,'local_rules':own,'fill_only':merged,
                     'oracle_union':[a or b for a,b in zip(base,own)],'new_correct':unique,
                     'fit_count':len(p['fits']),'chosen':p.get('chosen',[]),'unknown_cells':p.get('unknown_cells',[])})
    metrics={}
    for key in ('reference','local_rules','fill_only','oracle_union'):
        credit=sum(sum(row[key])/row['outputs'] for row in rows)
        metrics[key]={'exact_outputs':sum(sum(row[key]) for row in rows),'fully_solved_tasks':sum(all(row[key]) for row in rows),
                      'fractional_task_credit':credit,'mean_fractional_credit_percent':100*credit/len(rows)}
    result={'schema':'original-cellular-discovery-evaluation-v1','discovery_only':True,'official_score':None,
            'tasks':len(rows),'outputs':sum(row['outputs'] for row in rows),'metrics':metrics,
            'unique_incremental_outputs':sum(sum(row['new_correct']) for row in rows),
            'fill_only_incremental_outputs':metrics['fill_only']['exact_outputs']-metrics['reference']['exact_outputs'],
            'prediction_seconds':predictions['seconds'],'tasks_with_fit':sum(bool(row['fit_count']) for row in rows),
            'maximum_task_seconds':max(x.get('seconds',0) for x in predictions['tasks'].values()),
            'task_timeouts':sum(x.get('timed_out',False) for x in predictions['tasks'].values()),
            'prediction_sha256':seal['sha256'],'solution_sha256':hashlib.sha256(solution_raw).hexdigest(),
            'reference_sha256':hashlib.sha256(reference_raw).hexdigest(),'rows':rows,
            'limits':['Already-exposed public discovery set, not held out.','Unknown neighborhoods copy input; this is a fallible inductive bias.',
                      'Oracle union is an upper bound, not a deployable two-attempt selector.','No score or promotion claim.']}
    with (HERE/'public_evaluation.json').open('x') as f:json.dump(result,f,indent=2,sort_keys=True);f.write('\n')
    print(json.dumps({k:v for k,v in result.items() if k!='rows'},indent=2))


if __name__=='__main__':main()
