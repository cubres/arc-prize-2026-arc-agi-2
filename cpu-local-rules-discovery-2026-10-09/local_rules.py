"""Original demonstration-fitted local grid rules. MIT, 2026 cubres.

Finite, discovery-only supplement; no task identifiers or test answers accepted.
Output dimensions must already be preserved by every demonstration.
"""
from collections import Counter
import time


def grid(a):
    if not isinstance(a,list) or not 1 <= len(a) <= 30 or not a[0] or len(a[0]) > 30:
        raise ValueError("Grid size out of bounds")
    g=tuple(tuple(row) for row in a)
    if any(len(row)!=len(g[0]) for row in g) or any(type(c) is not int or not 0 <= c <= 9 for row in g for c in row):
        raise ValueError("Malformed ARC grid")
    return g


def mode(g):
    counts=Counter(c for row in g for c in row)
    return min(counts,key=lambda c:(-counts[c],c))


def signature(g,r,c,offsets,bg):
    # Relative color IDs encode equality, not arbitrary absolute palette IDs.
    roles={bg:0}
    if g[r][c]!=bg:roles[g[r][c]]=1
    encoded=[];values=[]
    for dr,dc in offsets:
        rr,cc=r+dr,c+dc
        if not 0 <= rr < len(g) or not 0 <= cc < len(g[0]):
            encoded.append(-1);values.append(None);continue
        value=g[rr][cc]
        if value not in roles:roles[value]=len(roles)
        encoded.append(roles[value]);values.append(value)
    return tuple(encoded),values


def action_candidates(current,wanted,bg,values):
    out=set()
    if current==wanted:out.add((0,0))
    if bg==wanted:out.add((1,0))
    for index,value in enumerate(values):
        if value==wanted:out.add((2,index))
    out.add((3,wanted))
    return out


def action_value(action,current,bg,values):
    kind,value=action
    if kind==0:return current
    if kind==1:return bg
    if kind==2:return values[value]
    if kind==3:return value
    raise ValueError("Unknown local action")


def neighborhood(kind):
    if kind=="cross1":return ((0,0),(-1,0),(0,-1),(0,1),(1,0))
    radius=1 if kind=="square1" else 2
    return tuple((dr,dc) for dr in range(-radius,radius+1) for dc in range(-radius,radius+1))


def fit_local(inputs,targets,kind,bg_name,deadline):
    offsets=neighborhood(kind);rules={}
    for g,target in zip(inputs,targets):
        bg=mode(g) if bg_name=="mode" else 0
        for r,row in enumerate(g):
            if time.monotonic()>=deadline:return None
            for c,current in enumerate(row):
                key,values=signature(g,r,c,offsets,bg)
                candidates=action_candidates(current,target[r][c],bg,values)
                if key in rules:candidates=rules[key] & candidates
                if not candidates:return None
                rules[key]=candidates
    return {key:min(candidates) for key,candidates in rules.items()}


def apply_local(g,kind,bg_name,rules):
    offsets=neighborhood(kind);bg=mode(g) if bg_name=="mode" else 0
    out=[];unknown=0
    for r,row in enumerate(g):
        outrow=[]
        for c,current in enumerate(row):
            key,values=signature(g,r,c,offsets,bg)
            if key not in rules:unknown+=1;outrow.append(current)
            else:outrow.append(action_value(rules[key],current,bg,values))
        out.append(tuple(outrow))
    return tuple(out),unknown


def motifs():
    seeds=[((0,0),(-1,0),(0,-1),(0,1),(1,0)),
           ((0,0),(-1,-1),(-1,1),(1,-1),(1,1)),
           ((0,0),(0,1),(1,0),(1,1)),
           ((0,0),(0,1),(0,2)),
           ((0,0),(0,1),(1,0)),
           ((0,0),(0,1),(0,-1),(1,0)),
           tuple((r,c) for r in (-1,0,1) for c in (-1,0,1)),
           tuple((r,c) for r in (-1,0,1) for c in (-1,0,1) if r or c)]
    all_shapes=set()
    for seed in seeds:
        for turn in range(4):
            shape=[]
            for r,c in seed:
                for _ in range(turn):r,c=c,-r
                shape.append((r,c))
            minr,minc=min(r for r,c in shape),min(c for r,c in shape)
            all_shapes.add(tuple(sorted((r-minr,c-minc) for r,c in shape)))
    return sorted(all_shapes,key=lambda s:(len(s),s))


def stamp(g,shape,source,target):
    out=[list(row) for row in g]
    for r in range(len(g)):
        for c in range(len(g[0])):
            cells=[(r+dr,c+dc) for dr,dc in shape]
            if all(0 <= rr < len(g) and 0 <= cc < len(g[0]) and g[rr][cc]==source for rr,cc in cells):
                for rr,cc in cells:out[rr][cc]=target
    return tuple(tuple(row) for row in out)


def solve_task(task):
    start=time.monotonic();deadline=start+2
    if set(task)!={"train","test"} or any(set(p)!={"input","output"} for p in task["train"]) or any(set(p)!={"input"} for p in task["test"]):
        raise ValueError("Demonstrations and test inputs only; no test output or ID")
    inputs=[grid(p["input"]) for p in task["train"]]
    targets=[grid(p["output"]) for p in task["train"]]
    tests=[grid(p["input"]) for p in task["test"]]
    empty={"attempts":[[] for _ in tests],"fits":[],"unknown_cells":[],"reason":"shape mismatch or too few demonstrations"}
    if len(inputs)<2 or any((len(g),len(g[0]))!=(len(t),len(t[0])) for g,t in zip(inputs,targets)):
        return empty
    fits=[]
    changes={(a,b) for g,t in zip(inputs,targets) for ar,br in zip(g,t) for a,b in zip(ar,br) if a!=b}
    if len(changes)==1:
        source,target=next(iter(changes))
        for shape in motifs():
            if time.monotonic()>=deadline:break
            if all(stamp(g,shape,source,target)==t for g,t in zip(inputs,targets)):
                fits.append(((0,len(shape),repr(shape)),f"stamp {source}->{target} {shape}",
                             [stamp(g,shape,source,target) for g in tests],[0]*len(tests)))
    for kind in ("cross1","square1","square2"):
        for bg_name in ("mode","zero"):
            if time.monotonic()>=deadline:break
            rules=fit_local(inputs,targets,kind,bg_name,deadline)
            if rules is None:continue
            if not all(apply_local(g,kind,bg_name,rules)[0]==t for g,t in zip(inputs,targets)):
                raise RuntimeError("Local rule demonstration mismatch")
            pairs=[apply_local(g,kind,bg_name,rules) for g in tests]
            changed=sum(action[0]!=0 for action in rules.values())
            fits.append(((1,len(neighborhood(kind)),changed,kind,bg_name),
                         f"local {kind} {bg_name} rules={len(rules)} changed={changed}",
                         [pair[0] for pair in pairs],[pair[1] for pair in pairs]))
    fits.sort(key=lambda x:x[0]);attempts=[];unknown=[];names=[]
    for i in range(len(tests)):
        grids=[];counts=[];programs=[]
        for score,name,predicted,unknowns in fits:
            if predicted[i] not in grids:
                grids.append(predicted[i]);counts.append(unknowns[i]);programs.append(name)
            if len(grids)==2:break
        attempts.append([[list(row) for row in g] for g in grids]);unknown.append(counts);names.append(programs)
    return {"attempts":attempts,"fits":[x[1] for x in fits],"chosen":names,"unknown_cells":unknown,
            "seconds":time.monotonic()-start,"timed_out":time.monotonic()>=deadline}
