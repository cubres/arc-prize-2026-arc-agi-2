"""Invented behavioral controls only; never imports public grids or truths."""
import numpy as np
import object_selector as s


def main():
    a=np.array([[0,2,2,0,3],[0,2,2,0,0],[0,0,0,0,0]],dtype=np.uint8)
    p=s.objects(a,0,False,False)
    assert len(p)==2
    largest=s.select(p,("area",-1))
    assert s.render(a,largest,0,"crop").tolist()==[[2,2],[2,2]]
    assert s.render(a,largest,0,"retain").tolist()==[[0,2,2,0,0],[0,2,2,0,0],[0,0,0,0,0]]
    assert s.render(a,largest,0,"erase").tolist()==[[0,0,0,0,3],[0,0,0,0,0],[0,0,0,0,0]]
    diag=np.array([[2,0],[0,2]],dtype=np.uint8)
    assert len(s.objects(diag,0,False,False))==2
    assert len(s.objects(diag,0,True,False))==1
    touching=np.array([[2,3]],dtype=np.uint8)
    assert len(s.objects(touching,0,False,False))==1
    assert len(s.objects(touching,0,False,True))==2
    try:
        s.select(s.objects(diag,0,False,False),("area",-1))
    except ValueError:
        pass
    else:
        raise AssertionError("ties must abstain")
    base=[{"grids":[[[1]]]}, {"grids":[[[2]]]}]
    extra=[{"grids":[[[3]]]}]
    assert s.fill_only(base,extra)==base
    assert s.fill_only(base[:1],extra)==base[:1]+extra
    assert s.fill_only([base[0],base[0]],extra)==base[:1]+extra
    # Two different input sizes and colors; novel identity color is supported.
    b=[[0,4,4,4,0,5],[0,4,4,4,0,0],[0,0,0,0,0,0]]
    q=[[0,7,7,0,8],[0,7,7,0,0],[0,0,0,0,0]]
    task={"train":[{"input":a.tolist(),"output":[[2,2],[2,2]]},
                   {"input":b,"output":[[4,4,4],[4,4,4]]}],"test":[{"input":q}]}
    result=s.solve(task,seconds=1)
    assert any(c["grids"]==[[[7,7],[7,7]]] for c in result["candidates"])
    rejected=dict(task); rejected["test"]=[{"input":q,"output":[[9]]}]
    try:
        s.solve(rejected)
    except ValueError:
        pass
    else:
        raise AssertionError("query truth must be refused")
    print("PASS 14 invented object/connectivity/tie/fill/schema controls")


if __name__=="__main__":
    main()
