"""Invented motif generalization controls; no public task truth. MIT."""
import importlib.util,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('rules',HERE/'local_rules.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def example(height,width,r,c,shape,source,target):
    g=[[0]*width for _ in range(height)]
    for dr,dc in shape:g[r+dr][c+dc]=source
    g[height-1][width-1]=source  # distractor must remain unrecolored
    out=[row[:] for row in g]
    for dr,dc in shape:out[r+dr][c+dc]=target
    return g,out


def main():
    shapes={'cross':[(0,0),(-1,0),(1,0),(0,-1),(0,1)],'square':[(0,0),(0,1),(1,0),(1,1)],
            'line':[(0,0),(0,1),(0,2)],'L':[(0,0),(0,1),(1,0)]}
    checks=[]
    for name,shape in shapes.items():
        train=[]
        for h,w,r,c in ((7,8,2,2),(8,9,4,4),(10,11,6,3)):
            g,out=example(h,w,r,c,shape,2,8);train.append({'input':g,'output':out})
        held,truth=example(12,13,7,8,shape,2,8)
        pred=m.solve_task({'train':train,'test':[{'input':held}]})
        checks.append({'name':name+' translated/resized with distractor','pass':truth in pred['attempts'][0]})
    try:m.solve_task({'train':[],'test':[{'input':[[1]],'output':[[1]]}]})
    except ValueError:checks.append({'name':'forbidden truth rejected before abstention','pass':True})
    else:raise RuntimeError('Truth key accepted')
    try:m.grid([[0]*31])
    except ValueError:checks.append({'name':'31-wide grid rejected','pass':True})
    else:raise RuntimeError('Size cap not enforced')
    if not all(c['pass'] for c in checks):raise RuntimeError('Positive control failed')
    with (HERE/'POSITIVE_CONTROLS.json').open('x') as f:json.dump({'status':'PASS','checks':checks},f,indent=2);f.write('\n')
    print(json.dumps(checks,indent=2))


if __name__=='__main__':main()
